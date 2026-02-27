import secrets
from sqlalchemy.engine import URL

class Config:
    SECRET_KEY = secrets.token_bytes(32)

    SQLALCHEMY_DATABASE_URI = URL.create(
        "mssql+pyodbc",
        username="busines8_sa",
        password="N0v3ll!@#$%67890",
        host="server6.hndservers.net",
        port=2019,
        database="busines8_chrm",
        query={
            "driver": "ODBC Driver 17 for SQL Server",
            "Encrypt": "yes",
            "TrustServerCertificate": "yes"
        }
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_SECRET_KEY = secrets.token_bytes(32)