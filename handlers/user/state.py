from aiogram.fsm.state import StatesGroup, State

from keyboards.user.reply_user import *


class UserState(StatesGroup):
    start = State()

    texts = {
        'UserState:start': [GREETING, start_user_kb],
        'UserState:main_chapter': [TEXT_MAIN_CHAPTER, main_chapter_kb],
        'UserState:chapter': [TEXT_CHAPTER, start_user_kb],
        'UserState:under_chapter': [TEXT_UNDER_CHAPTER, start_user_kb],
        'UserState:answer_mode': [TEXT_ANSWER_MODE, answer_mode_kb],
        'UserState:answer_prepare': [TEXT_INTRODUCE_TEST, ready_test_kb],
        'UserState:answers_checker': [TEXT_START_TEST, ReplyKeyboardRemove()],

    }

