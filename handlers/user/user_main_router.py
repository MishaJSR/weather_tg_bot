import requests
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from urllib3 import HTTPConnectionPool

user_main_router = Router()


@user_main_router.message(CommandStart())
async def user_start(message: types.Message, state: FSMContext):
    username = "@"
    if message.from_user.username:
        username = message.from_user.username
    try:
        response = requests.post(f"http://127.0.0.1:8000/user/"
                                 f"check_or_create?tg_user_id={message.from_user.id}&user_tag={username}")
    except requests.exceptions.ConnectionError:
        await message.answer(f"Ошибка подключения к серверу")
        return
    await message.answer(f"Привет\n"
                         f"Напиши /weather <Город> чтобы узнать погоду")


@user_main_router.message(Command("weather"))
async def user_start(message: types.Message, state: FSMContext):
    try:
        city = message.text.replace("/weather", "")[1:]
        url = f"http://127.0.0.1:8000/get_weather/get_weather_by_id?user_tg_id={message.from_user.id}&city={city}"
        try:
            response = requests.post(url)
        except requests.exceptions.ConnectionError:
            await message.answer(f"Ошибка подключения к серверу")
            return
        data = response.json()
        if data.get("status_code") == 400:
            detail = data["detail"][0]
            await message.answer(f"{detail}\n"
                                 f"Напиши /weather <Город> чтобы узнать погоду")
        else:
            res_str = ""
            res_list = [el for el in data.values()]
            res_static = ["Город: ", "Температура: ", "Ощущается как: ",
                          "Описание: ", "Влажность: ", "Скорость ветра: "]
            end_param = ["\n", " C\n", " C\n", "\n", " %\n", " м\с\n"]
            for col, par, end in zip(res_static, res_list, end_param):
                res_str += f"{col}{par}{end}"
            await message.answer(res_str)

    except Exception as e:
        await message.answer(f"Ой, наверное вы ошиблись\n"
                         f"Напиши /weather <Город> чтобы узнать погоду")
