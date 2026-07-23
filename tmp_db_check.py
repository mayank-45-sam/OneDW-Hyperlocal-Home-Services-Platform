import asyncio
from app.database.connection import connect_to_mongo, get_database

async def main():
    await connect_to_mongo()
    db = get_database()
    print(type(db).__name__)
    result = await db.users.insert_one({'email': 'demo@example.com', 'password': 'x'})
    print(type(result).__name__, str(result.inserted_id))

asyncio.run(main())
