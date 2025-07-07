import os
import sys
import subprocess
from datetime import datetime
import locale


def run_tests():
    """运行测试的主函数"""
    print("🚀 开始运行API自动化测试...")

    # 创建allure结果目录
    allure_results_dir = "reports/allure-results"
    allure_report_dir = "reports/allure-report"

    if not os.path.exists(allure_results_dir):
        os.makedirs(allure_results_dir)

    if not os.path.exists(allure_report_dir):
        os.makedirs(allure_report_dir)

    # 创建reports目录（备用HTML报告）
    if not os.path.exists("reports"):
        os.makedirs("reports")

    # 构建pytest命令
    cmd = [
        "pytest",
        "test/",
        "-v",  # 详细输出
        "--alluredir=" + allure_results_dir,  # Allure结果目录
        "--self-contained-html",  # 自包含HTML报告
        "--tb=short",  # 简短的traceback
        "--clean-alluredir",  # 清理之前的allure结果
    ]

    try:
        # 设置环境变量解决编码问题
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'

        # 运行测试，生成allure结果
        print("📋 正在执行测试用例...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            env=env
        )

        # 输出测试结果
        print("测试输出:")
        if result.stdout:
            print(result.stdout)

        if result.stderr:
            print("错误信息:")
            print(result.stderr)

        # 生成Allure报告
        print("📊 正在生成Allure报告...")
        generate_allure_report(allure_results_dir, allure_report_dir)

        # 检查测试结果
        if result.returncode == 0:
            print(f"✅ 所有测试通过！")
        else:
            print(f"❌ 测试失败，返回码: {result.returncode}")

        print(f"📊 Allure报告已生成: {allure_report_dir}/index.html")

        # 尝试打开Allure报告
        # try_open_allure_report(allure_report_dir)

    except Exception as e:
        print(f"❌ 运行测试时发生错误: {str(e)}")
        # 提供备用运行方式
        print("尝试使用备用运行方式...")
        run_tests_alternative(allure_results_dir, allure_report_dir)


def generate_allure_report(results_dir, report_dir):
    """生成Allure报告"""
    try:
        # 检查allure命令是否可用
        subprocess.run(["E:\\develop\\allure\\bin\\allure.bat", "--version"], capture_output=True, check=True)

        # 生成报告
        cmd = ["E:\\develop\\allure\\bin\\allure.bat", "generate", results_dir, "-o", report_dir, "--clean"]
        subprocess.run(cmd, capture_output=True, check=True)

        print("✅ Allure报告生成成功！")
        return True

    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Allure命令未找到，请安装Allure命令行工具")
        print("安装说明: https://docs.qameta.io/allure/#_installing_a_commandline")
        return False


def try_open_allure_report(report_dir):
    """尝试打开Allure报告"""
    try:
        import webbrowser
        report_path = os.path.join(report_dir, "index.html")
        if os.path.exists(report_path):
            webbrowser.open(f"file://{os.path.abspath(report_path)}")
            print("🌐 已尝试在浏览器中打开Allure报告")
        else:
            print("⚠️  Allure报告文件不存在，可能生成失败")
    except Exception as e:
        print(f"⚠️  无法自动打开报告: {str(e)}")


def run_tests_alternative(allure_results_dir, allure_report_dir):
    """备用运行方式"""
    try:
        # 直接使用os.system运行，避免编码问题
        cmd = f'pytest test/ -v --alluredir={allure_results_dir} --self-contained-html --tb=short --clean-alluredir'
        result = os.system(cmd)

        # 生成Allure报告
        generate_allure_report(allure_results_dir, allure_report_dir)

        if result == 0:
            print(f"✅ 所有测试通过！")
        else:
            print(f"❌ 测试失败，返回码: {result}")

        print(f"📊 Allure报告已生成: {allure_report_dir}/index.html")

    except Exception as e:
        print(f"❌ 备用运行方式也失败了: {str(e)}")
        print("请尝试直接运行: pytest test/ -v --alluredir=allure-results")


if __name__ == "__main__":
    run_tests()