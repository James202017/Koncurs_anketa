import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

class Form(StatesGroup):
    name = State()
    phone = State()
    residence = State()
    satisfaction = State()
    property_type = State()
    location = State()
    budget = State()
    search_status = State()
    mortgage = State()
    purchase_time = State()
    contact_method = State()
    contact_time = State()
    confirm = State()

def get_inline_keyboard(options, row_width=2):
    kb = InlineKeyboardBuilder()
    for opt in options:
        kb.button(text=opt, callback_data=opt)
    kb.adjust(row_width)
    return kb.as_markup()

def get_reply_keyboard(options, row_width=2, one_time=False, resize=True):
    kb = ReplyKeyboardBuilder()
    for opt in options:
        kb.button(text=opt)
    kb.adjust(row_width)
    return kb.as_markup(resize_keyboard=resize, one_time_keyboard=one_time)

# Функция для форматирования сообщения с данными заявки
def format_application_message(data, user_id, is_sos=False):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if is_sos:
        message = f"🆘 <b>SOS запрос!</b>\n\n"
        message += f"От: {data.get('name', 'Не указано')}\n"
        message += f"📱 Телефон: {data.get('phone', 'Не указано')}\n"
        message += f"🆔 ID пользователя: {user_id}\n"
        message += f"⏰ Время запроса: {current_time}"
    else:
        message = f"🔔 <b>Новая заявка!</b>\n\n"
        message += f"👤 Имя: {data.get('name', 'Не указано')}\n"
        message += f"📱 Телефон: {data.get('phone', 'Не указано')}\n\n"
        
        message += f"<b>Блок 1. Жилищная ситуация</b>\n"
        message += f"🏠 Текущее жилье: {data.get('residence', 'Не указано')}\n"
        message += f"😊 Довольны условиями: {data.get('satisfaction', 'Не указано')}\n"
        message += f"🏢 Тип недвижимости: {data.get('property_type', 'Не указано')}\n"
        message += f"📍 Желаемое расположение: {data.get('location', 'Не указано')}\n"
        message += f"💰 Бюджет: {data.get('budget', 'Не указано')}\n"
        message += f"🔍 Статус поиска: {data.get('search_status', 'Не указано')}\n\n"
        
        message += f"<b>Блок 2. Готовность к покупке</b>\n"
        message += f"🏦 Ипотека: {data.get('mortgage', 'Не указано')}\n"
        message += f"⏱ Планируемое время покупки: {data.get('purchase_time', 'Не указано')}\n\n"
        
        message += f"<b>Блок 3. Контактные данные</b>\n"
        message += f"📞 Предпочтительный способ связи: {data.get('contact_method', 'Не указано')}\n"
        message += f"📅 Удобное время для связи: {data.get('contact_time', 'Не указано')}\n\n"
        
        message += f"🆔 ID пользователя: {user_id}\n"
        message += f"⏰ Время заявки: {current_time}"
    
    return message

@dp.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await message.answer(
        "👋 Привет! Я помогу тебе узнать, как улучшить свои жилищные условия. Как тебя зовут?",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Form.name)

@dp.message(Form.name)
async def get_name(message: Message, state: FSMContext):
    if len(message.text) < 2:
        await message.answer("Пожалуйста, введите корректное имя (минимум 2 символа)")
        return
        
    await state.update_data(name=message.text)
    
    await message.answer(
        "🏠 Где вы сейчас живёте?", 
        reply_markup=get_inline_keyboard([
            "В своей квартире", 
            "Снимаю квартиру", 
            "Живу с родителями", 
            "Живу с парнем/девушкой", 
            "В общежитии", 
            "Другое"
        ], row_width=2)
    )
    await state.set_state(Form.residence)

@dp.message(Form.phone)
async def get_phone(message: Message, state: FSMContext):
    # Проверка на кнопку "Отправить мой номер телефона"
    if message.text == "Отправить мой номер телефона":
        # Проверяем, есть ли у пользователя номер телефона в профиле
        if message.from_user.id and hasattr(message.from_user, 'contact') and message.from_user.contact and message.from_user.contact.phone_number:
            phone = message.from_user.contact.phone_number
        else:
            # Если номера нет в профиле, просим отправить контакт
            keyboard = ReplyKeyboardBuilder()
            keyboard.add(KeyboardButton(text="Отправить контакт", request_contact=True))
            await message.answer(
                "Для отправки номера телефона, пожалуйста, нажмите кнопку ниже или введите номер вручную в формате +7XXXXXXXXXX",
                reply_markup=keyboard.as_markup(resize_keyboard=True)
            )
            return
    # Проверка на отправку контакта
    elif message.contact and message.contact.phone_number:
        phone = message.contact.phone_number
    # Ручной ввод номера
    else:
        phone = message.text
        if not re.match(r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$', phone):
            keyboard = ReplyKeyboardBuilder()
            keyboard.add(KeyboardButton(text="Отправить контакт", request_contact=True))
            await message.answer(
                "Пожалуйста, введите корректный номер телефона в формате +7XXXXXXXXXX или нажмите кнопку для отправки контакта",
                reply_markup=keyboard.as_markup(resize_keyboard=True)
            )
            return
    
    # Сохраняем телефон и переходим к следующему шагу
    await state.update_data(phone=phone)
    await message.answer(
        "Когда и как вам лучше всего связаться?",
        reply_markup=get_inline_keyboard([
            "По телефону",
            "Написать в Telegram",
            "Написать в WhatsApp",
            "E-mail",
            "Другое"
        ], row_width=2)
    )
    await state.set_state(Form.contact_method)

@dp.callback_query(Form.residence)
async def get_residence(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(residence=call.data)
    
    # Если выбрано "Другое", предлагаем ввести свой вариант
    if call.data == "Другое":
        await call.message.answer(
            "Пожалуйста, опишите ваши текущие жилищные условия:",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    # Переходим к вопросу о удовлетворенности
    await call.message.answer(
        "Вы довольны текущими условиями проживания?", 
        reply_markup=get_inline_keyboard([
            "Да, всё устраивает", 
            "Нет, хочу улучшить", 
            "Затрудняюсь ответить"
        ], row_width=1)
    )
    await state.set_state(Form.satisfaction)

@dp.message(Form.residence)
async def get_residence_text(message: Message, state: FSMContext):
    # Сохраняем введенный пользователем текст
    await state.update_data(residence=message.text)
    
    # Переходим к вопросу о удовлетворенности
    await message.answer(
        "Вы довольны текущими условиями проживания?", 
        reply_markup=get_inline_keyboard([
            "Да, всё устраивает", 
            "Нет, хочу улучшить", 
            "Затрудняюсь ответить"
        ], row_width=1)
    )
    await state.set_state(Form.satisfaction)

@dp.callback_query(Form.satisfaction)
async def get_satisfaction(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(satisfaction=call.data)
    await call.message.answer(
        "Какой тип недвижимости вы хотели бы приобрести?", 
        reply_markup=get_inline_keyboard([
            "Квартира в новостройке", 
            "Вторичка", 
            "Дом", 
            "Таунхаус", 
            "Участок под строительство", 
            "Пока не решил(а)"
        ], row_width=2)
    )
    await state.set_state(Form.property_type)

@dp.callback_query(Form.budget)
async def get_budget(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(budget=call.data)
    await call.message.answer(
        "Вы уже подбирали варианты?", 
        reply_markup=get_inline_keyboard([
            "Да, активно ищу",
            "Смотрю, но пока без спешки",
            "Нет, только начал(а) интересоваться",
            "Нет, но хочу узнать, как начать"
        ], row_width=1)
    )
    await state.set_state(Form.search_status)

@dp.callback_query(Form.property_type)
async def get_property_type(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(property_type=call.data)
    
    await call.message.answer(
        "Где бы вы хотели приобрести недвижимость?",
        reply_markup=get_inline_keyboard([
            "В текущем городе",
            "В другом городе",
            "За городом",
            "Пока не знаю"
        ], row_width=2)
    )
    await state.set_state(Form.location)

@dp.callback_query(Form.location)
async def get_location(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    
    # Если выбран другой город, просим указать какой
    if call.data == "В другом городе":
        await call.message.answer(
            "Пожалуйста, укажите город:",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    await state.update_data(location=call.data)
    await call.message.answer(
        "Какой у вас примерный бюджет?",
        reply_markup=get_inline_keyboard([
            "До 2 млн ₽",
            "2–5 млн ₽",
            "5–10 млн ₽",
            "10+ млн ₽",
            "Затрудняюсь ответить"
        ], row_width=2)
    )
    await state.set_state(Form.budget)

@dp.message(Form.location)
async def get_location_text(message: Message, state: FSMContext):
    # Сохраняем введенный город
    await state.update_data(location=f"В другом городе: {message.text}")
    
    await message.answer(
        "Какой у вас примерный бюджет?",
        reply_markup=get_inline_keyboard([
            "До 2 млн ₽",
            "2–5 млн ₽",
            "5–10 млн ₽",
            "10+ млн ₽",
            "Затрудняюсь ответить"
        ], row_width=2)
    )
    await state.set_state(Form.budget)

@dp.callback_query(Form.search_status)
async def get_search_status(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(search_status=call.data)
    
    # Информационное сообщение о возможностях покупки
    info_message = "Знаете ли вы, что можно купить недвижимость:\n"
    info_message += "✅ с господдержкой\n"
    info_message += "✅ с субсидированной ставкой\n"
    info_message += "✅ в рассрочку\n"
    info_message += "✅ без первоначального взноса\n\n"
    info_message += "Мы расскажем вам подробнее об этих возможностях!"
    
    await call.message.answer(info_message)
    
    # Переходим к вопросу об ипотеке
    await call.message.answer(
        "Рассматриваете ли вы ипотеку?",
        reply_markup=get_inline_keyboard(["Да", "Нет", "Возможно"], row_width=3)
    )
    await state.set_state(Form.mortgage)

@dp.callback_query(Form.mortgage)
async def get_mortgage(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(mortgage=call.data)
    
    await call.message.answer(
        "Когда вы планируете покупку?",
        reply_markup=get_inline_keyboard([
            "В ближайший месяц",
            "Через 3–6 месяцев",
            "В течение года",
            "Пока не знаю"
        ], row_width=2)
    )
    await state.set_state(Form.purchase_time)

@dp.callback_query(Form.purchase_time)
async def get_purchase_time(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(purchase_time=call.data)
    
    # Информационное сообщение о возможностях покупки
    info_message = "ℹ️ <b>Знаете ли вы, что можно купить недвижимость:</b>\n\n"
    info_message += "✅ с господдержкой\n"
    info_message += "✅ с субсидированной ставкой\n"
    info_message += "✅ в рассрочку\n"
    info_message += "✅ без первоначального взноса\n\n"
    info_message += "Мы расскажем вам подробнее об этих возможностях после заполнения анкеты."
    
    await call.message.answer(info_message)
    
    # Переходим к вопросу об имени
    await call.message.answer(
        "Как вас зовут? (имя и фамилия)",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Form.name)

@dp.callback_query(Form.contact_method)
async def get_contact_method(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await state.update_data(contact_method=call.data)
    
    # Если выбрано "Другое", просим указать свой вариант
    if call.data == "Другое":
        await call.message.answer(
            "Пожалуйста, укажите предпочтительный способ связи:",
            reply_markup=ReplyKeyboardRemove()
        )
        return
    
    await call.message.answer(
        "Укажите удобный день и время для связи:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Form.contact_time)

@dp.message(Form.contact_method)
async def get_contact_method_text(message: Message, state: FSMContext):
    # Сохраняем введенный пользователем способ связи
    await state.update_data(contact_method=message.text)
    
    await message.answer(
        "Укажите удобный день и время для связи:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Form.contact_time)

@dp.message(Form.contact_time)
async def get_contact_time(message: Message, state: FSMContext):
    await state.update_data(contact_time=message.text)
    
    # Создаем клавиатуру с кнопкой для отправки контакта
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text="Отправить контакт", request_contact=True))
    keyboard.add(KeyboardButton(text="Отправить мой номер телефона"))
    
    await message.answer(
        "📱 Укажите ваш номер телефона для связи",
        reply_markup=keyboard.as_markup(resize_keyboard=True)
    )
    await state.set_state(Form.phone)

@dp.message(Form.phone)
async def get_phone(message: Message, state: FSMContext):
    # Проверяем, был ли отправлен контакт
    if message.contact is not None:
        phone = message.contact.phone_number
        await process_phone(message, state, phone)
    elif message.text and re.match(r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$', message.text):
        # Если пользователь ввел номер вручную и он соответствует формату
        phone = message.text
        await process_phone(message, state, phone)
    else:
        # Если формат неверный или это не контакт
        await message.answer(
            "Пожалуйста, отправьте ваш номер телефона, нажав на кнопку 'Отправить контакт' или введите его вручную в формате +7XXXXXXXXXX",
            reply_markup=get_contact_keyboard()
        )

async def process_phone(message: Message, state: FSMContext, phone: str):
    # Удаляем все нецифровые символы
    phone = re.sub(r'\D', '', phone)
    
    # Приводим к формату с 7 в начале
    if phone.startswith('8'):
        phone = '7' + phone[1:]
    
    # Сохраняем телефон
    await state.update_data(phone=phone)
    
    # Получаем все данные формы
    data = await state.get_data()
    
    # Формируем сообщение для подтверждения
    confirm_message = f"📋 <b>Проверьте введенные данные:</b>\n\n"
    
    # Блок 1. Жилищная ситуация
    confirm_message += f"<b>Блок 1. Жилищная ситуация</b>\n"
    confirm_message += f"👤 Имя: {data['name']}\n"
    confirm_message += f"🏠 Текущее жилье: {data.get('residence', 'Не указано')}\n"
    confirm_message += f"😊 Довольны условиями: {data.get('satisfaction', 'Не указано')}\n"
    confirm_message += f"🏢 Тип недвижимости: {data.get('property_type', 'Не указано')}\n"
    confirm_message += f"📍 Желаемое расположение: {data.get('location', 'Не указано')}\n"
    confirm_message += f"💰 Бюджет: {data.get('budget', 'Не указано')}\n"
    confirm_message += f"🔍 Статус поиска: {data.get('search_status', 'Не указано')}\n\n"
    
    # Блок 2. Готовность к покупке
    confirm_message += f"<b>Блок 2. Готовность к покупке</b>\n"
    confirm_message += f"🏦 Ипотека: {data.get('mortgage', 'Не указано')}\n"
    confirm_message += f"⏱ Планируемое время покупки: {data.get('purchase_time', 'Не указано')}\n\n"
    
    # Блок 3. Контактные данные
    confirm_message += f"<b>Блок 3. Контактные данные</b>\n"
    confirm_message += f"📞 Предпочтительный способ связи: {data.get('contact_method', 'Не указано')}\n"
    confirm_message += f"📅 Удобное время для связи: {data.get('contact_time', 'Не указано')}\n"
    confirm_message += f"📱 Телефон: +{phone}\n\n"
    
    confirm_message += "Всё верно?"
    
    # Отправляем сообщение с подтверждением
    await message.answer(
        confirm_message,
        reply_markup=get_inline_keyboard(["✅ Подтвердить", "❌ Изменить"], row_width=2)
    )
    
    # Устанавливаем состояние подтверждения
     await state.set_state(Form.confirm)
    confirm_message += f"🏢 Тип недвижимости: {data.get('property_type', 'Не указано')}\n"
    confirm_message += f"📍 Желаемое расположение: {data.get('location', 'Не указано')}\n"
    confirm_message += f"💰 Бюджет: {data.get('budget', 'Не указано')}\n"
    confirm_message += f"🔍 Статус поиска: {data.get('search_status', 'Не указано')}\n\n"
    
    # Блок 2. Готовность к покупке
    confirm_message += f"<b>Блок 2. Готовность к покупке</b>\n"
    confirm_message += f"🏦 Ипотека: {data.get('mortgage', 'Не указано')}\n"
    confirm_message += f"⏱ Планируемое время покупки: {data.get('purchase_time', 'Не указано')}\n\n"
    
    # Блок 3. Контактные данные
    confirm_message += f"<b>Блок 3. Контактные данные</b>\n"
    confirm_message += f"📞 Предпочтительный способ связи: {data.get('contact_method', 'Не указано')}\n"
    confirm_message += f"📅 Удобное время для связи: {data.get('contact_time', 'Не указано')}\n"
    confirm_message += f"📱 Телефон: {phone}\n\n"
    
    confirm_message += "Всё верно?"
    
    await message.answer(
        confirm_message,
        reply_markup=get_inline_keyboard(["✅ Подтвердить", "❌ Изменить"], row_width=2)
    )
    await state.set_state(Form.confirm)

@dp.callback_query(Form.confirm)
async def confirm_data(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    
    if call.data == "✅ Подтвердить":
        data = await state.get_data()
        
        try:
            # Формируем сообщение для администратора
            admin_message = format_application_message(data, call.from_user.id)
            
            # Отправляем сообщение администраторам
            sent_successfully = False
            for admin in ADMIN_IDS:
                try:
                    await bot.send_message(admin, admin_message)
                    sent_successfully = True
                except Exception as e:
                    logging.error(f"Ошибка при отправке сообщения администратору {admin}: {e}")
            
            if sent_successfully:
                await call.message.answer(
                    "✅ Спасибо! Твоя заявка принята.\n\n" +
                    "Наш специалист свяжется с тобой в указанное время.\n\n" +
                    "Если у тебя возникли срочные вопросы, нажми /sos, и мы свяжемся с тобой как можно скорее.",
                    reply_markup=get_reply_keyboard(["📋 Новая заявка", "❓ Помощь"], row_width=2)
                )
            else:
                # Если не удалось отправить ни одному администратору
                await call.message.answer(
                    "❌ Произошла ошибка при отправке заявки. Пожалуйста, попробуйте позже или свяжитесь с администратором.",
                    reply_markup=get_reply_keyboard(["📋 Новая заявка", "❓ Помощь"], row_width=2)
                )
        except Exception as e:
            logging.error(f"Ошибка при обработке заявки: {e}")
            await call.message.answer(
                "❌ Произошла ошибка при обработке заявки. Пожалуйста, попробуйте позже или свяжитесь с администратором.",
                reply_markup=get_reply_keyboard(["📋 Новая заявка", "❓ Помощь"], row_width=2)
            )
    else:  # Пользователь выбрал "Изменить"
        await call.message.answer(
            "🔄 Давай начнем заново. Как тебя зовут?",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(Form.name)
    
    if call.data == "✅ Подтвердить":
        await state.clear()

@dp.message(F.text == "/sos")
async def sos(message: Message, state: FSMContext):
    # Получаем данные пользователя, если они есть
    data = await state.get_data()
    user_info = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
    user_name = f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip()
    
    # Добавляем имя и телефон в данные, если их нет
    if 'name' not in data:
        data['name'] = user_name
    if 'phone' not in data:
        data['phone'] = "Не указан"
    
    # Уведомляем пользователя
    await message.answer(
        "🆘 Запрос отправлен! Наш специалист свяжется с тобой в ближайшее время.",
        reply_markup=get_reply_keyboard(["📋 Новая заявка", "❓ Помощь"], row_width=2)
    )
    
    # Формируем и отправляем SOS-сообщение администраторам
    sos_message = format_application_message(data, message.from_user.id, is_sos=True)
    
    sent_successfully = False
    for admin in ADMIN_IDS:
        try:
            await bot.send_message(admin, sos_message)
            sent_successfully = True
        except Exception as e:
            logging.error(f"Ошибка при отправке SOS администратору {admin}: {e}")

@dp.message(F.text == "📋 Новая заявка")
async def new_request(message: Message, state: FSMContext):
    await start(message, state)

@dp.message(F.text == "❓ Помощь")
async def help_command(message: Message):
    await message.answer(
        "ℹ️ <b>Помощь по использованию бота:</b>\n\n" +
        "• /start - Начать новую заявку на подбор недвижимости\n" +
        "• /sos - Срочная связь со специалистом\n" +
        "• /help - Показать это сообщение\n\n" +
        "Если у вас возникли вопросы или проблемы, нажмите /sos, и наш специалист свяжется с вами в ближайшее время.",
        reply_markup=get_reply_keyboard(["📋 Новая заявка"], row_width=1)
    )

@dp.message(F.text == "/help")
async def help_command_alt(message: Message):
    await help_command(message)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())