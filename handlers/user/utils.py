import logging
import os
import random

from aiogram import types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, FSInputFile

from database.models import UserRepository, TaskRepository, TheoryRepository, UserProgressRepository
from database.utils.AlchemyDataObject import AlchemyDataObject
from database.utils.construct_schemas import ConstructUser, ConstructUserProgress
from keyboards.user.reply_user import answer_mode_kb, under_chapter_kb, start_profile_kb
from utils.common.levels import levels, levels_arr
from utils.common.static_url import path_to_imgs, imgs_format
from utils.common.static_user import *


async def send_question(message: types.Message, user_state, state: FSMContext) -> object:
    if user_state.questions:
        user_state.now_question = random.choice(user_state.questions)
        user_state.questions.remove(user_state.now_question)
        res_message = f"<b>{user_state.now_question.description}</b>\n\n" \
                      f"{user_state.now_question.answers}\n"
        await message.answer(res_message, parse_mode=ParseMode.HTML, reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer("Задания закончились", reply_markup=answer_mode_kb())
        await state.set_state(user_state.answer_mode)


async def check_user(user_id: int) -> str | bool:
    user_field = ["username"]
    user_filter = {
        "user_id": user_id
    }
    res = await UserRepository().get_one_by_fields(data=user_field, field_filter=user_filter)
    if res:
        return res.username
    return False


async def add_new_user(user_id: int, username: str):
    try:
        new_user = ConstructUser(user_id=user_id,
                                 username=username,
                                 is_subscribe=True).model_dump()
        await UserRepository().add_object(data=new_user)
    except Exception as e:
        logging.info(f"Ошибка регистрации пользователя {e}")


async def get_all_chapters() -> list[str]:
    task_fields = ["chapter"]
    rows = await TaskRepository().get_all_by_fields(data=task_fields, distinct=True)
    return [el.chapter for el in rows]


async def get_all_under_chapters(chapter) -> list[str]:
    task_fields = ["under_chapter"]
    task_filter = {
        "chapter": chapter
    }
    rows = await TaskRepository().get_all_by_fields(data=task_fields, field_filter=task_filter, distinct=True)
    return [el.under_chapter for el in rows]


async def get_questions(under_chapter) -> AlchemyDataObject:
    task_fields = ["id", "chapter", "under_chapter", "description", "answers", "answer", "about"]
    task_filter = {"under_chapter": under_chapter}
    rows = await TaskRepository().get_all_by_fields(data=task_fields, field_filter=task_filter)
    return rows


async def update_progress(status, message, now_question):
    update_filter = {
        "chapter": now_question.chapter,
        "under_chapter": now_question.under_chapter,
        "user_id": message.from_user.id,
        "question_id": now_question.id,
        "is_pass": False
    }
    update_data = {
        "is_pass": status
    }
    check_filter = {
        "question_id": now_question.id
    }
    is_already_add = await UserProgressRepository().get_one_by_fields(data=["id"], field_filter=check_filter)
    await UserProgressRepository().update_fields(update_data=update_data, update_filter=update_filter)
    if not is_already_add:
        new_progress = ConstructUserProgress(chapter=now_question.chapter,
                                             under_chapter=now_question.under_chapter,
                                             user_id=message.from_user.id,
                                             question_id=now_question.id,
                                             is_pass=status).model_dump()
        await UserProgressRepository().add_object(data=new_progress)


async def go_to_under_chapters(message: types.Message, user_state):
    if len(user_state.list_of_under_chapters) == 1:
        await message.answer(TEXT_UNDER_CHAPTER,
                             reply_markup=under_chapter_kb(data=user_state.list_of_under_chapters))
    else:
        user_state.index_now_under_chapter = 0
        await message.answer(TEXT_UNDER_CHAPTER,
                             reply_markup=under_chapter_kb(data=user_state.list_of_under_chapters[0], is_more=True))


async def update_under_chapters(message: types.Message, user_state):
    cur_ind = user_state.index_now_under_chapter
    has_more_button = len(user_state.list_of_under_chapters) - 1 == cur_ind
    is_return = False
    if cur_ind != 0:
        is_return = True
    if user_state.index_now_under_chapter < len(user_state.list_of_under_chapters):
        if has_more_button:
            await message.answer(TEXT_UNDER_CHAPTER,
                                 reply_markup=under_chapter_kb(data=user_state.list_of_under_chapters[cur_ind],
                                                               is_return=True))
        else:
            await message.answer(TEXT_UNDER_CHAPTER,
                                 reply_markup=under_chapter_kb(data=user_state.list_of_under_chapters[cur_ind],
                                                               is_more=True,
                                                               is_return=is_return))
    else:
        await message.answer(EMPTY_UNDER_CHAPTERS)


def split_array(arr, chunk_size):
    return [arr[i:i + chunk_size] for i in range(0, len(arr), chunk_size)]


async def send_theory(message: types.Message, user_state):
    theory_field = ["text", "photo_id"]
    theory_filter = {
        "under_chapter": user_state.select_under_chapter
    }
    posts = await TheoryRepository().get_all_by_fields(data=theory_field, field_filter=theory_filter)
    for post in posts:
        if post.photo_id:
            await message.answer_photo(photo=post.photo_id)
        await message.answer(post.text, parse_mode=ParseMode.HTML)


async def count_statistic(message: types.Message, flag="all", chapter=None, under_chapter=None):
    match flag:
        case "chapter":
            field_filter_ready = {
                "chapter": chapter,
                "user_id": message.from_user.id,
                "is_pass": True
            }
            field_filter_user = {
                "chapter": chapter,
                "user_id": message.from_user.id
            }
            field_filter_all = {
                "chapter": chapter,
            }
        case "under_chapter":
            field_filter_ready = {
                "under_chapter": under_chapter,
                "user_id": message.from_user.id,
                "is_pass": True
            }
            field_filter_user = {
                "under_chapter": under_chapter,
                "user_id": message.from_user.id
            }
            field_filter_all = {
                "under_chapter": under_chapter
            }
        case _:
            field_filter_ready = {
                "user_id": message.from_user.id,
                "is_pass": True
            }
            field_filter_user = {
                "user_id": message.from_user.id
            }
            field_filter_all = None


    data = ["id"]
    all_tasks = await TaskRepository().get_all_by_fields(data=data, field_filter=field_filter_all)
    all_user_tasks = await UserProgressRepository().get_all_by_fields(data=data, field_filter=field_filter_user)
    all_user_ready_tasks = await UserProgressRepository().get_all_by_fields(data=data, field_filter=field_filter_ready)
    percent = round(len(all_user_tasks) / len(all_tasks) * 100, 2)
    if len(all_user_tasks) == 0:
        percent_ready = 0
    else:
        percent_ready = round(len(all_user_ready_tasks) / len(all_user_tasks) * 100, 2)
    status = closest_number(levels, int(percent * percent_ready))
    return percent, len(all_user_tasks), len(all_tasks), percent_ready, status


async def send_status(message: types.Message, status, points=0):
    all_users = await UserRepository().get_all_by_fields(data=["id"])
    name = os.getcwd() + path_to_imgs + f"{status}.{imgs_format}"
    file = FSInputFile(name)
    update_data = {
        "points": points
    }
    update_filter = {
        "user_id": message.from_user.id
    }
    my_user = await UserRepository().update_fields(update_data=update_data, update_filter=update_filter)
    all_users = await UserRepository().get_all_by_fields(data=["points"], order_filter="points")
    position_in_top = 1
    for index, user in enumerate(all_users):
        if user.points == points:
            position_in_top = index + 1
    await message.answer_photo(photo=file, caption=f"<b>Вы достигли {levels_arr.index(status) + 1} уровня -"
                                                   f" {status}</b>\n"
                                                   f"Вы заняли <b>{position_in_top} место из {len(all_users)}</b> "
                                                   f"в общем топе учеников 🏆",
                               reply_markup=start_profile_kb(),
                               parse_mode=ParseMode.HTML)


async def print_statistic(message: types.Message, percent, all_user_tasks, all_tasks, percent_ready, addition=""):
    text = f"{addition}{TEXT_COMMON_STATISTIC_1} <b>{str(percent)} %</b>\n" \
           f"{TEXT_COMMON_STATISTIC_2}: <b>{all_user_tasks} из {all_tasks}</b>\n" \
           f"{TEXT_COMMON_STATISTIC_3}: <b>{str(percent_ready)} %</b>"
    await message.answer(text, parse_mode=ParseMode.HTML)


def closest_number(dictionary: dict, target) -> str:
    closest = 0
    for key, value in dictionary.items():
        if abs(key - target) < abs(closest - target):
            closest = key
    return dictionary.get(closest)
