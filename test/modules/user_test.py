import allure
import pytest

@allure.feature("用户接口测试")
class UserTest:
    @pytest.fixture(autouse=True)
    def setup(self, user_api):
        self.user_api = user_api

    @allure.story("获取用户信息")
    @allure.title("测试获取单个用户信息")
    def test_get_user(self):
        user_id = "1"
        with allure.step(f"获取用户 ID 为 {user_id} 的信息"):
            response = self.user_api.get_user(user_id)
        with allure.step("验证响应状态码"):
            assert response.status_code == 200