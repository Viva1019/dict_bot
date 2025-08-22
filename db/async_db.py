import asyncpg
import json
import asyncio
from db.init_db import get_connection


async def get_user_data(user_id):
    conn = await get_connection()
    user = await conn.fetchrow("SELECT * FROM users WHERE telegram_id = $1", user_id)
    await conn.close()
    return dict(user) if user else None


async def add_user(telegram_id):
    conn = await get_connection()
    try:
        await conn.execute(
            "INSERT INTO users (telegram_id, registration_date) VALUES ($1, NOW())",
            telegram_id
        )
        print(f"User with ID {telegram_id} added successfully.")
    except Exception as e:
        print(f"Error adding user: {e}")
    await conn.close()


async def get_user_dictionaries(telegram_id):
    user_data = await get_user_data(telegram_id)
    if user_data and user_data.get("dictionaries"):
        if isinstance(user_data["dictionaries"], str):
            return json.loads(user_data["dictionaries"])
        return user_data["dictionaries"]
    return None


async def add_user_dictionaries(telegram_id, dict_name):
    dictionaries = await get_user_dictionaries(telegram_id)
    if dictionaries is not None:
        dictionaries[dict_name] = {}
        conn = await get_connection()
        await conn.execute(
            "UPDATE users SET dictionaries = $1 WHERE telegram_id = $2",
            json.dumps(dictionaries), telegram_id
        )
        await conn.close()


async def add_word_to_dict(telegram_id, dictionary_name, word):
    dictionaries = await get_user_dictionaries(telegram_id)
    if dictionaries is not None:
        if dictionary_name not in dictionaries or not isinstance(dictionaries[dictionary_name], dict):
            dictionaries[dictionary_name] = {}

        try:
            word1, word2 = word.split(":")
            dictionaries[dictionary_name][word1] = word2
        except ValueError:
            print("Word must be in 'word1:word2' format")
            return

        conn = await get_connection()
        await conn.execute(
            "UPDATE users SET dictionaries = $1 WHERE telegram_id = $2",
            json.dumps(dictionaries), telegram_id
        )
        await conn.close()


async def delete_word_from_dict(telegram_id, dictionary_name, word):
    dictionaries = await get_user_dictionaries(telegram_id)
    if dictionaries is not None:
        if dictionary_name in dictionaries and word in dictionaries[dictionary_name]:
            dictionaries[dictionary_name].pop(word)
            conn = await get_connection()
            await conn.execute(
                "UPDATE users SET dictionaries = $1 WHERE telegram_id = $2",
                json.dumps(dictionaries), telegram_id
            )
            await conn.close()
        else:
            print(f"Word '{word}' not found in dictionary '{dictionary_name}' for user {telegram_id}.")


async def delete_dictionary(telegram_id, dictionary_name):
    dictionaries = await get_user_dictionaries(telegram_id)
    if dictionaries is not None:
        if dictionary_name in dictionaries:
            dictionaries.pop(dictionary_name)
            conn = await get_connection()
            await conn.execute(
                "UPDATE users SET dictionaries = $1 WHERE telegram_id = $2",
                json.dumps(dictionaries), telegram_id
            )
            await conn.close()
        else:
            print(f"Dictionary '{dictionary_name}' not found for user {telegram_id}.")


async def main():
    # await add_user_dictionaries(123123, "rus")
    # await add_word_to_dict(123123, "rus", "value1:value2")
    # await delete_word_from_dict(123123, "rus", "value1")
    await delete_dictionary(123123, "rus")
    dicts = await get_user_dictionaries(123123)
    print(dicts)

asyncio.run(main())