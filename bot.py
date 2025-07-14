import logging
import re
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardRemove, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv("BOT_TOKEN"), default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# Определение состояний формы
class Form(StatesGroup):
    start = State()            # Начальное состояние
    residence = State()        # Текущее жилье
    satisfaction = State()     # Довольны ли текущими условиями
    property_type = State()    # Тип недвижимости
    location = State()         # Желаемое расположение
    budget = State()           # Бюджет
    search_status = State()    # Статус поиска
    mortgage = State()         # Ипотека
    purchase_time = State()    # Планируемое время покупки
    name = State()             # Имя
    contact_method = State()   # Способ связи
    contact_method_text = State()  # Текстовый ввод способа связи
    contact_time = State()     # Удобное время для связи
    phone = State()            # Телефон
    confirm = State()          # Подтверждение данных

# Словарь для навигации назад (текущее состояние -> предыдущее состояние)
PREVIOUS_STATES = {
    Form.satisfaction: Form.residence,
    Form.property_type: Form.satisfaction,
    Form.location: Form.property_type,
    Form.budget: Form.location,
    Form.search_status: Form.budget,
    Form.mortgage: Form.search_status,
    Form.purchase_time: Form.mortgage,
    Form.name: Form.purchase_time,
    Form.contact_method: Form.name,
    Form.contact_method_text: Form.name,
    Form.contact_time: Form.contact_method,
    Form.phone: Form.contact_time,
}

# Функция для создания инлайн-клавиатуры
def get_inline_keyboard(buttons, row_width=1, add_back_button=False):
    builder = InlineKeyboardBuilder()
    for button in buttons:
        builder.button(text=button, callback_data=button)
    
    # Добавляем кнопку "Назад" если требуется
    if add_back_button:
        builder.button(text="⬅️ Назад", callback_data="⬅️ Назад")
    
    builder.adjust(row_width)
    return builder.as_markup()

# Функция для создания клавиатуры только с кнопкой "Назад"
def get_back_keyboard():
    keyboard = [[KeyboardButton(text="⬅️ Назад")]]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

# Функция для создания обычной клавиатуры
def get_reply_keyboard(buttons, row_width=1, one_time_keyboard=True, resize_keyboard=True, add_back_button=True):
    keyboard = []
    row = []
    for i, button in enumerate(buttons):
        row.append(KeyboardButton(text=button))
        if (i + 1) % row_width == 0 or i == len(buttons) - 1:
            keyboard.append(row)
            row = []
    
    # Добавляем кнопку "Назад" в последний ряд, если требуется
    if add_back_button:
        back_button = KeyboardButton(text="⬅️ Назад")
        if keyboard and len(keyboard[-1]) < row_width:
            keyboard[-1].append(back_button)
        else:
            keyboard.append([back_button])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, one_time_keyboard=one_time_keyboard, resize_keyboard=resize_keyboard)

# Функция для создания клавиатуры с кнопкой отправки контакта
def get_contact_keyboard():
    keyboard = [
        [KeyboardButton(text="Отправить контакт", request_contact=True)],
        [KeyboardButton(text="Отправить мой номер телефона")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, one_time_keyboard=True, resize_keyboard=True)

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Здравствуйте! Я бот для подбора недвижимости. Я помогу вам найти идеальное жилье, соответствующее вашим потребностям и бюджету.\n\n"
        "Для начала, давайте узнаем немного о вашей текущей жилищной ситуации.\n\n"
        "Где вы сейчас проживаете?",
        reply_markup=get_reply_keyboard([
            "Собственная квартира",
            "Собственный дом",
            "Аренда",
            "С родителями/родственниками",
            "Другое"
        ], row_width=1, add_back_button=False)
    )
    await state.set_state(Form.residence)

# Обработчик команды /help
@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Я бот для подбора недвижимости. Вот что я могу:\n\n"
        "1. Помочь вам определиться с типом недвижимости\n"
        "2. Подобрать варианты по вашему бюджету\n"
        "3. Учесть ваши предпочтения по расположению\n"
        "4. Дать информацию об ипотечных программах\n\n"
        "Чтобы начать заново, отправьте команду /start"
    )

# Обработчик команды /cancel
@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    
    await state.clear()
    await message.answer(
        "Действие отменено. Чтобы начать заново, отправьте команду /start",
        reply_markup=ReplyKeyboardRemove()
    )

# Обработчик для состояния Form.residence
@dp.message(Form.residence)
async def get_residence(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        # Обработка кнопки "Назад" уже реализована в отдельном обработчике
        return
    
    if message.text == "Другое":
        await message.answer(
            "Пожалуйста, опишите вашу текущую жилищную ситуацию:",
            reply_markup=get_reply_keyboard([], add_back_button=True, row_width=1)
        )
        # Остаемся в том же состоянии, чтобы получить текстовый ответ
        return
    
    await state.update_data(residence=message.text)
    
    await message.answer(
        "Довольны ли вы своими текущими жилищными условиями?",
        reply_markup=get_reply_keyboard([
            "Да, полностью доволен",
            "Частично доволен",
            "Нет, не доволен"
        ])
    )
    await state.set_state(Form.satisfaction)

# Обработчик для состояния Form.satisfaction
@dp.message(Form.satisfaction)
async def get_satisfaction(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        # Обработка кнопки "Назад" уже реализована в отдельном обработчике
        return
    
    await state.update_data(satisfaction=message.text)
    
    await message.answer(
        "Какой тип недвижимости вас интересует?",
        reply_markup=get_reply_keyboard([
            "Квартира",
            "Дом",
            "Таунхаус",
            "Участок земли",
            "Коммерческая недвижимость"
        ], row_width=2)
    )
    await state.set_state(Form.property_type)

# Обработчик для состояния Form.property_type
@dp.message(Form.property_type)
async def get_property_type(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        # Обработка кнопки "Назад" уже реализована в отдельном обработчике
        return
    
    await state.update_data(property_type=message.text)
    
    await message.answer(
        "В каком районе или городе вы хотели бы приобрести недвижимость?",
        reply_markup=get_reply_keyboard([
            "В центре города",
            "В спальном районе",
            "В пригороде",
            "За городом",
            "Другое (напишите свой вариант)"
        ], row_width=1)
    )
    await state.set_state(Form.location)

# Обработчик для состояния Form.location
@dp.message(Form.location)
async def get_location(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        # Обработка кнопки "Назад" уже реализована в отдельном обработчике
        return
    
    if message.text == "Другое (напишите свой вариант)":
        await message.answer(
            "Пожалуйста, укажите желаемое расположение недвижимости:",
            reply_markup=get_reply_keyboard([], add_back_button=True, row_width=1)
        )
        # Остаемся в том же состоянии, чтобы получить текстовый ответ
        return
    
    await state.update_data(location=message.text)
    
    await message.answer(
        "Какой у вас бюджет на покупку недвижимости?",
        reply_markup=get_reply_keyboard([
            "До 3 млн ₽",
            "3-5 млн ₽",
            "5-10 млн ₽",
            "10-20 млн ₽",
            "Более 20 млн ₽"
        ], row_width=1)
    )
    await state.set_state(Form.budget)

# Обработчик для состояния Form.budget
@dp.message(Form.budget)
async def get_budget(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        # Обработка кнопки "Назад" уже реализована в отдельном обработчике
        return
    
    await state.update_data(budget=message.text)
    
    await message.answer(
        "На каком этапе поиска недвижимости вы находитесь?",
        reply_markup=get_reply_keyboard([
            "Только начинаю искать",
            "Уже смотрел(а) варианты",
            "Определился(лась) с выбором",
            "Готов(а) к сделке"
        ], row_width=1)
    )
    await state.set_state(Form.search_status)

# Обработчик для состояния Form.search_status
@dp.message(Form.search_status)
async def get_search_status(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        # Обработка кнопки "Назад" уже реализована в отдельном обработчике
        return
    
    await state.update_data(search_status=message.text)
    
    await message.answer(
        "Планируете ли вы использовать ипотеку для покупки?",
        reply_markup=get_reply_keyboard([
            "Да, уже одобрена",
            "Да, планирую подать заявку",
            "Нет, полная оплата",
            "Еще не решил(а)"
        ], row_width=1)
    )
    await state.set_state(Form.mortgage)

# Обработчик для состояния Form.mortgage
@dp.message(Form.mortgage)
async def get_mortgage(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        # Обработка кнопки "Назад" уже реализована в отдельном обработчике
        return
    
    await state.update_data(mortgage=message.text)
    
    await message.answer(
        "Когда вы планируете совершить покупку?",
        reply_markup=get_reply_keyboard([
            "В ближайший месяц",
            "В течение 3 месяцев",
            "В течение полугода",
            "В течение года",
            "Пока просто интересуюсь"
        ], row_width=1)
    )
    await state.set_state(Form.purchase_time)

# Обработчик для состояния Form.purchase_time
@dp.message(Form.purchase_time)
async def get_purchase_time(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        # Обработка кнопки "Назад" уже реализована в отдельном обработчике
        return
    
    await state.update_data(purchase_time=message.text)
    
    # Информационное сообщение о возможностях покупки недвижимости
    await message.answer(
        "Спасибо за информацию о ваших планах покупки!\n\n"
        "Сейчас на рынке недвижимости есть много интересных предложений, и мы поможем вам найти оптимальный вариант в соответствии с вашими пожеланиями и бюджетом.\n\n"
        "Теперь давайте соберем ваши контактные данные, чтобы наш специалист мог связаться с вами и предложить подходящие варианты."
    )
    
    # Запрашиваем имя пользователя
    await message.answer(
        "Как вас зовут?",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(Form.name)

# Обработчик для состояния Form.name
@dp.message(Form.name)
async def get_name(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        # Обработка кнопки "Назад" уже реализована в отдельном обработчике
        return
    
    await state.update_data(name=message.text)
    
    # Запрашиваем номер телефона
    await message.answer(
        "Введите ваш номер телефона для связи:",
        reply_markup=get_reply_keyboard([], row_width=1)
    )
    await state.set_state(Form.phone)

# Обработчик для состояния Form.contact_method
@dp.message(Form.contact_method)
async def get_contact_method(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        # Обработка кнопки "Назад" уже реализована в отдельном обработчике
        return
    
    if message.text == "Другое":
        await message.answer(
            "Укажите предпочтительный способ связи:",
            reply_markup=get_reply_keyboard([], add_back_button=True, row_width=1)
        )
        await state.set_state(Form.contact_method_text)
    else:
        await state.update_data(contact_method=message.text)
        
        await message.answer(
            "В какое время вам удобно, чтобы с вами связались?",
            reply_markup=get_reply_keyboard([
                "Утро (9:00-12:00)",
                "День (12:00-18:00)",
                "Вечер (18:00-21:00)",
                "В любое время"
            ], row_width=1)
        )
        await state.set_state(Form.contact_time)

# Обработчик для состояния Form.contact_method_text
@dp.message(Form.contact_method_text)
async def get_contact_method_text(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        # Обработка кнопки "Назад" уже реализована в отдельном обработчике
        return
    
    await state.update_data(contact_method=message.text)
    
    await message.answer(
        "В какое время вам удобно, чтобы с вами связались?",
        reply_markup=get_reply_keyboard([
            "Утро (9:00-12:00)",
            "День (12:00-18:00)",
            "Вечер (18:00-21:00)",
            "В любое время"
        ], row_width=1)
    )
    await state.set_state(Form.contact_time)

# Обработчик для состояния Form.contact_time
@dp.message(Form.contact_time)
async def get_contact_time(message: Message, state: FSMContext):
    await state.update_data(contact_time=message.text)
    
    # Запрашиваем номер телефона
    await message.answer(
        "Пожалуйста, укажите ваш номер телефона для связи.",
        reply_markup=get_contact_keyboard()
    )
    await state.set_state(Form.phone)

# Обработчик для состояния Form.phone
@dp.message(Form.phone)
async def get_phone(message: Message, state: FSMContext):
    if message.text == "⬅️ Назад":
        # Обработка кнопки "Назад" уже реализована в отдельном обработчике
        return
    
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

@dp.callback_query(Form.confirm)
async def confirm_data(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    
    if call.data == "✅ Подтвердить":
        # Получаем все данные формы
        data = await state.get_data()
        
        # Формируем сообщение для администраторов
        admin_message = f"📨 <b>Новая заявка на подбор недвижимости</b>\n\n"
        admin_message += f"<b>Дата и время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        
        # Блок 1. Жилищная ситуация
        admin_message += f"<b>Блок 1. Жилищная ситуация</b>\n"
        admin_message += f"👤 Имя: {data['name']}\n"
        admin_message += f"🏠 Текущее жилье: {data.get('residence', 'Не указано')}\n"
        admin_message += f"😊 Довольны условиями: {data.get('satisfaction', 'Не указано')}\n"
        admin_message += f"🏢 Тип недвижимости: {data.get('property_type', 'Не указано')}\n"
        admin_message += f"📍 Желаемое расположение: {data.get('location', 'Не указано')}\n"
        admin_message += f"💰 Бюджет: {data.get('budget', 'Не указано')}\n"
        admin_message += f"🔍 Статус поиска: {data.get('search_status', 'Не указано')}\n\n"
        
        # Блок 2. Готовность к покупке
        admin_message += f"<b>Блок 2. Готовность к покупке</b>\n"
        admin_message += f"🏦 Ипотека: {data.get('mortgage', 'Не указано')}\n"
        admin_message += f"⏱ Планируемое время покупки: {data.get('purchase_time', 'Не указано')}\n\n"
        
        # Блок 3. Контактные данные
        admin_message += f"<b>Блок 3. Контактные данные</b>\n"
        admin_message += f"📞 Предпочтительный способ связи: {data.get('contact_method', 'Не указано')}\n"
        admin_message += f"📅 Удобное время для связи: {data.get('contact_time', 'Не указано')}\n"
        admin_message += f"📱 Телефон: +{data.get('phone', 'Не указано')}\n"
        admin_message += f"🔗 Telegram: @{call.from_user.username if call.from_user.username else 'Отсутствует'}\n"
        
        # Отправляем сообщение администраторам
        admin_ids = os.getenv("ADMIN_IDS", "").split(",")
        for admin_id in admin_ids:
            if admin_id.strip():
                try:
                    await bot.send_message(chat_id=admin_id.strip(), text=admin_message)
                except Exception as e:
                    logging.error(f"Ошибка при отправке сообщения администратору {admin_id}: {e}")
        
        # Отправляем сообщение пользователю об успешной отправке заявки
        await call.message.answer(
            "✅ Спасибо! Ваша заявка успешно отправлена.\n\n"
            "Наш специалист свяжется с вами в ближайшее время для уточнения деталей и подбора оптимальных вариантов недвижимости.\n\n"
            "Если у вас возникнут дополнительные вопросы, вы можете задать их, отправив новое сообщение.",
            reply_markup=get_inline_keyboard(["🔄 Новая заявка", "❓ Помощь"], row_width=2)
        )
        
        # Очищаем состояние
        await state.clear()
    
    elif call.data == "❌ Изменить":
        # Предлагаем пользователю выбрать, какие данные нужно изменить
        await call.message.answer(
            "Какие данные вы хотели бы изменить?",
            reply_markup=get_inline_keyboard([
                "🏠 Жилищная ситуация", 
                "💰 Готовность к покупке", 
                "📞 Контактные данные",
                "🔄 Начать заново"
            ], row_width=2)
        )
    
    # Обработка кнопки "Назад" реализована в отдельном обработчике

@dp.callback_query(lambda call: call.data in ["🔄 Новая заявка", "🔄 Начать заново"])
async def new_application(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await state.clear()
    
    await call.message.answer(
        "Давайте начнем заново. Где вы сейчас проживаете?",
        reply_markup=get_reply_keyboard([
            "Собственная квартира",
            "Собственный дом",
            "Аренда",
            "С родителями/родственниками",
            "Другое"
        ], row_width=1)
    )
    await state.set_state(Form.residence)

@dp.callback_query(lambda call: call.data in ["🏠 Жилищная ситуация", "💰 Готовность к покупке", "📞 Контактные данные", "⬅️ Назад"])
async def edit_section(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    
    if call.data == "🏠 Жилищная ситуация":
        # Редактирование жилищной ситуации
        await call.message.answer(
            "Где вы сейчас проживаете?",
            reply_markup=get_reply_keyboard([
                "Собственная квартира",
                "Собственный дом",
                "Аренда",
                "С родителями/родственниками",
                "Другое"
            ], row_width=1)
        )
        await state.set_state(Form.residence)
    
    elif call.data == "💰 Готовность к покупке":
        # Редактирование готовности к покупке
        await call.message.answer(
            "Планируете ли вы использовать ипотеку для покупки?",
            reply_markup=get_reply_keyboard([
                "Да, уже одобрена",
                "Да, планирую подать заявку",
                "Нет, полная оплата",
                "Еще не решил(а)"
            ], row_width=1)
        )
        await state.set_state(Form.mortgage)
    
    elif call.data == "📞 Контактные данные":
        # Редактирование контактных данных
        await call.message.answer(
            "Как вас зовут?",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(Form.name)
    
    elif call.data == "⬅️ Назад":
        # Возвращаемся к экрану подтверждения
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
        confirm_message += f"📱 Телефон: +{data.get('phone', 'Не указано')}\n\n"
        
        confirm_message += "Всё верно?"
        
        # Отправляем сообщение с подтверждением
        await call.message.answer(
            confirm_message,
            reply_markup=get_inline_keyboard(["✅ Подтвердить", "❌ Изменить"], row_width=2)
        )
        
        # Устанавливаем состояние подтверждения
        await state.set_state(Form.confirm)

@dp.callback_query(lambda call: call.data == "❓ Помощь")
async def help_callback(call: types.CallbackQuery):
    await call.answer()
    
    await call.message.answer(
        "Я бот для подбора недвижимости. Вот что я могу:\n\n"
        "1. Помочь вам определиться с типом недвижимости\n"
        "2. Подобрать варианты по вашему бюджету\n"
        "3. Учесть ваши предпочтения по расположению\n"
        "4. Дать информацию об ипотечных программах\n\n"
        "Чтобы начать заново, нажмите кнопку ниже:",
        reply_markup=get_inline_keyboard(["🔄 Новая заявка"])
    )

# Обработчик для кнопки "Назад"
@dp.message(lambda message: message.text == "⬅️ Назад")
async def back_button(message: Message, state: FSMContext):
    # Получаем текущее состояние
    current_state = await state.get_state()
    if current_state is None:
        await cmd_start(message, state)
        return
    
    # Преобразуем строковое представление состояния в объект состояния
    current_state_obj = getattr(Form, current_state.split(':')[1])
    
    # Проверяем, есть ли предыдущее состояние для текущего
    if current_state_obj in PREVIOUS_STATES:
        # Получаем предыдущее состояние
        previous_state = PREVIOUS_STATES[current_state_obj]
        
        # Сохраняем текущие данные
        data = await state.get_data()
        
        # Устанавливаем предыдущее состояние
        await state.set_state(previous_state)
        
        # Отправляем соответствующий вопрос в зависимости от предыдущего состояния
        if previous_state == Form.residence:
            await message.answer(
                "Где вы сейчас проживаете?",
                reply_markup=get_reply_keyboard([
                    "Собственная квартира",
                    "Собственный дом",
                    "Аренда",
                    "С родителями/родственниками",
                    "Другое"
                ], row_width=1, add_back_button=False)
            )
        elif previous_state == Form.satisfaction:
            await message.answer(
                "Довольны ли вы своими текущими жилищными условиями?",
                reply_markup=get_reply_keyboard([
                    "Да, полностью доволен",
                    "Частично доволен",
                    "Нет, не доволен"
                ])
            )
        elif previous_state == Form.property_type:
            await message.answer(
                "Какой тип недвижимости вас интересует?",
                reply_markup=get_reply_keyboard([
                    "Квартира",
                    "Дом",
                    "Таунхаус",
                    "Участок земли",
                    "Коммерческая недвижимость"
                ], row_width=2)
            )
        elif previous_state == Form.location:
            await message.answer(
                "В каком районе или городе вы хотели бы приобрести недвижимость?",
                reply_markup=get_reply_keyboard([
                    "В центре города",
                    "В спальном районе",
                    "В пригороде",
                    "За городом",
                    "Другое (напишите свой вариант)"
                ], row_width=1)
            )
        elif previous_state == Form.budget:
            await message.answer(
                "Какой у вас бюджет на покупку недвижимости?",
                reply_markup=get_reply_keyboard([
                    "До 3 млн ₽",
                    "3-5 млн ₽",
                    "5-10 млн ₽",
                    "10-20 млн ₽",
                    "Более 20 млн ₽"
                ], row_width=1)
            )
        elif previous_state == Form.search_status:
            await message.answer(
                "На каком этапе поиска недвижимости вы находитесь?",
                reply_markup=get_reply_keyboard([
                    "Только начинаю искать",
                    "Уже смотрел(а) варианты",
                    "Определился(лась) с выбором",
                    "Готов(а) к сделке"
                ], row_width=1)
            )
        elif previous_state == Form.mortgage:
            await message.answer(
                "Планируете ли вы использовать ипотеку для покупки?",
                reply_markup=get_reply_keyboard([
                    "Да, уже одобрена",
                    "Да, планирую подать заявку",
                    "Нет, полная оплата",
                    "Еще не решил(а)"
                ], row_width=1)
            )
        elif previous_state == Form.purchase_time:
            await message.answer(
                "Когда вы планируете совершить покупку?",
                reply_markup=get_reply_keyboard([
                    "В ближайший месяц",
                    "В течение 3 месяцев",
                    "В течение полугода",
                    "В течение года",
                    "Пока просто смотрю варианты"
                ], row_width=1)
            )
        elif previous_state == Form.name:
            await message.answer(
                "Как вас зовут?",
                reply_markup=ReplyKeyboardRemove()
            )
        elif previous_state == Form.contact_method:
            await message.answer(
                "Как с вами удобнее связаться?",
                reply_markup=get_reply_keyboard([
                    "Телефон",
                    "WhatsApp",
                    "Telegram",
                    "Другое"
                ], row_width=2)
            )
        elif previous_state == Form.contact_time:
            await message.answer(
                "В какое время вам удобно, чтобы с вами связались?",
                reply_markup=get_reply_keyboard([
                    "Утро (9:00-12:00)",
                    "День (12:00-18:00)",
                    "Вечер (18:00-21:00)",
                    "В любое время"
                ], row_width=1)
            )
    else:
        # Если предыдущего состояния нет, начинаем заново
        await cmd_start(message, state)

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())