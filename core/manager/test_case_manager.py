"""测试用例管理模块"""
from typing import Dict, List, Any

from common.excel.excel_parser import read_test_cases_from_excel
from common.log.logger import Logger

logger = Logger().get_logger()


class TestCaseManager:
    """测试用例管理类，负责测试用例的加载、依赖分析和执行"""
    
    def __init__(self, excel_file: str):
        self.excel_file = excel_file
        self.all_test_cases: List[Dict[str, Any]] = []
        self.processed_test_cases_map: Dict[str, Dict[str, Any]] = {}
        self.executed_test_cases: Dict[str, Dict[str, Any]] = {}
        self.dependency_graph: Dict[str, List[str]] = {}
    
    def load_test_cases(self) -> bool:
        """加载并预处理所有测试用例"""
        logger.info(f"Reading test cases from {self.excel_file}...")
        try:
            self.all_test_cases = read_test_cases_from_excel(self.excel_file)
            
            # 将测试用例按 test_case_id 存储到字典中，方便查找依赖
            self.processed_test_cases_map = {
                case['test_case_id']: case for case in self.all_test_cases
            }
            
            # 构建依赖关系图
            self._build_dependency_graph()
            
            # 检查循环依赖
            self._check_circular_dependencies()
            
            logger.info(f"Successfully loaded {len(self.all_test_cases)} test cases.")
            return True
        except Exception as e:
            logger.error(f"Failed to load test cases: {e}")
            return False
    
    def _build_dependency_graph(self) -> None:
        """构建测试用例依赖关系图"""
        self.dependency_graph = {}
        
        for case in self.all_test_cases:
            case_id = case['test_case_id']
            pre_condition = case.get('pre_condition_tc')
            
            # 初始化依赖图
            if case_id not in self.dependency_graph:
                self.dependency_graph[case_id] = []
            
            # 添加依赖关系
            if pre_condition:
                if pre_condition not in self.dependency_graph:
                    self.dependency_graph[pre_condition] = []
                self.dependency_graph[pre_condition].append(case_id)
    
    def _check_circular_dependencies(self) -> None:
        """检查循环依赖"""
        visited = {}
        rec_stack = {}
        
        def is_cyclic_util(case_id: str) -> bool:
            visited[case_id] = True
            rec_stack[case_id] = True
            
            # 检查所有依赖此用例的用例
            for dependent in self.dependency_graph.get(case_id, []):
                # 如果未访问，则递归检查
                if not visited.get(dependent, False):
                    if is_cyclic_util(dependent):
                        return True
                # 如果在递归栈中，则存在循环
                elif rec_stack.get(dependent, False):
                    return True
            
            # 回溯时从递归栈中移除
            rec_stack[case_id] = False
            return False
        
        # 检查所有用例
        for case_id in self.dependency_graph:
            if not visited.get(case_id, False):
                if is_cyclic_util(case_id):
                    raise ValueError(f"Circular dependency detected in test cases involving {case_id}")
    
    def get_runnable_test_cases(self) -> List[Dict[str, Any]]:
        """获取可运行的测试用例"""
        return [case for case in self.all_test_cases if case.get('is_run')]
    
    def get_test_case_by_id(self, test_case_id: str) -> Dict[str, Any]:
        """根据ID获取测试用例"""
        return self.processed_test_cases_map.get(test_case_id)
    
    def mark_test_case_executed(self, test_case_id: str, result: Dict[str, Any]) -> None:
        """标记测试用例已执行"""
        self.executed_test_cases[test_case_id] = result
    
    def is_test_case_executed(self, test_case_id: str) -> bool:
        """检查测试用例是否已执行"""
        return test_case_id in self.executed_test_cases
    
    def get_execution_result(self, test_case_id: str) -> Dict[str, Any]:
        """获取测试用例执行结果"""
        return self.executed_test_cases.get(test_case_id)
    
    def clear_execution_results(self) -> None:
        """清空执行结果"""
        self.executed_test_cases.clear()