"""测试执行器模块"""
import time
import concurrent.futures
from typing import Dict, List, Any

from common.http.request_util import RequestUtil
from common.patterns import CacheSingleton
from common.validators.assert_util import assert_response
from common.log.logger import Logger
from core.manager.test_case_manager import TestCaseManager

logger = Logger().get_logger()


class TestExecutor:
    """测试执行器类，负责执行测试用例"""
    
    def __init__(self, request_client: RequestUtil, test_case_manager: TestCaseManager):
        self.request_client = request_client
        self.test_case_manager = test_case_manager
        self.cache = CacheSingleton()
    
    def execute_test_case(self, test_case_data: Dict[str, Any], is_dependency: bool = False) -> Dict[str, Any]:
        """执行单个测试用例
        
        Args:
            test_case_data: 测试用例数据
            is_dependency: 是否作为依赖执行
        
        Returns:
            包含执行结果的字典
        """
        test_case_id = test_case_data.get('test_case_id', 'N/A')
        
        # 如果已经执行过，直接返回结果
        if self.test_case_manager.is_test_case_executed(test_case_id) and not is_dependency:
            return self.test_case_manager.get_execution_result(test_case_id)
        
        start_time = time.time()
        result = {
            'test_case_id': test_case_id,
            'success': False,
            'response': None,
            'error': None,
            'duration': 0,
            'extracted_vars': {}
        }
        
        try:
            # 执行前置依赖
            pre_condition_tc = test_case_data.get('pre_condition_tc')
            if pre_condition_tc:
                self._execute_dependency(pre_condition_tc)
            
            # 执行当前请求
            method = test_case_data.get('method')
            path = test_case_data.get('path')
            headers = test_case_data.get('headers')
            params = test_case_data.get('params')
            body = test_case_data.get('body')
            extract_vars = test_case_data.get('extract_vars', {})
            asserts = test_case_data.get('asserts', [])
            
            # 发送请求
            response = self.request_client.send_request(
                method, path, headers=headers, params=params, body=body
            )
            result['response'] = response
            
            # 提取变量
            if extract_vars:
                extracted = self.request_client.extract_variables_from_response(response, extract_vars)
                result['extracted_vars'] = extracted
            
            # 执行断言
            assertion_results = assert_response(response, asserts)
            result['assertion_results'] = assertion_results
            result['success'] = (
                all(ar.success for ar in assertion_results) 
                if isinstance(assertion_results, list) 
                else assertion_results
            )
            
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
        finally:
            result['duration'] = time.time() - start_time
            
            # 存储执行结果
            if not is_dependency:
                self.test_case_manager.mark_test_case_executed(test_case_id, result)
        
        return result
    
    def _execute_dependency(self, dependency_id: str) -> Dict[str, Any]:
        """执行依赖测试用例
        
        Args:
            dependency_id: 依赖的测试用例ID
        
        Returns:
            依赖测试用例的执行结果
        """
        # 检查依赖是否已执行
        if self.test_case_manager.is_test_case_executed(dependency_id):
            return self.test_case_manager.get_execution_result(dependency_id)
        
        # 获取依赖测试用例数据
        dependent_case = self.test_case_manager.get_test_case_by_id(dependency_id)
        if not dependent_case:
            raise ValueError(f"Dependency test case '{dependency_id}' not found.")
        
        # 执行依赖测试用例
        logger.info(f"Executing dependency test case: {dependency_id}")
        result = self.execute_test_case(dependent_case, is_dependency=True)
        
        # 检查依赖执行结果
        if not result['success']:
            raise ValueError(f"Dependency test case '{dependency_id}' failed: {result['error']}")
        
        return result
    
    def execute_test_cases_in_parallel(
        self, 
        test_cases: List[Dict[str, Any]], 
        max_workers: int = 4
    ) -> Dict[str, Dict[str, Any]]:
        """并行执行多个测试用例
        
        Args:
            test_cases: 测试用例列表
            max_workers: 最大工作线程数
        
        Returns:
            测试用例ID到执行结果的映射
        """
        results = {}
        
        # 按照依赖关系对测试用例进行排序
        sorted_test_cases = self._sort_test_cases_by_dependency(test_cases)
        
        # 分批执行测试用例
        batches = self._create_execution_batches(sorted_test_cases)
        logger.info(f"Created {len(batches)} execution batches for parallel processing")
        
        for batch_index, batch in enumerate(batches):
            logger.info(f"Executing batch {batch_index + 1}/{len(batches)} with {len(batch)} test cases")
            
            # 使用线程池并行执行当前批次的测试用例
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(max_workers, len(batch))) as executor:
                # 提交所有任务
                future_to_case = {executor.submit(self.execute_test_case, case): case for case in batch}
                
                # 收集结果
                for future in concurrent.futures.as_completed(future_to_case):
                    case = future_to_case[future]
                    case_id = case.get('test_case_id')
                    try:
                        result = future.result()
                        results[case_id] = result
                        status = "✅ 成功" if result['success'] else "❌ 失败"
                        logger.info(f"Test case {case_id} completed: {status} in {result['duration']:.2f}s")
                    except Exception as e:
                        logger.error(f"Test case {case_id} raised an exception: {e}")
                        results[case_id] = {
                            'test_case_id': case_id,
                            'success': False,
                            'error': str(e),
                            'duration': 0
                        }
        
        return results
    
    def _sort_test_cases_by_dependency(self, test_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """根据依赖关系对测试用例进行排序
        
        Args:
            test_cases: 测试用例列表
        
        Returns:
            排序后的测试用例列表
        """
        # 创建依赖图
        dependency_graph = {}
        for case in test_cases:
            case_id = case['test_case_id']
            dependency_graph[case_id] = case.get('pre_condition_tc')
        
        # 拓扑排序
        sorted_cases = []
        visited = set()
        temp_visited = set()
        
        def visit(case_id: str) -> None:
            if case_id in temp_visited:
                raise ValueError(f"Circular dependency detected involving {case_id}")
            
            if case_id not in visited:
                temp_visited.add(case_id)
                
                # 访问依赖
                dependency = dependency_graph.get(case_id)
                if dependency:
                    visit(dependency)
                
                temp_visited.remove(case_id)
                visited.add(case_id)
                sorted_cases.append(case_id)
        
        # 对每个测试用例执行拓扑排序
        for case in test_cases:
            case_id = case['test_case_id']
            if case_id not in visited:
                visit(case_id)
        
        # 根据排序结果重新排列测试用例
        case_map = {case['test_case_id']: case for case in test_cases}
        return [case_map[case_id] for case_id in sorted_cases if case_id in case_map]
    
    def _create_execution_batches(self, sorted_test_cases: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """创建测试用例执行批次
        
        将测试用例分成多个批次，每个批次中的测试用例可以并行执行
        同一批次中的测试用例之间没有依赖关系
        
        Args:
            sorted_test_cases: 按依赖关系排序的测试用例列表
        
        Returns:
            测试用例批次列表
        """
        batches = []
        current_batch = []
        processed_dependencies = set()
        
        for case in sorted_test_cases:
            case_id = case['test_case_id']
            dependency = case.get('pre_condition_tc')
            
            # 如果没有依赖，或者依赖已经处理过，则可以加入当前批次
            if not dependency or dependency in processed_dependencies:
                current_batch.append(case)
            else:
                # 如果有未处理的依赖，则开始新的批次
                if current_batch:
                    batches.append(current_batch)
                    # 记录已处理的测试用例ID
                    for processed_case in current_batch:
                        processed_dependencies.add(processed_case['test_case_id'])
                    current_batch = [case]
                else:
                    current_batch.append(case)
        
        # 添加最后一个批次
        if current_batch:
            batches.append(current_batch)
        
        return batches