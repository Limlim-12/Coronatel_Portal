# extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize Flask extensions without app context
db = SQLAlchemy()
login_manager = LoginManager()

# Optional: You can configure the login view here if needed
# login_manager.login_view = 'auth.login'  # replace 'auth.login' with your login endpoint
