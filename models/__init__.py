
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
from .user import User, OAuth, login_manager
from .function import Function