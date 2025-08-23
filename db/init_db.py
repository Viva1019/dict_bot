import os
from db.models import Database

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

db_config = {
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

db = Database(db_config)