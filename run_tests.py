#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试执行入口脚本
支持命令行参数控制测试执行方式
"""

import argparse
import configparser
import os
import subprocess
import sys
import time
from datetime import datetime


def parse_arguments():
    """
    解析命令行参数
    """
    parser = argparse.ArgumentParser(description="API自动化测试执行工具")
    
    # 测试用例选择
    parser.add_argument("-f", "--file", help="指定测试用例Excel文件路径")
    parser.add_argument("-m", "--module", help="指定要执行的模块名称")
    parser.add_argument("-k", "--keyword", help="根据关键字筛选测试用例")
    parser.add_argument("-i", "--case-id", dest="case_id", help="指定测试用例ID")
    parser.add_argument("-t", "--tag", help="根据标签筛选测试用例")
    
    # 执行控制
    parser.add_argument("-p", "--parallel", action="store_true", help="启用并行执行")
    parser.add_argument("-w", "--workers", type=int, default=4, help="并行执行的最大工作线程数")
    parser.add_argument("-r", "--retries", type=int, default=0, help="失败重试次数")
    parser.add_argument("-v", "--verbose", action="store_true", help="显示详细日志")
    parser.add_argument("--failfast", action="store_true", help="首次失败时停止")
    
    # 报告相关
    parser.add_argument("--report", action="store_true", help="生成Allure报告")
    parser.add_argument("--report-dir", dest="report_dir", help="指定报告输出目录")
    parser.add_argument("--clean", action="store_true", help="清理旧的测试结果")
    
    # 环境相关
    parser.add_argument("--env", choices=["dev", "test", "staging", "prod"], default="test", 
                        help="指定测试环境")
    parser.add_argument("--config", help="指定配置文件路径")
    
    return parser.parse_args()


def build_pytest_command(args):
    """
    根据命令行参数构建pytest命令
    """
    cmd = ["pytest"]
    
    # 测试用例选择
    if args.module:
        cmd.append(f"-k {args.module}")
    if args.keyword:
        cmd.append(f"-k {args.keyword}")
    if args.case_id:
        cmd.append(f"-k {args.case_id}")
    if args.tag:
        cmd.append(f"-m {args.tag}")
    
    # 执行控制
    if args.verbose:
        cmd.append("-v")
    if args.failfast:
        cmd.append("--exitfirst")
    
    # 环境变量设置
    env_vars = [f"TEST_ENV={args.env}"]
    if args.file:
        env_vars.append(f"TEST_EXCEL_FILE={args.file}")
    if args.parallel:
        env_vars.append("PARALLEL_EXECUTION=true")
    if args.workers:
        env_vars.append(f"MAX_WORKERS={args.workers}")
    if args.config:
        env_vars.append(f"CONFIG_FILE={args.config}")
    
    # 添加环境变量前缀
    if env_vars:
        if os.name == 'nt':  # Windows
            env_prefix = "set " + " && set ".join(env_vars) + " && "
        else:  # Unix/Linux/Mac
            env_prefix = " ".join(env_vars) + " "
        cmd = [env_prefix + cmd[0]] + cmd[1:]
    
    # Allure报告相关
    if args.clean:
        cmd.append("--clean-alluredir")
    
    allure_results_dir = args.report_dir or "./reports/allure-results"
    cmd.append(f"--alluredir={allure_results_dir}")
    
    return " ".join(cmd)


def run_tests(args):
    """
    执行测试
    """
    start_time = time.time()
    print(f"\n{'='*80}")
    print(f"开始执行API自动化测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # 构建并执行pytest命令
    cmd = build_pytest_command(args)
    print(f"执行命令: {cmd}\n")
    
    result = subprocess.run(cmd, shell=True)
    
    # 生成Allure报告
    if args.report and result.returncode in [0, 1]:  # 0=成功, 1=测试失败但执行完成
        generate_allure_report(args)
    
    elapsed = time.time() - start_time
    print(f"\n{'='*80}")
    print(f"测试执行完成 - 耗时: {elapsed:.2f}秒")
    print(f"{'='*80}\n")
    
    return result.returncode


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