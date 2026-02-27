import secrets
import os

class Config:
    SECRET_KEY = secrets.token_bytes(32)

    SQLALCHEMY_DATABASE_URI = (
        "mssql+pyodbc://"
        f"{os.getenv('DB_USER')}:"
        f"{os.getenv('DB_PASS')}@"
        f"{os.getenv('DB_HOST')}/"
        f"{os.getenv('DB_NAME')}"
        "?driver=ODBC+Driver+17+for+SQL+Server"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_SECRET_KEY = secrets.token_bytes(32)