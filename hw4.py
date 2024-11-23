import logging
import asyncio
import sqlite3

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import BotCommand

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from aiogram import Router
from config import token

router=Router()


bot = Bot(token=token)
dp = Dispatcher()


command = [BotCommand(command='start', description='Начать')]


buttons = [
     [KeyboardButton(text='Добавить задачу'), KeyboardButton(text='Показать задачи')],
     [KeyboardButton(text='Очистить список')]
]

keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True,  input_field_placeholder='Выберите кнопку')


inline_button = [
     [InlineKeyboardButton(text="Подтвердить", callback_data="confirm_clear")],
     [InlineKeyboardButton(text="Отменить", callback_data="cancel_clear")]
]

inline_keyboard = InlineKeyboardMarkup(inline_keyboard=inline_button)

connect= sqlite3.connect("to_do_list.db")
cursor = connect.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
telegram_user INTEGER UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks(
id INTEGER PRIMARY KEY AUTOINCREMENT,
task TEXT
)
""")
connect.commit()

def register_user(telegram_user):
        cursor.execute("INSERt INTO users (telegram_user) VALUES (?)", (telegram_user,))
        connect.commit()

def add_task(telegram_user, task):
        cursor.execute("SELECT id FROM users WHERE telegram_user = ?", (telegram_user,))
        user_id = cursor.fetchone()
        if user_id:
            cursor.execute("INSERT INTO tasks (text, user_id) VALUES (?, ?)", (task, user_id[0]))
            connect.commit()

def get_tasks(telegram_user):
        cursor.execute("""
        SELECT * FROM tasks
        """, (telegram_user,))
        return cursor.fetchall()

def delete_all_tasks(telegram_user):
        cursor.execute("""
        DELETE FROM tasks WHERE user_id = (
            SELECT id FROM users WHERE telegram_user = ?
        )
        """, (telegram_user,))
        connect.commit()

def tasks_buttons(tasks):
    markup = InlineKeyboardMarkup()
    for task_id, task_text in tasks:
        markup.add(InlineKeyboardButton(text=task_text[:20], callback_data=f"task_{task_id}"))
    return markup


@router.message(CommandStart())
async def command_start(message: types.Message):
    await message.answer(f'Привет {message.from_user}', reply_markup=keyboard)

@router.message(F.text=='Добавить задачу')
async def add_task(message: types.Message):
    await message.reply('Введите содержание задачи:')

@router.message()
async def save_task(message: types.Message):
        add_task(message.from_user.id, message.text)
        await message.answer("Задача добавлена!", reply_markup=keyboard)

@router.message(F.text=="Показать задачи")
async def show_tasks(message: types.Message):
        tasks = get_tasks(message.from_user.id)
        if tasks:
            await message.answer("Ваши задачи:", reply_markup=tasks_buttons(tasks))
        else:
            await message.answer("Список задач пуст.")


@router.message(F.text=="Очистить список")
async def confirm_clear_list(message: types.Message):
        await message.answer("Вы уверены?", reply_markup=inline_keyboard)

@router.callback_query(F.test=="confirm_clear")
async def clear_tasks(callback: types.CallbackQuery):
        delete_all_tasks(callback.from_user.id)
        await callback.message.answer("Список задач очищен.", reply_markup=keyboard)

@router.callback_query(F.text=="cancel_clear")
async def cancel_clear(callback: types.CallbackQuery):
        await callback.message.answer("Очистка отменена.", reply_markup=keyboard)


async def main():
    logging.basicConfig(level=logging.INFO)
    dp.include_routers(router)
    await dp.start_polling(bot)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("Выход")