#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试执行入口脚本
支持命令行参数控制测试执行方式

重构版本：
- 使用类结构组织代码
- 增强错误处理和日志记录
- 优化配置管理
- 扩展命令行参数
- 改进报告生成逻辑
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Tuple, Optional

from common.log import Logger
from core import ConfigManager


class TestRunner:
    """测试执行器类，负责处理测试执行的全流程"""

    def __init__(self):
        """初始化测试执行器"""
        self.logger = Logger().get_logger()
        self.args = None
        self.start_time = None
        self.banner = "=" * 80
        # 初始化配置管理器
        self.config_manager = ConfigManager()
        self.configs = self.config_manager.get_all_configs()

    def run(self) -> int:
        """运行测试主流程
        
        Returns:
            int: 退出码，0表示成功，非0表示失败
        """
        try:
            # 解析命令行参数
            self.args = self._parse_arguments()

            # 执行测试
            return self._execute_tests()

        except KeyboardInterrupt:
            self.logger.warning("\n测试执行被用户中断")
            return 130  # 130是SIGINT的标准退出码
        except Exception as e:
            self.logger.error(f"\n执行过程中发生错误: {e}", exc_info=True)
            return 1

    def _parse_arguments(self) -> argparse.Namespace:
        """解析命令行参数
        
        Returns:
            argparse.Namespace: 解析后的命令行参数
        """
        parser = argparse.ArgumentParser(description="API自动化测试执行工具")

        # 测试用例选择
        test_selection = parser.add_argument_group("测试用例选择")
        test_selection.add_argument("-f", "--file", help="指定测试用例Excel文件路径")
        test_selection.add_argument("-m", "--module", help="指定要执行的模块名称")
        test_selection.add_argument("-k", "--keyword", help="根据关键字筛选测试用例")
        test_selection.add_argument("-i", "--case-id", dest="case_id", help="指定测试用例ID")
        test_selection.add_argument("-t", "--tag", help="根据标签筛选测试用例")
        test_selection.add_argument("--priority", choices=["P0", "P1", "P2", "P3"],
                                    help="按优先级筛选测试用例")

        # 执行控制
        execution = parser.add_argument_group("执行控制")
        execution.add_argument("-p", "--parallel", action="store_true", help="启用并行执行")
        execution.add_argument("-w", "--workers", type=int, default=4, help="并行执行的最大工作线程数")
        execution.add_argument("-r", "--retries", type=int, default=0, help="失败重试次数")
        execution.add_argument("-v", "--verbose", action="store_true", help="显示详细日志")
        execution.add_argument("--failfast", action="store_true", help="首次失败时停止")
        execution.add_argument("--timeout", type=int, default=30, help="请求超时时间(秒)")
        execution.add_argument("--max-failures", type=int, dest="max_failures",
                               help="最大失败次数，超过后停止测试")

        # 报告相关
        reporting = parser.add_argument_group("报告配置")
        reporting.add_argument("--report", action="store_true", help="生成Allure报告")
        reporting.add_argument("--report-dir", dest="report_dir", help="指定报告输出目录")
        reporting.add_argument("--clean", action="store_true", help="清理旧的测试结果")
        reporting.add_argument("--open-report", action="store_true", dest="open_report",
                               help="测试完成后自动打开报告")
        # reporting.add_argument("--html-report", action="store_true", dest="html_report",
        #                        help="生成HTML格式的报告")
        # reporting.add_argument("--junit-report", action="store_true", dest="junit_report",
        #                        help="生成JUnit格式的报告")

        # 环境相关
        environment = parser.add_argument_group("环境配置")
        environment.add_argument("--env", choices=["dev", "test", "staging", "prod"], default="test",
                                 help="指定测试环境")
        environment.add_argument("--config", help="指定配置文件路径")
        environment.add_argument("--debug", action="store_true", help="启用调试模式")
        environment.add_argument("--var", action="append", dest="variables",
                                 help="设置自定义变量，格式: 名称=值")

        # 其他选项
        other = parser.add_argument_group("其他选项")
        other.add_argument("--version", action="version", version="API自动化测试框架 v1.0.0")
        other.add_argument("--list-cases", action="store_true", dest="list_cases",
                           help="列出符合条件的测试用例但不执行")
        other.add_argument("--export-cases", dest="export_cases",
                           help="导出符合条件的测试用例到指定文件")

        return parser.parse_args()

    def _execute_tests(self) -> int:
        """执行测试
        
        Returns:
            int: 退出码，0表示成功，非0表示失败
        """
        self.start_time = time.time()
        self._print_banner("开始执行API自动化测试")

        try:
            # 检查是否只列出测试用例
            if self.args.list_cases:
                return self._list_test_cases()

            # 检查是否导出测试用例
            if self.args.export_cases:
                return self._export_test_cases()

            # 构建pytest命令和环境变量
            cmd, env = self._build_pytest_command()
            cmd_str = ' '.join(cmd)
            self.logger.info(f"执行命令: {cmd_str}")

            # 记录环境变量
            if self.args.debug:
                env_vars = {k: v for k, v in env.items()
                            if k.startswith('TEST_') or
                            k in ['PARALLEL_EXECUTION', 'MAX_WORKERS', 'CONFIG_FILE', 'DEBUG']}
                self.logger.debug(f"环境变量: {env_vars}")

            # 执行测试
            result = self._run_pytest_command(cmd, env)

            # 生成报告
            if self.args.report and result.returncode in [0, 1]:  # 0=成功, 1=测试失败但执行完成
                self._generate_reports()

            # 输出结果摘要
            self._print_summary(result.returncode)

            return result.returncode

        except Exception as e:
            self._handle_execution_error(e)
            return 2  # 通用错误退出码

    def _build_pytest_command(self) -> Tuple[List[str], Dict[str, str]]:
        """根据命令行参数构建pytest命令
        
        Returns:
            tuple: (命令列表, 环境变量字典)
        """
        cmd = ["pytest"]
        env = os.environ.copy()  # 复制当前环境变量

        # 测试用例选择参数
        test_filters = []
        if self.args.module:
            test_filters.append(self.args.module)
        if self.args.keyword:
            test_filters.append(self.args.keyword)
        if self.args.case_id:
            test_filters.append(f"test_case_id='{self.args.case_id}'")
        if self.args.priority:
            test_filters.append(f"priority='{self.args.priority}'")

        # 合并所有过滤条件
        if test_filters:
            cmd.append(f"-k '{' and '.join(test_filters)}'")

        # 标签过滤
        if self.args.tag:
            cmd.append(f"-m {self.args.tag}")

        # 执行控制
        if self.args.verbose:
            cmd.append("-v")
        if self.args.failfast:
            cmd.append("--exitfirst")
        if self.args.retries > 0:
            cmd.append(f"--reruns {self.args.retries}")
        if self.args.max_failures:
            cmd.append(f"--maxfail={self.args.max_failures}")

        # 设置环境变量
        env["TEST_ENV"] = self.args.env
        env["TEST_TIMEOUT"] = str(self.args.timeout)

        # 处理Excel文件路径
        if self.args.file:
            excel_path = self._validate_file_path(self.args.file)
            if excel_path:
                env["TEST_EXCEL_FILE"] = excel_path

        # 并行执行设置
        if self.args.parallel:
            env["PARALLEL_EXECUTION"] = "true"
            env["MAX_WORKERS"] = str(self.args.workers)

        # 配置文件设置
        if self.args.config:
            config_path = self._validate_file_path(self.args.config)
            if config_path:
                env["CONFIG_FILE"] = config_path

        # 自定义变量
        if self.args.variables:
            for var in self.args.variables:
                if "=" in var:
                    name, value = var.split("=", 1)
                    env[f"TEST_VAR_{name.upper()}"] = value

        # 调试模式
        if self.args.debug:
            env["DEBUG"] = "true"
            cmd.append("-v")
            cmd.append("--no-header")
            cmd.append("--show-capture=all")

        # 报告相关设置
        self._setup_report_options(cmd, env)

        return cmd, env

    def _validate_file_path(self, file_path: str) -> Optional[str]:
        """验证文件路径是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 绝对路径，如果文件不存在则返回None
        """
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            self.logger.warning(f"指定的文件不存在: {abs_path}")
            return None
        return abs_path

    def _setup_report_options(self, cmd: List[str], env: Dict[str, str]) -> None:
        """设置报告相关选项
        
        Args:
            cmd: 命令列表
            env: 环境变量字典
        """
        # Allure报告相关
        allure_results_dir = self.args.report_dir or self.configs.get("report").allure_results_dir
        allure_results_dir = os.path.abspath(allure_results_dir)

        # 确保报告目录存在
        os.makedirs(allure_results_dir, exist_ok=True)

        if self.args.clean:
            cmd.append("--clean-alluredir")

        cmd.append(f"--alluredir={allure_results_dir}")

        # HTML报告
        if self.configs.get("report").html_report_dir:
            html_report_dir = self.configs.get("report").html_report_dir
            os.makedirs(html_report_dir, exist_ok=True)
            cmd.append(f"--html={html_report_dir}/report.html")
            cmd.append("--self-contained-html")

        # JUnit报告
        if self.configs.get("report").junit_report_dir:
            junit_report_dir = self.configs.get("report").junit_report_dir
            os.makedirs(junit_report_dir, exist_ok=True)
            cmd.append(f"--junitxml={junit_report_dir}/junit-report.xml")

    def _run_pytest_command(self, cmd: List[str], env: Dict[str, str]) -> subprocess.CompletedProcess:
        """运行pytest命令
        
        Args:
            cmd: 命令列表
            env: 环境变量字典
            
        Returns:
            subprocess.CompletedProcess: 命令执行结果
        """
        result = subprocess.run(
            cmd,
            env=env,
            stdout=subprocess.PIPE if not self.args.verbose else None,
            stderr=subprocess.PIPE if not self.args.verbose else None,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        # 如果不是详细模式，但需要显示输出
        if not self.args.verbose:
            if result.returncode != 0:
                self.logger.error("测试执行失败，输出详情:")
                if result.stdout:
                    self.logger.info(result.stdout)
                if result.stderr:
                    self.logger.error(result.stderr)
            elif self.args.debug:
                self.logger.debug("测试输出:")
                if result.stdout:
                    self.logger.debug(result.stdout)

        return result

    def _generate_reports(self) -> None:
        """生成测试报告"""
        self.logger.info("\n生成测试报告...")

        # 生成Allure报告
        allure_results_dir = self.args.report_dir or self.configs.get("report").allure_results_dir
        allure_results_dir = os.path.abspath(allure_results_dir)
        allure_report_dir = self.configs.get("report").allure_report_dir

        # 确保目录存在
        os.makedirs(allure_results_dir, exist_ok=True)

        # 生成报告
        try:
            cmd = f"allure generate {allure_results_dir} -o {allure_report_dir} --clean"
            subprocess.run(cmd, shell=True, check=True)

            self.logger.info(f"报告已生成: {os.path.abspath(allure_report_dir)}")

            # 尝试打开报告
            if self.args.open_report:
                self._open_report(allure_report_dir)

        except subprocess.CalledProcessError as e:
            self.logger.error(f"生成Allure报告失败: {e}")
        except Exception as e:
            self.logger.error(f"生成报告过程中发生错误: {e}", exc_info=True)

    def _open_report(self, report_dir: str) -> None:
        """打开测试报告
        
        Args:
            report_dir: 报告目录
        """
        report_path = os.path.abspath(report_dir)
        try:
            self.logger.info(f"尝试打开报告: {report_path}")

            if os.name == 'nt':  # Windows
                os.system(f"start {report_path}")
            elif sys.platform == 'darwin':  # macOS
                os.system(f"open {report_path}")
            else:  # Linux或其他
                os.system(f"xdg-open {report_path} || sensible-browser {report_path} || x-www-browser {report_path}")
        except Exception as e:
            self.logger.warning(f"无法自动打开报告: {e}")
            self.logger.info(f"请手动打开报告: {report_path}")

    def _list_test_cases(self) -> int:
        """列出符合条件的测试用例
        
        Returns:
            int: 退出码
        """
        self.logger.info("列出符合条件的测试用例:")

        # 构建命令，添加--collect-only参数
        cmd, env = self._build_pytest_command()
        cmd.append("--collect-only")
        cmd.append("-v")

        # 执行命令
        result = subprocess.run(
            cmd,
            env=env,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        return result.returncode

    def _export_test_cases(self) -> int:
        """导出符合条件的测试用例
        
        Returns:
            int: 退出码
        """
        self.logger.info(f"导出符合条件的测试用例到: {self.args.export_cases}")

        # 构建命令，添加--collect-only参数
        cmd, env = self._build_pytest_command()
        cmd.append("--collect-only")
        cmd.append("-v")

        # 执行命令并捕获输出
        result = subprocess.run(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        # 将输出写入文件
        if result.returncode == 0:
            try:
                with open(self.args.export_cases, 'w', encoding='utf-8') as f:
                    f.write(result.stdout)
                self.logger.info(f"测试用例已导出到: {os.path.abspath(self.args.export_cases)}")
            except Exception as e:
                self.logger.error(f"导出测试用例失败: {e}")
                return 1
        else:
            self.logger.error("收集测试用例失败")
            if result.stderr:
                self.logger.error(result.stderr)
            return result.returncode

        return 0

    def _print_banner(self, message: str) -> None:
        """打印横幅信息
        
        Args:
            message: 要显示的消息
        """
        self.logger.info(f"\n{self.banner}")
        self.logger.info(f"{message} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"环境: {self.args.env.upper()}")
        self.logger.info(f"{self.banner}\n")

    def _print_summary(self, return_code: int) -> None:
        """打印测试执行摘要
        
        Args:
            return_code: 命令返回码
        """
        elapsed = time.time() - self.start_time
        self.logger.info(f"\n{self.banner}")

        if return_code == 0:
            self.logger.info(f"测试执行成功 - 耗时: {elapsed:.2f}秒")
        elif return_code == 1:
            self.logger.warning(f"测试执行完成，但有失败的测试 - 耗时: {elapsed:.2f}秒")
        else:
            self.logger.error(f"测试执行出错 (退出码: {return_code}) - 耗时: {elapsed:.2f}秒")

        self.logger.info(f"{self.banner}\n")

    def _handle_execution_error(self, error: Exception) -> None:
        """处理执行过程中的错误
        
        Args:
            error: 异常对象
        """
        elapsed = time.time() - self.start_time
        self.logger.error(f"执行测试过程中发生错误: {error}", exc_info=True)
        self.logger.error(f"\n{self.banner}")
        self.logger.error(f"测试执行失败 - 耗时: {elapsed:.2f}秒")
        self.logger.error(f"{self.banner}\n")


def main():
    """主函数"""
    runner = TestRunner()
    exit_code = runner.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
