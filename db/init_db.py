import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def get_connection():
    return await asyncpg.connect(
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )



