import pandas as pd
import json
from common.log import Logger


logger = Logger().get_logger()

def read_test_cases_from_excel(file_path):
    """从 Excel 文件读取测试用例"""
    try:
        df = pd.read_excel(file_path, sheet_name='Sheet1').fillna('') # 读取第一个sheet，空值填充为空字符串
        test_cases = df.to_dict(orient='records')
        parsed_cases = []
        for case in test_cases:
            parsed_case = {k: v for k, v in case.items()} # 复制一份，避免直接修改原始dict

            # 尝试解析 JSON 字符串
            for key in ['headers', 'params', 'extract_vars', 'asserts']:
                if isinstance(parsed_case.get(key), str) and parsed_case[key].strip():
                    try:
                        parsed_case[key] = json.loads(parsed_case[key])
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON parsing error for {key} in test case {case.get('test_case_id')}: {e}")
                        parsed_case[key] = {} # 解析失败则设为空字典
                else:
                    parsed_case[key] = {} # 确保是字典类型

            # 处理 is_run 字段
            if isinstance(parsed_case.get('is_run'), str):
                parsed_case['is_run'] = parsed_case['is_run'].strip().lower() == 'true'
            else:
                parsed_case['is_run'] = bool(parsed_case['is_run']) # 确保是布尔值

            parsed_cases.append(parsed_case)
        return parsed_cases
    except Exception as e:
        logger.error(f"Error reading or parsing Excel file {file_path}: {e}")
        return []