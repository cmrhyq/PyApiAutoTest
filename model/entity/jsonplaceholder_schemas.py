"""JSONPlaceholder API响应的JSON Schema定义

此模块包含JSONPlaceholder API响应的JSON Schema定义，用于验证API响应格式
"""

# 帖子相关Schema
POST_SCHEMA = {
    "type": "object",
    "required": ["id", "userId", "title", "body"],
    "properties": {
        "id": {"type": "integer"},
        "userId": {"type": "integer"},
        "title": {"type": "string"},
        "body": {"type": "string"}
    }
}

POSTS_LIST_SCHEMA = {
    "type": "array",
    "items": POST_SCHEMA
}

# 评论相关Schema
COMMENT_SCHEMA = {
    "type": "object",
    "required": ["id", "postId", "name", "email", "body"],
    "properties": {
        "id": {"type": "integer"},
        "postId": {"type": "integer"},
        "name": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "body": {"type": "string"}
    }
}

COMMENTS_LIST_SCHEMA = {
    "type": "array",
    "items": COMMENT_SCHEMA
}

# 用户相关Schema
USER_ADDRESS_SCHEMA = {
    "type": "object",
    "required": ["street", "suite", "city", "zipcode", "geo"],
    "properties": {
        "street": {"type": "string"},
        "suite": {"type": "string"},
        "city": {"type": "string"},
        "zipcode": {"type": "string"},
        "geo": {
            "type": "object",
            "required": ["lat", "lng"],
            "properties": {
                "lat": {"type": "string"},
                "lng": {"type": "string"}
            }
        }
    }
}

USER_COMPANY_SCHEMA = {
    "type": "object",
    "required": ["name", "catchPhrase", "bs"],
    "properties": {
        "name": {"type": "string"},
        "catchPhrase": {"type": "string"},
        "bs": {"type": "string"}
    }
}

USER_SCHEMA = {
    "type": "object",
    "required": ["id", "name", "username", "email", "address", "phone", "website", "company"],
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "username": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "address": USER_ADDRESS_SCHEMA,
        "phone": {"type": "string"},
        "website": {"type": "string"},
        "company": USER_COMPANY_SCHEMA
    }
}

USERS_LIST_SCHEMA = {
    "type": "array",
    "items": USER_SCHEMA
}

# 待办事项相关Schema
TODO_SCHEMA = {
    "type": "object",
    "required": ["id", "userId", "title", "completed"],
    "properties": {
        "id": {"type": "integer"},
        "userId": {"type": "integer"},
        "title": {"type": "string"},
        "completed": {"type": "boolean"}
    }
}

TODOS_LIST_SCHEMA = {
    "type": "array",
    "items": TODO_SCHEMA
}

# 相册相关Schema
ALBUM_SCHEMA = {
    "type": "object",
    "required": ["id", "userId", "title"],
    "properties": {
        "id": {"type": "integer"},
        "userId": {"type": "integer"},
        "title": {"type": "string"}
    }
}

ALBUMS_LIST_SCHEMA = {
    "type": "array",
    "items": ALBUM_SCHEMA
}

# 照片相关Schema
PHOTO_SCHEMA = {
    "type": "object",
    "required": ["id", "albumId", "title", "url", "thumbnailUrl"],
    "properties": {
        "id": {"type": "integer"},
        "albumId": {"type": "integer"},
        "title": {"type": "string"},
        "url": {"type": "string", "format": "uri"},
        "thumbnailUrl": {"type": "string", "format": "uri"}
    }
}

PHOTOS_LIST_SCHEMA = {
    "type": "array",
    "items": PHOTO_SCHEMA
}

# 汇总所有Schema
JSONPLACEHOLDER_SCHEMAS = {
    "POST_SCHEMA": POST_SCHEMA,
    "POSTS_LIST_SCHEMA": POSTS_LIST_SCHEMA,
    "COMMENT_SCHEMA": COMMENT_SCHEMA,
    "COMMENTS_LIST_SCHEMA": COMMENTS_LIST_SCHEMA,
    "USER_SCHEMA": USER_SCHEMA,
    "USERS_LIST_SCHEMA": USERS_LIST_SCHEMA,
    "TODO_SCHEMA": TODO_SCHEMA,
    "TODOS_LIST_SCHEMA": TODOS_LIST_SCHEMA,
    "ALBUM_SCHEMA": ALBUM_SCHEMA,
    "ALBUMS_LIST_SCHEMA": ALBUMS_LIST_SCHEMA,
    "PHOTO_SCHEMA": PHOTO_SCHEMA,
    "PHOTOS_LIST_SCHEMA": PHOTOS_LIST_SCHEMA
}