"""API响应的JSON Schema定义

此模块包含API响应的JSON Schema定义，用于验证API响应格式
"""

# 用户相关Schema
USER_PROFILE_SCHEMA = {
    "type": "object",
    "required": ["id", "username", "email"],
    "properties": {
        "id": {"type": "integer"},
        "username": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "nickname": {"type": "string"},
        "avatar": {"type": "string"},
        "role": {"type": "string"},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"}
    }
}

LOGIN_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["token", "user"],
    "properties": {
        "token": {"type": "string"},
        "user": USER_PROFILE_SCHEMA
    }
}

# 产品相关Schema
PRODUCT_SCHEMA = {
    "type": "object",
    "required": ["id", "name", "price"],
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "price": {"type": "number"},
        "category_id": {"type": "integer"},
        "category_name": {"type": "string"},
        "image": {"type": "string"},
        "stock": {"type": "integer"},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"}
    }
}

PRODUCT_LIST_SCHEMA = {
    "type": "object",
    "required": ["total", "items"],
    "properties": {
        "total": {"type": "integer"},
        "page": {"type": "integer"},
        "limit": {"type": "integer"},
        "items": {
            "type": "array",
            "items": PRODUCT_SCHEMA
        }
    }
}

PRODUCT_DETAIL_SCHEMA = PRODUCT_SCHEMA

# 订单相关Schema
ORDER_DETAIL_SCHEMA = {
    "type": "object",
    "required": ["id", "user_id", "product_id", "quantity", "total_price", "status"],
    "properties": {
        "id": {"type": "integer"},
        "user_id": {"type": "integer"},
        "product_id": {"type": "integer"},
        "product_name": {"type": "string"},
        "quantity": {"type": "integer"},
        "unit_price": {"type": "number"},
        "total_price": {"type": "number"},
        "status": {"type": "string", "enum": ["pending", "paid", "shipped", "delivered", "cancelled"]},
        "address": {"type": "string"},
        "payment_method": {"type": "string"},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"}
    }
}

ORDER_LIST_SCHEMA = {
    "type": "object",
    "required": ["total", "items"],
    "properties": {
        "total": {"type": "integer"},
        "page": {"type": "integer"},
        "limit": {"type": "integer"},
        "items": {
            "type": "array",
            "items": ORDER_DETAIL_SCHEMA
        }
    }
}

# 支付相关Schema
PAYMENT_DETAIL_SCHEMA = {
    "type": "object",
    "required": ["id", "order_id", "amount", "status"],
    "properties": {
        "id": {"type": "integer"},
        "order_id": {"type": "integer"},
        "amount": {"type": "number"},
        "payment_method": {"type": "string"},
        "status": {"type": "string", "enum": ["processing", "completed", "failed", "refunded"]},
        "transaction_id": {"type": "string"},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"}
    }
}

PAYMENT_LIST_SCHEMA = {
    "type": "object",
    "required": ["total", "items"],
    "properties": {
        "total": {"type": "integer"},
        "page": {"type": "integer"},
        "limit": {"type": "integer"},
        "items": {
            "type": "array",
            "items": PAYMENT_DETAIL_SCHEMA
        }
    }
}

# 通用响应Schema
SUCCESS_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["success"],
    "properties": {
        "success": {"type": "boolean"},
        "message": {"type": "string"}
    }
}

ERROR_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["error"],
    "properties": {
        "error": {"type": "string"},
        "code": {"type": "integer"},
        "details": {"type": "object"}
    }
}

PAGINATION_META_SCHEMA = {
    "type": "object",
    "required": ["total", "page", "limit"],
    "properties": {
        "total": {"type": "integer"},
        "page": {"type": "integer"},
        "limit": {"type": "integer"},
        "pages": {"type": "integer"}
    }
}

# 汇总所有Schema
SCHEMAS = {
    "USER_PROFILE_SCHEMA": USER_PROFILE_SCHEMA,
    "LOGIN_RESPONSE_SCHEMA": LOGIN_RESPONSE_SCHEMA,
    "PRODUCT_SCHEMA": PRODUCT_SCHEMA,
    "PRODUCT_LIST_SCHEMA": PRODUCT_LIST_SCHEMA,
    "PRODUCT_DETAIL_SCHEMA": PRODUCT_DETAIL_SCHEMA,
    "ORDER_DETAIL_SCHEMA": ORDER_DETAIL_SCHEMA,
    "ORDER_LIST_SCHEMA": ORDER_LIST_SCHEMA,
    "PAYMENT_DETAIL_SCHEMA": PAYMENT_DETAIL_SCHEMA,
    "PAYMENT_LIST_SCHEMA": PAYMENT_LIST_SCHEMA,
    "SUCCESS_RESPONSE_SCHEMA": SUCCESS_RESPONSE_SCHEMA,
    "ERROR_RESPONSE_SCHEMA": ERROR_RESPONSE_SCHEMA,
    "PAGINATION_META_SCHEMA": PAGINATION_META_SCHEMA
}