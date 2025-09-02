import asyncio
import os

import asyncpg
import json
from typing import Optional

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

class Database:
    def __init__(self, db_config: dict):
        self.db_config = db_config
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Инициализирует пул соединений"""
        self.pool = await asyncpg.create_pool(**self.db_config)
        print("✅ Database connected.")

    async def close(self):
        """Закрывает пул соединений"""
        if self.pool:
            await self.pool.close()
            print("✅ Database disconnected.")

    # ---------------------- USERS ----------------------

    async def get_user_data(self, telegram_id: int) -> Optional[dict]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1", telegram_id
            )
            return dict(row) if row else None


    async def add_user(self, telegram_id: int):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                try:
                    await conn.execute(
                        "INSERT INTO users (telegram_id, registration_date) VALUES ($1, NOW())",
                        telegram_id,
                    )
                    print(f"✅ User {telegram_id} added.")
                except Exception as e:
                    print(f"❌ Error adding user: {e}")
                
    async def get_user_dictionaries(self, telegram_id: int) -> Optional[dict]:
        user = await self.get_user_data(telegram_id)
        if user and user.get("dictionaries"):
            dictionaries = user["dictionaries"]
            if isinstance(dictionaries, str):
                return json.loads(dictionaries)
            return dictionaries
        return {}

    async def __update_dictionaries(self, telegram_id: int, dictionaries: dict):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "UPDATE users SET dictionaries = $1 WHERE telegram_id = $2",
                    json.dumps(dictionaries), telegram_id
                )

    async def add_user_dictionaries(self, telegram_id: int, dict_name: str):
        dictionaries = await self.get_user_dictionaries(telegram_id)
        dictionaries[dict_name] = {}
        await self.__update_dictionaries(telegram_id, dictionaries)

    async def add_word_to_dict(self, telegram_id: int, dict_name: str, word: str):
        dictionaries = await self.get_user_dictionaries(telegram_id)

        if dict_name not in dictionaries or not isinstance(dictionaries[dict_name], dict):
            dictionaries[dict_name] = {}

        try:
            word1, word2 = word.split(":")
            word1 = word1.lower()
            word2 = word2.lower()
            dictionaries[dict_name][word1.strip()] = word2.strip()
        except ValueError:
            print("❌ Invalid word format. Use 'word:translation'.")
            return

        await self.__update_dictionaries(telegram_id, dictionaries)

    async def delete_word_from_dict(self, telegram_id: int, dict_name: str, word: str):
        dictionaries = await self.get_user_dictionaries(telegram_id)

        if dict_name in dictionaries and word in dictionaries[dict_name]:
            dictionaries[dict_name].pop(word)
            await self.__update_dictionaries(telegram_id, dictionaries)
        else:
            print(f"❌ Word '{word}' not found in dictionary '{dict_name}'.")

    async def edit_word_in_dict(self, telegram_id: int, dict_name: str, word: str, new_translation: str):
        dictionaries = await self.get_user_dictionaries(telegram_id)
        current_dict = dictionaries[dict_name]

        if dict_name in dictionaries and word in current_dict:
            current_dict[new_translation] = current_dict.pop(word)
            await self.__update_dictionaries(telegram_id, dictionaries)
        elif dict_name in dictionaries and word in current_dict.values():
            for key in current_dict:
                if current_dict[key] == word:
                    current_dict[key] = new_translation
                    break
            await self.__update_dictionaries(telegram_id, dictionaries)
        else:
            print(f"❌ Word '{word}' not found in dictionary '{dict_name}'.")

    async def delete_dictionary(self, telegram_id: int, dict_name: str):
        dictionaries = await self.get_user_dictionaries(telegram_id)

        if dict_name in dictionaries:
            dictionaries.pop(dict_name)
            await self.__update_dictionaries(telegram_id, dictionaries)
        else:
            print(f"❌ Dictionary '{dict_name}' not found for user {telegram_id}.")

