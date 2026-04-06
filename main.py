from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
import logging
from config import TOKEN
from handlers import router
from database import create_pool, close_pool

logging.basicConfig(level=logging.INFO)

async def main():
    await create_pool()
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    bot = Bot(token=TOKEN)
    dp.include_router(router)

    try:
         logging.info("Starting polling...")
         await dp.start_polling(bot)
    finally:
         logging.info("Closing pool...")
         await close_pool()

if __name__ == "__main__":
        asyncio.run(main())