from aiogram.fsm.state import StatesGroup, State


class Form(StatesGroup):
    username = State()
    answer = State()
    button_enter = State()
