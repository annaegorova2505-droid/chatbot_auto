import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
import json
import os

# Настройки
BOT_TOKEN = "8466756793:AAGk7Qh6TViRnN1jWM05wopoGifoMkWdbkY"
ADMIN_ID = "@annegorovka"

BRANDS = ["Toyota", "BMW", "Mercedes", "Audi", "Volkswagen", "Hyundai", "Kia", "Nissan"]
BODY_TYPES = ["Седан", "Внедорожник", "Хэтчбек", "Универсал", "Купе", "Минивэн", "Пикап"]
ENGINE_TYPES = ["Бензин", "Дизель", "Электро", "Гибрид"]
TRANSMISSIONS = ["Автомат", "Механика", "Вариатор", "Робот"]
PRICE_RANGES = [
    "До 500 000 ₽",
    "500 000 - 1 000 000 ₽", 
    "1 000 000 - 2 000 000 ₽",
    "2 000 000 - 5 000 000 ₽",
    "Свыше 5 000 000 ₽"
]

# Простая база данных
class Database:
    def __init__(self):
        self.cars_file = "cars.json"
        self.load_data()
    
    def load_data(self):
        try:
            with open(self.cars_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except:
            self.data = {"cars": [], "contacts": {}}
    
    def get_cars(self, filters=None):
        cars = [car for car in self.data["cars"] if car["is_available"]]
        if not filters:
            return cars
        
        filtered_cars = []
        for car in cars:
            match = True
            if filters.get('brand') and car['brand'] != filters['brand']:
                match = False
            if filters.get('body_type') and car['body_type'] != filters['body_type']:
                match = False
            if filters.get('engine_type') and car['engine_type'] != filters['engine_type']:
                match = False
            if filters.get('transmission') and car['transmission'] != filters['transmission']:
                match = False
            if filters.get('price_range'):
                price_range = filters['price_range']
                price = car['price']
                if price_range == "До 500 000 ₽" and price > 500000:
                    match = False
                elif price_range == "500 000 - 1 000 000 ₽" and (price < 500000 or price > 1000000):
                    match = False
                elif price_range == "1 000 000 - 2 000 000 ₽" and (price < 1000000 or price > 2000000):
                    match = False
                elif price_range == "2 000 000 - 5 000 000 ₽" and (price < 2000000 or price > 5000000):
                    match = False
                elif price_range == "Свыше 5 000 000 ₽" and price < 5000000:
                    match = False
            
            if match:
                filtered_cars.append(car)
        return filtered_cars
    
    def count_cars_by_filters(self, filters):
        return len(self.get_cars(filters))
    
    def get_contacts(self):
        return self.data.get("contacts", {})
    
    def get_car_by_id(self, car_id):
        for car in self.data["cars"]:
            if car["id"] == car_id:
                return car
        return None

db = Database()

# Клавиатуры
def get_main_menu():
    keyboard = [["🚗 Каталог авто"], ["📞 Контакты", "🆘 Помощь"]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_catalog_menu():
    keyboard = [
        [InlineKeyboardButton("🎛 Подбор по параметрам", callback_data="filter_params")],
        [InlineKeyboardButton("📋 Смотреть все авто", callback_data="show_all")],
        [InlineKeyboardButton("⬅️ Назад в главное меню", callback_data="back_to_main_from_catalog")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_filters_menu():
    keyboard = [
        [InlineKeyboardButton("🏷 Марка", callback_data="filter_brand")],
        [InlineKeyboardButton("🚙 Тип кузова", callback_data="filter_body")],
        [InlineKeyboardButton("⚙️ Тип двигателя", callback_data="filter_engine")],
        [InlineKeyboardButton("🔧 Коробка передач", callback_data="filter_transmission")],
        [InlineKeyboardButton("💰 Цена", callback_data="filter_price")],
        [InlineKeyboardButton("📊 Смотреть наличие", callback_data="check_availability")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_catalog")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_brands_keyboard():
    keyboard = []
    for brand in BRANDS:
        keyboard.append([InlineKeyboardButton(brand, callback_data=f"select_brand_{brand}")])
    keyboard.append([InlineKeyboardButton("📊 Смотреть наличие", callback_data="check_availability")])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_filters")])
    return InlineKeyboardMarkup(keyboard)

def get_body_types_keyboard():
    keyboard = []
    for body in BODY_TYPES:
        keyboard.append([InlineKeyboardButton(body, callback_data=f"select_body_{body}")])
    keyboard.append([InlineKeyboardButton("📊 Смотреть наличие", callback_data="check_availability")])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_filters")])
    return InlineKeyboardMarkup(keyboard)

def get_engine_types_keyboard():
    keyboard = []
    for engine in ENGINE_TYPES:
        keyboard.append([InlineKeyboardButton(engine, callback_data=f"select_engine_{engine}")])
    keyboard.append([InlineKeyboardButton("📊 Смотреть наличие", callback_data="check_availability")])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_filters")])
    return InlineKeyboardMarkup(keyboard)

def get_transmission_keyboard():
    keyboard = []
    for transmission in TRANSMISSIONS:
        keyboard.append([InlineKeyboardButton(transmission, callback_data=f"select_transmission_{transmission}")])
    keyboard.append([InlineKeyboardButton("📊 Смотреть наличие", callback_data="check_availability")])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_filters")])
    return InlineKeyboardMarkup(keyboard)

def get_price_ranges_keyboard():
    keyboard = []
    for price in PRICE_RANGES:
        keyboard.append([InlineKeyboardButton(price, callback_data=f"select_price_{price}")])
    keyboard.append([InlineKeyboardButton("📊 Смотреть наличие", callback_data="check_availability")])
    keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data="back_to_filters")])
    return InlineKeyboardMarkup(keyboard)

def get_availability_keyboard(count):
    keyboard = [
        [InlineKeyboardButton(f"✅ Смотреть {count} авто", callback_data="view_available_cars")],
        [InlineKeyboardButton("🔄 Новый поиск", callback_data="new_search")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_filters")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_car_navigation_keyboard(car_index, total_cars):
    keyboard = []
    nav_buttons = []
    if car_index > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️", callback_data=f"prev_{car_index-1}"))
    
    nav_buttons.append(InlineKeyboardButton(f"{car_index+1}/{total_cars}", callback_data="current"))
    
    if car_index < total_cars - 1:
        nav_buttons.append(InlineKeyboardButton("➡️", callback_data=f"next_{car_index+1}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.extend([
        [InlineKeyboardButton("📞 Оставить заявку", callback_data="create_application")],
        [InlineKeyboardButton("⬅️ Назад к каталогу", callback_data="back_to_catalog")]
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_contacts_keyboard():
    keyboard = [
        [InlineKeyboardButton("📞 Оставить заявку", callback_data="create_application")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Обработчики
async def start(update, context):
    user = update.effective_user
    welcome_text = f"""👋 Добро пожаловать, {user.first_name}!

🚗 Добро пожаловать в автосалон AutoHouse!

Выберите нужный раздел:"""
    await update.message.reply_text(welcome_text, reply_markup=get_main_menu())

async def help_command(update, context):
    help_text = """🆘 Помощь

• 🚗 Каталог авто - подбор автомобиля по параметрам
• 📞 Контакты - свяжитесь с нами

Для начала работы нажмите «🚗 Каталог авто»"""
    await update.message.reply_text(help_text, reply_markup=get_main_menu())

async def show_catalog(update, context):
    context.user_data.clear()
    text = "🚗 Каталог автомобилей\n\nВыберите способ поиска:"
    if hasattr(update, 'message'):
        await update.message.reply_text(text, reply_markup=get_catalog_menu())
    else:
        await update.edit_message_text(text, reply_markup=get_catalog_menu())

async def show_contacts(update, context):
    contacts = db.get_contacts()
    contacts_text = f"""📞 Контакты автосалона

📱 Телефон: {contacts.get('phone', 'не указан')}
💬 WhatsApp: {contacts.get('whatsapp', 'не указан')}
📧 Email: {contacts.get('email', 'не указан')}

🏢 Адрес: {contacts.get('address', 'не указан')}
🕒 График работы: {contacts.get('work_hours', 'не указан')}

Свяжитесь с нами или оставьте заявку! 🚗"""
    
    if hasattr(update, 'message'):
        await update.message.reply_text(contacts_text, reply_markup=get_contacts_keyboard())
    else:
        await update.edit_message_text(contacts_text, reply_markup=get_contacts_keyboard())

# Обработчики каталога
async def show_filter_params(update, context):
    query = update.callback_query
    await query.answer()
    text = "🎛 Подбор по параметрам\n\nВыберите параметр для фильтрации:"
    await query.edit_message_text(text, reply_markup=get_filters_menu())

async def show_all_cars(update, context):
    query = update.callback_query
    await query.answer()
    
    cars = db.get_cars()
    if not cars:
        await query.edit_message_text("На данный момент нет доступных автомобилей.")
        return
    
    context.user_data['current_cars'] = cars
    context.user_data['current_index'] = 0
    await show_car(query, context, 0)

async def show_car(update, context, index):
    cars = context.user_data.get('current_cars', [])
    
    if not cars or index >= len(cars):
        await update.edit_message_text("Автомобиль не найден")
        return
    
    car = cars[index]
    
    caption = f"""
🚗 *{car['brand']} {car['model']}*

📅 Год: {car['year']}
💰 Цена: *{car['price']:,} ₽*
🎨 Цвет: {car['color']}
📏 Пробег: {car['mileage']:,} км
⚙️ Двигатель: {car['engine_type']}, {car['engine_volume']} л
🔧 КПП: {car['transmission']}
🏷 Кузов: {car['body_type']}

📝 *{car['description']}*

🎯 *Особенности:*
{chr(10).join(['• ' + feature for feature in car['features']])}
"""
    
    try:
        if car['photos']:
            from telegram import InputMediaPhoto
            media = InputMediaPhoto(media=car['photos'][0], caption=caption, parse_mode=ParseMode.MARKDOWN)
            await update.edit_message_media(media=media, reply_markup=get_car_navigation_keyboard(index, len(cars)))
        else:
            await update.edit_message_text(caption, parse_mode=ParseMode.MARKDOWN, reply_markup=get_car_navigation_keyboard(index, len(cars)))
    except:
        await update.edit_message_text(caption, parse_mode=ParseMode.MARKDOWN, reply_markup=get_car_navigation_keyboard(index, len(cars)))

# Обработчики фильтров
async def filter_brand(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🏷 Выберите марку автомобиля:", reply_markup=get_brands_keyboard())

async def filter_body(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🚙 Выберите тип кузова:", reply_markup=get_body_types_keyboard())

async def filter_engine(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⚙️ Выберите тип двигателя:", reply_markup=get_engine_types_keyboard())

async def filter_transmission(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🔧 Выберите коробку передач:", reply_markup=get_transmission_keyboard())

async def filter_price(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("💰 Выберите ценовой диапазон:", reply_markup=get_price_ranges_keyboard())

async def handle_filter_selection(update, context):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if 'filters' not in context.user_data:
        context.user_data['filters'] = {}
    
    if data.startswith('select_brand_'):
        brand = data.replace('select_brand_', '')
        context.user_data['filters']['brand'] = brand
        text = f"✅ Выбрана марка: {brand}\n\nВыберите следующий параметр или проверьте наличие:"
    
    elif data.startswith('select_body_'):
        body = data.replace('select_body_', '')
        context.user_data['filters']['body_type'] = body
        text = f"✅ Выбран кузов: {body}\n\nВыберите следующий параметр или проверьте наличие:"
    
    elif data.startswith('select_engine_'):
        engine = data.replace('select_engine_', '')
        context.user_data['filters']['engine_type'] = engine
        text = f"✅ Выбран двигатель: {engine}\n\nВыберите следующий параметр или проверьте наличие:"
    
    elif data.startswith('select_transmission_'):
        transmission = data.replace('select_transmission_', '')
        context.user_data['filters']['transmission'] = transmission
        text = f"✅ Выбрана КПП: {transmission}\n\nВыберите следующий параметр или проверьте наличие:"
    
    elif data.startswith('select_price_'):
        price = data.replace('select_price_', '')
        context.user_data['filters']['price_range'] = price
        text = f"✅ Выбран ценовой диапазон: {price}\n\nВыберите следующий параметр или проверьте наличие:"
    
    await query.edit_message_text(text, reply_markup=get_filters_menu())

async def check_availability(update, context):
    query = update.callback_query
    await query.answer()
    
    filters = context.user_data.get('filters', {})
    count = db.count_cars_by_filters(filters)
    
    filters_text = "Текущие фильтры:\n"
    if filters.get('brand'):
        filters_text += f"• Марка: {filters['brand']}\n"
    if filters.get('body_type'):
        filters_text += f"• Кузов: {filters['body_type']}\n"
    if filters.get('engine_type'):
        filters_text += f"• Двигатель: {filters['engine_type']}\n"
    if filters.get('transmission'):
        filters_text += f"• КПП: {filters['transmission']}\n"
    if filters.get('price_range'):
        filters_text += f"• Цена: {filters['price_range']}\n"
    
    if not filters:
        filters_text = "Фильтры не установлены\n"
    
    text = f"📊 Проверка наличия\n\n{filters_text}\n✅ Доступно {count} авто"
    await query.edit_message_text(text, reply_markup=get_availability_keyboard(count))

async def view_available_cars(update, context):
    query = update.callback_query
    await query.answer()
    
    filters = context.user_data.get('filters', {})
    cars = db.get_cars(filters)
    
    if not cars:
        await query.edit_message_text("По вашим параметрам не найдено доступных автомобилей.")
        return
    
    context.user_data['current_cars'] = cars
    context.user_data['current_index'] = 0
    await show_car(query, context, 0)

async def new_search(update, context):
    query = update.callback_query
    await query.answer()
    
    context.user_data['filters'] = {}
    text = "🔄 Новый поиск\n\nВыберите параметр для фильтрации:"
    await query.edit_message_text(text, reply_markup=get_filters_menu())

# Навигация по автомобилям
async def handle_car_navigation(update, context):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('prev_'):
        new_index = int(query.data.split('_')[1])
        await show_car(query, context, new_index)
    elif query.data.startswith('next_'):
        new_index = int(query.data.split('_')[1])
        await show_car(query, context, new_index)
    elif query.data == 'back_to_catalog':
        await show_catalog(query, context)

# Обработчики кнопки "Назад"
async def back_to_main(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Главное меню:", reply_markup=get_main_menu())

async def back_to_main_from_catalog(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Главное меню:", reply_markup=get_main_menu())

async def back_to_catalog(update, context):
    query = update.callback_query
    await query.answer()
    await show_catalog(query, context)

async def back_to_filters(update, context):
    query = update.callback_query
    await query.answer()
    text = "🎛 Подбор по параметрам\n\nВыберите параметр для фильтрации:"
    await query.edit_message_text(text, reply_markup=get_filters_menu())

# Обработчик заявки (ИСПРАВЛЕННЫЙ)
async def create_application(update, context):
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    application_text = f"""
📋 *Новая заявка от пользователя*

👤 Имя: {user.first_name}
📞 Username: @{user.username or 'не указан'}
🆔 ID: {user.id}

💬 Пользователь хочет получить консультацию по автомобилю!"""

    # Отправляем администратору
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID, 
            text=application_text,
            parse_mode=ParseMode.MARKDOWN
        )
        print(f"✅ Заявка отправлена на {ADMIN_ID}")
    except Exception as e:
        print(f"❌ Ошибка отправки заявки: {e}")
    
    # Ответ пользователю
    success_text = """✅ *Спасибо за ваше обращение!*

В ближайшее время менеджер с вами свяжется для уточнения деталей.

Хорошего дня! 😊"""
    
    await query.message.reply_text(
        success_text, 
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_main_menu()
    )

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # Главное меню
    application.add_handler(MessageHandler(filters.Text("🚗 Каталог авто"), show_catalog))
    application.add_handler(MessageHandler(filters.Text("📞 Контакты"), show_contacts))
    application.add_handler(MessageHandler(filters.Text("🆘 Помощь"), help_command))
    
    # Каталог
    application.add_handler(CallbackQueryHandler(show_filter_params, pattern="^filter_params$"))
    application.add_handler(CallbackQueryHandler(show_all_cars, pattern="^show_all$"))
    
    # Фильтры
    application.add_handler(CallbackQueryHandler(filter_brand, pattern="^filter_brand$"))
    application.add_handler(CallbackQueryHandler(filter_body, pattern="^filter_body$"))
    application.add_handler(CallbackQueryHandler(filter_engine, pattern="^filter_engine$"))
    application.add_handler(CallbackQueryHandler(filter_transmission, pattern="^filter_transmission$"))
    application.add_handler(CallbackQueryHandler(filter_price, pattern="^filter_price$"))
    application.add_handler(CallbackQueryHandler(handle_filter_selection, pattern="^select_"))
    application.add_handler(CallbackQueryHandler(check_availability, pattern="^check_availability$"))
    application.add_handler(CallbackQueryHandler(view_available_cars, pattern="^view_available_cars$"))
    application.add_handler(CallbackQueryHandler(new_search, pattern="^new_search$"))
    
    # Навигация
    application.add_handler(CallbackQueryHandler(handle_car_navigation, pattern="^(prev_|next_|back_to_catalog)"))
    
    # Кнопки Назад
    application.add_handler(CallbackQueryHandler(back_to_main, pattern="^back_to_main$"))
    application.add_handler(CallbackQueryHandler(back_to_main_from_catalog, pattern="^back_to_main_from_catalog$"))
    application.add_handler(CallbackQueryHandler(back_to_catalog, pattern="^back_to_catalog$"))
    application.add_handler(CallbackQueryHandler(back_to_filters, pattern="^back_to_filters$"))
    
    # Заявка
    application.add_handler(CallbackQueryHandler(create_application, pattern="^create_application$"))
    
    print("✅ Бот запускается... Кнопки 'Назад' и 'Заявка' исправлены!")
    application.run_polling()

if __name__ == "__main__":
    main()