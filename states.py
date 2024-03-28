from aiogram.dispatcher.filters.state import StatesGroup, State

class EditMessageForm(StatesGroup):
    content = State()

class DeleteMessageForm(StatesGroup):
    confirm = State()