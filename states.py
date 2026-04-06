from aiogram.fsm.state import StatesGroup, State

class Spam(StatesGroup):
    waiting_for_message = State()

class AddTheme(StatesGroup):
    waiting_for_title = State()

class AddShop(StatesGroup):
    waiting_for_title = State()
class EditShop(StatesGroup):
    waiting_for_new_title = State()
    waiting_for_photo = State()
    waiting_for_description = State()