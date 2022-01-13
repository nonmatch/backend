import logging
from utils import get_env_variable

class Config(object):
    POSTGRES_URL = get_env_variable('POSTGRES_URL')
    POSTGRES_USER = get_env_variable('POSTGRES_USER')
    POSTGRES_PASSWORD = get_env_variable('POSTGRES_PASSWORD')
    POSTGRES_DB = get_env_variable('POSTGRES_DB')

    DEBUG = False
    TESTING = False
    # SQLAlchemy
    uri_template = 'postgresql+psycopg2://{user}:{pw}@{url}/{db}'
    SQLALCHEMY_DATABASE_URI = uri_template.format(
        user=POSTGRES_USER,
        pw=POSTGRES_PASSWORD,
        url=POSTGRES_URL,
        db=POSTGRES_DB)

    # Silence the deprecation warning
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # API settings
    API_PAGINATION_PER_PAGE = 10

    SECRET_KEY=get_env_variable('SECRET_KEY')
    FRONTEND_URL=get_env_variable('FRONTEND_URL')


class DevelopmentConfig(Config):
    DEBUG = True


class TestConfig(Config):
    TESTING = True


class ProductionConfig(Config):
    # production config
    pass


def get_config(env=None):
    if env is None:
        try:
            env = get_env_variable('ENV')
        except Exception:
            env = 'development'
            logging.error('env is not set, using env:', env)

    if env == 'production':
        return ProductionConfig()
    elif env == 'test':
        return TestConfig()

    return DevelopmentConfig()