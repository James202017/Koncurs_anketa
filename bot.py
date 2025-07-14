import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
import os
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))
SHEET_ID = os.getenv("GOOGLE_SHEET_ID")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

class Form(StatesGroup):
    name = State()
    phone = State()
    residence = State()
    goal = State()
    time = State()

def get_keyboard(options):
    kb = InlineKeyboardBuilder()
    for opt in options:
        kb.button(text=opt, callback_data=opt)
    return kb.as_markup()

def get_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client = gspread.authorize(creds)
    return client.open_by_key(SHEET_ID).sheet1

@dp.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await message.answer("Привет! Давай подберем тебе недвижимость. Как тебя зовут?")
    await state.set_state(Form.name)

@dp.message(Form.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Оставь свой номер телефона 📞")
    await state.set_state(Form.phone)

@dp.message(Form.phone)
async def get_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer(
        "Где ты сейчас живёшь?", 
        reply_markup=get_keyboard(["Съёмная", "Своя", "У родителей", "У партнёра", "Другое"])
    )
    await state.set_state(Form.residence)

@dp.callback_query(Form.residence)
async def get_residence(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(residence=call.data)
    await call.message.answer(
        "Хотел(а) бы улучшить свои жилищные условия?", 
        reply_markup=get_keyboard(["Да", "Нет", "Пока не думал(а)"])
    )
    await state.set_state(Form.goal)

@dp.callback_query(Form.goal)
async def get_goal(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(goal=call.data)
    await call.message.answer("Укажи день и время, когда тебе удобно поговорить с нашим специалистом.")
    await state.set_state(Form.time)

@dp.message(Form.time)
async def get_time(message: Message, state: FSMContext):
    await state.update_data(time=message.text)
    data = await state.get_data()

    sheet = get_gsheet()
    sheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        message.from_user.id,
        data['name'],
        data['phone'],
        data['residence'],
        data['goal'],
        data['time']
    ])

    await message.answer("Спасибо! Если не терпится — жми /sos и мы свяжемся с тобой сразу.")
    await state.clear()

@dp.message(F.text == "/sos")
async def sos(message: Message):
    for admin in ADMIN_IDS:
        await bot.send_message(admin, f"SOS от @{message.from_user.username} ({message.from_user.id})")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())