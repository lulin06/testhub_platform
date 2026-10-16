"""
测试专用 Django Settings
使用 SQLite 作为测试数据库，避免依赖外部 MySQL 服务
"""
from backend.settings import *  # noqa: F401,F403

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',
    }
}

# 测试时禁用密码验证器，简化用户创建
AUTH_PASSWORD_VALIDATORS = []

# 测试时关闭 Channels（WebSocket 需要 Redis，测试环境不依赖）
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# Django-Q2 test configuration. Task functions can be called directly in tests.
Q_CLUSTER = {**Q_CLUSTER, 'workers': 1, 'orm': 'default'}

# 缓存使用本地内存
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
}
