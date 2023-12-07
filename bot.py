import os
import sqlite3
import telebot

from aiogram import Dispatcher, types
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from db import DatabaseManager
from states import EditMessageForm, DeleteMessageForm

bot = telebot.TeleBot(os.getenv("BOT_TOKEN"))
dp = Dispatcher(bot, storage=MemoryStorage())

db_manager = DatabaseManager('users.db')
db_manager.init_db()


@dp.message_handler(commands=['add'])
async def add_user(message: types.Message):
    response = db_manager.add_user(message.from_user.username, message.from_user.full_name)
    await message.reply(response)


@dp.message_handler(commands=['delete'])
async def delete_user(message: types.Message):
    response = db_manager.delete_user(message.from_user.username)
    await message.reply(response)


@dp.message_handler(commands=['view'])
async def view_users(message: types.Message):
    users = db_manager.get_all_users()
    users_list = '\n'.join([f'{user[1]}: {user[2]}' for user in users]) if users else "Пользователей нет"
    await message.reply(users_list)


@dp.message_handler(commands=['add_message'])
async def add_message(message: types.Message):
    cnt_del_symbol = len('/add_message ')
    content = message.text[cnt_del_symbol:]  # Удаление '/add_message ' из текста сообщения
    if not content:
        await message.reply("Введите текст заметки после команды")
        return

    # Разделение на заголовок и содержимое
    parts = content.split('\n', 1)
    title = parts[0]
    content = parts[1] if len(parts) > 1 else ''

    db_manager.add_message(message.from_user.id, title, content)
    await message.reply("Заметка с заголовком сохранена")


@dp.message_handler(commands=['view_messages'])
async def view_messages(message: types.Message):
    messages = db_manager.get_messages(message.from_user.id)
    if messages:
        messages_list = '\n'.join([f'Заголовок: {msg[0]}\n Заметка: {msg[1]}\n' for msg in messages])
        await message.reply(messages_list)
    else:
        await message.reply("У вас нет сохраненных заметок")


@dp.message_handler(commands=['view_titles'])
async def view_titles(message: types.Message):
    titles = db_manager.get_titles(message.from_user.id)

    if titles:
        keyboard = InlineKeyboardMarkup()
        for msg_id, title in titles:
            keyboard.add(InlineKeyboardButton(text=title, callback_data=f"view_{msg_id}"))
        await message.reply("Выберите заметку для просмотра:", reply_markup=keyboard)
    else:
        await message.reply("У вас нет сохраненных заметок")


@dp.callback_query_handler(lambda c: c.data.startswith('view_'))
async def process_callback_button(callback_query: types.CallbackQuery):
    message_id = int(callback_query.data.split('_')[1])
    with sqlite3.connect('users.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT title, content FROM messages WHERE id = ?", (message_id,))
        message_data = cur.fetchone()

    if message_data:
        await bot.send_message(callback_query.from_user.id,
                               f"Заголовок: {message_data[0]}\n Заметка: {message_data[1]}")
    else:
        await bot.send_message(callback_query.from_user.id, "Заметка не найдена")


@dp.message_handler(commands=['edit_title'])
async def edit_title(message: types.Message):
    titles = db_manager.get_titles(message.from_user.id)

    if titles:
        keyboard = InlineKeyboardMarkup()
        for msg_id, title in titles:
            keyboard.add(InlineKeyboardButton(text=title, callback_data=f"edit_{msg_id}"))
        await message.reply("Выберите заметку для редактирования:", reply_markup=keyboard)
    else:
        await message.reply("У вас нет сохраненных сообщений")


@dp.callback_query_handler(lambda c: c.data.startswith('edit_'))
async def process_edit_button(callback_query: types.CallbackQuery):
    message_id = int(callback_query.data.split('_')[1])
    with sqlite3.connect('users.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT title FROM messages WHERE id = ?", (message_id,))
        title = cur.fetchone()

    if title:
        await EditMessageForm.content.set()
        state = dp.current_state(chat=callback_query.message.chat.id, user=callback_query.from_user.id)
        await state.update_data(message_id=message_id)
        await bot.send_message(callback_query.from_user.id, f"Введите новое содержимое для заметки '{title[0]}':")
    else:
        await bot.send_message(callback_query.from_user.id, "Заметка не найдена")


@dp.message_handler(state=EditMessageForm.content)
async def process_new_content(message: types.Message, state: FSMContext):
    data = await state.get_data()
    message_id = data['message_id']
    new_content = message.text

    with sqlite3.connect('users.db') as conn:
        cur = conn.cursor()
        cur.execute("UPDATE messages SET content = ? WHERE id = ?", (new_content, message_id))
        conn.commit()

    await message.reply("Содержимое заметки обновлено")
    await state.finish()


@dp.message_handler(commands=['delete_message'])
async def delete_message(message: types.Message):
    titles = db_manager.get_titles(message.from_user.id)

    if titles:
        keyboard = InlineKeyboardMarkup()
        for msg_id, title in titles:
            keyboard.add(InlineKeyboardButton(text=title, callback_data=f"delete_{msg_id}"))
        await message.reply("Выберите заметку для удаления:", reply_markup=keyboard)
    else:
        await message.reply("У вас нет сохраненных заметок")


@dp.callback_query_handler(lambda c: c.data.startswith('delete_'))
async def process_delete_button(callback_query: types.CallbackQuery):
    message_id = int(callback_query.data.split('_')[1])
    with sqlite3.connect('users.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT title FROM messages WHERE id = ?", (message_id,))
        title = cur.fetchone()

    if title:
        await DeleteMessageForm.confirm.set()
        state = dp.current_state(chat=callback_query.message.chat.id, user=callback_query.from_user.id)
        await state.update_data(message_id=message_id)
        with sqlite3.connect('users.db') as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM messages WHERE id = ?", (message_id,))
            conn.commit()
        await bot.send_message(callback_query.from_user.id, "Заметка удалена")
    else:
        await bot.send_message(callback_query.from_user.id, "Заметка не найдена")
    await state.finish()


@dp.message_handler(commands=['help'])
async def start(message: types.Message):
    await message.reply(
        "Привет! Используйте команды:\n/add - Добавить пользователя\n/delete - Удалить пользователя\n/view - Просмотреть пользователей\n/add_message - Добавить заметку с заголовком. Для ввода сообщения напишите заголовок, затем на следующей строчке заметку. Все нужно писать в одном сообщении с командой \n/view_messages - Просмотреть сообщения\n /view_titles - посмотреть заметку по его заголовку\n /edit_title - редактировать заметку по его заголовку \n /delete_message - удалить заметку")


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("Привет! Бот запущен, введи команду\n /help")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
