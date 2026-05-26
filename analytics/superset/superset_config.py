import os


SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "change-me-for-local-only")

SQLALCHEMY_DATABASE_URI = (
    "postgresql+psycopg2://"
    f"{os.environ.get('SUPERSET_METADATA_USER', 'superset')}:"
    f"{os.environ.get('SUPERSET_METADATA_PASSWORD', 'change-me-local-metadata-password')}"
    "@superset-db:5432/"
    f"{os.environ.get('SUPERSET_METADATA_DB', 'superset')}"
)

REDIS_HOST = "superset-redis"
REDIS_PORT = 6379

CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_HOST": REDIS_HOST,
    "CACHE_REDIS_PORT": REDIS_PORT,
    "CACHE_REDIS_DB": 1,
}

DATA_CACHE_CONFIG = CACHE_CONFIG
FILTER_STATE_CACHE_CONFIG = CACHE_CONFIG
EXPLORE_FORM_DATA_CACHE_CONFIG = CACHE_CONFIG

FEATURE_FLAGS = {
    "DASHBOARD_NATIVE_FILTERS": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
}

TALISMAN_ENABLED = False
WTF_CSRF_ENABLED = True

SQLLAB_CTAS_NO_LIMIT = True
SQLLAB_TIMEOUT = 300
SUPERSET_WEBSERVER_TIMEOUT = 300
