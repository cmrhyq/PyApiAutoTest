"""JSON Schema 定义

此模块包含用于验证API响应的JSON Schema定义
"""

from typing import Dict, Any
from model.entity.jsonplaceholder_schemas import JSONPLACEHOLDER_SCHEMAS

# 用户信息Schema
USER_PROFILE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["success", "data"],
    "properties": {
        "success": {"type": "boolean"},
        "data": {
            "type": "object",
            "required": ["id", "username", "nickname", "email"],
            "properties": {
                "id": {"type": "integer"},
                "username": {"type": "string"},
                "nickname": {"type": "string"},
                "email": {"type": "string", "format": "email"},
                "avatar": {"type": ["string", "null"]},
                "created_at": {"type": "string", "format": "date-time"},
                "updated_at": {"type": "string", "format": "date-time"}
            }
        }
    }
}

# 登录响应Schema
LOGIN_RESPONSE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["success", "data"],
    "properties": {
        "success": {"type": "boolean"},
        "data": {
            "type": "object",
            "required": ["access_token", "refresh_token", "user"],
            "properties": {
                "access_token": {"type": "string"},
                "refresh_token": {"type": "string"},
                "user": {
                    "type": "object",
                    "required": ["id", "username"],
                    "properties": {
                        "id": {"type": "integer"},
                        "username": {"type": "string"},
                        "nickname": {"type": "string"}
                    }
                }
            }
        }
    }
}

# 通用成功响应Schema
SUCCESS_RESPONSE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["success"],
    "properties": {
        "success": {"type": "boolean"},
        "message": {"type": "string"}
    }
}

# 错误响应Schema
ERROR_RESPONSE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["success", "error"],
    "properties": {
        "success": {"type": "boolean"},
        "error": {
            "type": "object",
            "required": ["code", "message"],
            "properties": {
                "code": {"type": "string"},
                "message": {"type": "string"}
            }
        }
    }
}

# 导出所有Schema
SCHEMAS = {
    "user_profile_schema": USER_PROFILE_SCHEMA,
    "login_response_schema": LOGIN_RESPONSE_SCHEMA,
    "success_response_schema": SUCCESS_RESPONSE_SCHEMA,
    "error_response_schema": ERROR_RESPONSE_SCHEMA,
    # 添加JSONPlaceholder的Schema
    **JSONPLACEHOLDER_SCHEMAS
}