import logging
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommandScopeAllPrivateChats, BotCommand
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
import betterlogging as bl

from env_config import load_config
from handlers.user.user_main_router import user_main_router


def get_storage(config):
    if config.tg_bot.use_redis:
        return RedisStorage.from_url(
            config.redis.dsn(),
            key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
        )
    else:
        return MemoryStorage()


def setup_logging():
    log_level = logging.INFO
    bl.basic_colorized_config(level=log_level)

    logging.basicConfig(
        level=logging.INFO,
        format="%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s",
    )


async def on_startup():
    logging.info("Starting bot")


async def on_shutdown(bot):
    logging.info("Shutdown bot")


async def main():
    setup_logging()
    config = load_config()
    storage = get_storage(config)

    bot = Bot(token=config.tg_bot.token)
    dp = Dispatcher(storage=storage)
    dp.include_routers(user_main_router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(commands=[BotCommand(command='start', description='Запустить бота')],
                              scope=BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Бот был выключен!")
