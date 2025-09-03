import asyncio
import os
from db.models import Database

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
db_config = {
    "database": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("PGHOST"),
    "port": os.getenv("PGPORT")
}


db = Database(db_config)


