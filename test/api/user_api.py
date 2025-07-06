from core.patterns.decorator.retry import retry_on_failure
from test.test_base import TestBase


class UserApi(TestBase):

    @retry_on_failure()
    def get_user(self, user_id):
        path = f'/users/{user_id}'
        return self.send_request('GET', path)

    def create_user(self, data):
        path = '/users'
        return self.send_request('POST', path, json=data)