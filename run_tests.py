#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试执行入口脚本
支持命令行参数控制测试执行方式
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime

from common.log import Logger

logger = Logger().get_logger()


def parse_arguments():
    """
    解析命令行参数
    
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
    
    # 执行控制
    execution = parser.add_argument_group("执行控制")
    execution.add_argument("-p", "--parallel", action="store_true", help="启用并行执行")
    execution.add_argument("-w", "--workers", type=int, default=4, help="并行执行的最大工作线程数")
    execution.add_argument("-r", "--retries", type=int, default=0, help="失败重试次数")
    execution.add_argument("-v", "--verbose", action="store_true", help="显示详细日志")
    execution.add_argument("--failfast", action="store_true", help="首次失败时停止")
    
    # 报告相关
    reporting = parser.add_argument_group("报告配置")
    reporting.add_argument("--report", action="store_true", help="生成Allure报告")
    reporting.add_argument("--report-dir", dest="report_dir", help="指定报告输出目录")
    reporting.add_argument("--clean", action="store_true", help="清理旧的测试结果")
    reporting.add_argument("--open-report", action="store_true", dest="open_report", 
                          help="测试完成后自动打开报告")
    
    # 环境相关
    environment = parser.add_argument_group("环境配置")
    environment.add_argument("--env", choices=["dev", "test", "staging", "prod"], default="test", 
                            help="指定测试环境")
    environment.add_argument("--config", help="指定配置文件路径")
    environment.add_argument("--debug", action="store_true", help="启用调试模式")
    
    return parser.parse_args()


def build_pytest_command(args):
    """
    根据命令行参数构建pytest命令
    
    Args:
        args (argparse.Namespace): 命令行参数
        
    Returns:
        tuple: (命令列表, 环境变量字典)
    """
    cmd = ["pytest"]
    env = os.environ.copy()  # 复制当前环境变量
    
    # 测试用例选择参数
    test_filters = []
    if args.module:
        test_filters.append(args.module)
    if args.keyword:
        test_filters.append(args.keyword)
    if args.case_id:
        test_filters.append(f"test_case_id='{args.case_id}'")
    
    # 合并所有过滤条件
    if test_filters:
        cmd.append(f"-k '{' and '.join(test_filters)}'")
    
    # 标签过滤
    if args.tag:
        cmd.append(f"-m {args.tag}")
    
    # 执行控制
    if args.verbose:
        cmd.append("-v")
    if args.failfast:
        cmd.append("--exitfirst")
    if args.retries > 0:
        cmd.append(f"--reruns {args.retries}")
    
    # 设置环境变量
    env["TEST_ENV"] = args.env
    if args.file:
        # 确保文件路径是绝对路径
        excel_path = os.path.abspath(args.file)
        if not os.path.exists(excel_path):
            logger.warning(f"指定的Excel文件不存在: {excel_path}")
        env["TEST_EXCEL_FILE"] = excel_path
    
    if args.parallel:
        env["PARALLEL_EXECUTION"] = "true"
        env["MAX_WORKERS"] = str(args.workers)
    
    if args.config:
        config_path = os.path.abspath(args.config)
        if not os.path.exists(config_path):
            logger.warning(f"指定的配置文件不存在: {config_path}")
        env["CONFIG_FILE"] = config_path
    
    # 调试模式
    if args.debug:
        env["DEBUG"] = "true"
        cmd.append("-v")
        cmd.append("--no-header")
        cmd.append("--show-capture=all")
    
    # Allure报告相关
    allure_results_dir = args.report_dir or "./reports/allure-results"
    allure_results_dir = os.path.abspath(allure_results_dir)
    
    # 确保报告目录存在
    os.makedirs(allure_results_dir, exist_ok=True)
    
    if args.clean:
        cmd.append("--clean-alluredir")
    
    cmd.append(f"--alluredir={allure_results_dir}")
    
    return cmd, env


def run_tests(args):
    """
    执行测试
    
    Args:
        args (argparse.Namespace): 命令行参数
        
    Returns:
        int: 退出码，0表示成功，非0表示失败
    """
    start_time = time.time()
    banner = f"{'='*80}"
    logger.info(f"\n{banner}")
    logger.info(f"开始执行API自动化测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"环境: {args.env.upper()}")
    logger.info(f"{banner}\n")
    
    try:
        # 构建pytest命令和环境变量
        cmd, env = build_pytest_command(args)
        cmd_str = ' '.join(cmd)
        logger.info(f"执行命令: {cmd_str}")
        
        # 记录环境变量
        if args.debug:
            env_vars = {k: v for k, v in env.items() if k.startswith('TEST_') or k in ['PARALLEL_EXECUTION', 'MAX_WORKERS', 'CONFIG_FILE', 'DEBUG']}
            logger.debug(f"环境变量: {env_vars}")
        
        # 执行测试
        result = subprocess.run(
            cmd, 
            env=env,
            stdout=subprocess.PIPE if not args.verbose else None,
            stderr=subprocess.PIPE if not args.verbose else None,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        # 如果不是详细模式，但需要显示输出
        if not args.verbose:
            if result.returncode != 0:
                logger.error("测试执行失败，输出详情:")
                if result.stdout:
                    logger.info(result.stdout)
                if result.stderr:
                    logger.error(result.stderr)
            elif args.debug:
                logger.debug("测试输出:")
                if result.stdout:
                    logger.debug(result.stdout)
        
        # 生成Allure报告
        if args.report and result.returncode in [0, 1]:  # 0=成功, 1=测试失败但执行完成
            generate_allure_report(args)
        
        # 输出结果摘要
        elapsed = time.time() - start_time
        logger.info(f"\n{banner}")
        
        if result.returncode == 0:
            logger.info(f"测试执行成功 - 耗时: {elapsed:.2f}秒")
        elif result.returncode == 1:
            logger.warning(f"测试执行完成，但有失败的测试 - 耗时: {elapsed:.2f}秒")
        else:
            logger.error(f"测试执行出错 (退出码: {result.returncode}) - 耗时: {elapsed:.2f}秒")
            
        logger.info(f"{banner}\n")
        
        return result.returncode
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"执行测试过程中发生错误: {e}")
        logger.error(f"\n{banner}")
        logger.error(f"测试执行失败 - 耗时: {elapsed:.2f}秒")
        logger.error(f"{banner}\n")
        return 2  # 通用错误退出码


def generate_allure_report(args):
    """
    生成Allure HTML报告
    """
    print("\n生成Allure HTML报告...")
    
    allure_results_dir = args.report_dir or "./reports/allure-results"
    allure_report_dir = "./reports/allure-report"
    
    # 确保目录存在
    os.makedirs(allure_results_dir, exist_ok=True)
    
    # 生成报告
    cmd = f"allure generate {allure_results_dir} -o {allure_report_dir} --clean"
    subprocess.run(cmd, shell=True)
    
    print(f"报告已生成: {os.path.abspath(allure_report_dir)}")
    
    # 尝试打开报告
    try:
        if os.name == 'nt':  # Windows
            os.system(f"start {os.path.abspath(allure_report_dir)}")
        elif os.name == 'posix':  # Linux/Mac
            os.system(f"open {os.path.abspath(allure_report_dir)}")
    except:
        pass


def main():
    """
    主函数
    """
    args = parse_arguments()
    
    try:
        exit_code = run_tests(args)
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n测试执行被用户中断")
        sys.exit(130)  # 130是SIGINT的标准退出码
    except Exception as e:
        print(f"\n执行过程中发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()