import logging
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота (ЗАМЕНИТЕ НА ВАШ ТОКЕН!)
BOT_TOKEN = ""

# Данные о товарах
PRODUCTS = {
    "komplekt_protivooskolochny": {
        "name": "🛡️ Комплект Противоосколочный",
        "description": "Полный комплект противоосколочной защиты для максимальной безопасности. Включает бронежилет, шлем, защиту конечностей.",
        "price": "199 500 руб",
        "category": "Комплекты",
        "details": "• Уровень защиты: 6а\n• Вес: 12 кг\n• Материал: кевлар+металл\n• Срок службы: 5 лет"
    },
    "komplekt_shturmovoy": {
        "name": "⚡ Комплект Штурмовой",
        "description": "Профессиональный штурмовой комплект для спецподразделений. Полная экипировка для штурмовых операций.",
        "price": "210 000 руб",
        "category": "Комплекты",
        "details": "• Уровень защиты: 6\n• Вес: 15 кг\n• Включает: бронежилет, шлем, разгрузку\n• Совместимость: с любым оружием"
    },
    "podarochny_sertifikat": {
        "name": "🎁 Подарочный Сертификат",
        "description": "Подарочный сертификат на приобретение защитной экипировки. Номинал 100 000 рублей.",
        "price": "100 000 руб",
        "category": "Сертификаты",
        "details": "• Срок действия: 1 год\n• Номинал: 100 000 руб\n• Можно комбинировать с другими покупками\n• Электронный или бумажный формат"
    },
    "purga": {
        "name": "❄️ Бронежилет Пурга",
        "description": "Надежный бронежилет для экстремальных условий. Защита от холода и влаги.",
        "price": "23 100 руб",
        "category": "Бронежилеты",
        "details": "• Класс защиты: 2\n• Вес: 4.5 кг\n• Температура: до -40°C\n• Водостойкость: да"
    },
    "mirazh": {
        "name": "🌫️ Бронежилет Мираж",
        "description": "Легкий и маневренный бронежилет для скрытного ношения.",
        "price": "39 900 руб",
        "category": "Бронежилеты",
        "details": "• Класс защиты: 3\n• Вес: 3.2 кг\n• Толщина: 15 мм\n• Скрытое ношение"
    },
    "ciklon": {
        "name": "🌀 Бронежилет Циклон",
        "description": "Универсальный бронежилет с улучшенной защитой. Подходит для городских условий.",
        "price": "55 650 руб",
        "category": "Бронежилеты",
        "details": "• Класс защиты: 4\n• Вес: 6.8 кг\n• Вентиляция: улучшенная\n• Размеры: S-XXL"
    },
    "promyshlenny": {
        "name": "🏭 Бронежилет Промышленный",
        "description": "Специализированный бронежилет для промышленных объектов и охраны предприятий.",
        "price": "63 000 руб",
        "category": "Бронежилеты",
        "details": "• Класс защиты: 3\n• Вес: 5.2 кг\n• Огнестойкость: да\n• Химзащита: частичная"
    },
    "taifun": {
        "name": "🌪️ Бронежилет Тайфун",
        "description": "Мощный бронежилет повышенной защиты для спецподразделений.",
        "price": "69 300 руб",
        "category": "Бронежилеты",
        "details": "• Класс защиты: 5\n• Вес: 8.1 кг\n• Бронепластины: 2 шт\n• Совместимость: с подсумками"
    },
    "shtorm": {
        "name": "🌊 Бронежилет Шторм",
        "description": "Профессиональный бронежилет для активных действий и длительных операций.",
        "price": "73 920 руб",
        "category": "Бронежилеты",
        "details": "• Класс защиты: 5+\n• Вес: 7.5 кг\n• Регулировка: полная\n• Износостойкость: высокая"
    },
    "zashita_shei": {
        "name": "🦵 Бронезащита Шеи",
        "description": "Защита шеи от осколков и пуль. Легкая и удобная конструкция.",
        "price": "23 100 руб",
        "category": "Доп. защита",
        "details": "• Вес: 0.8 кг\n• Регулировка: универсальная\n• Совместимость: с любым шлемом\n• Материал: баллистический нейлон"
    },
    "zashita_plech": {
        "name": "💪 Бронезащита Плеч",
        "description": "Бронезащита плечевых суставов. Не ограничивает подвижность.",
        "price": "15 750 руб",
        "category": "Доп. защита",
        "details": "• Вес: 1.2 кг/пара\n• Размеры: регулируемые\n• Крепление: на липучках\n• Защита: 2 класс"
    },
    "napashnik": {
        "name": "🎽 Напашник Пятиточечник",
        "description": "Удобный напашник с системой крепления для быстрого доступа к снаряжению.",
        "price": "15 750 руб",
        "category": "Экипировка",
        "details": "• Материал: Cordura\n• Крепление: 5 точек\n• Цвет: черный, хаки\n• Совместимость: стандартная"
    },
    "razgruzochny_poyas": {
        "name": "🦺 Разгрузочный пояс",
        "description": "Профессиональный разгрузочный пояс для тактического снаряжения.",
        "price": "23 000 руб",
        "category": "Экипировка",
        "details": "• Ширина: 10 см\n• Регулировка: 70-130 см\n• Материал: нейлон 1000D\n• Кольца: 4 шт"
    },
    "poyas_kobura": {
        "name": "🔫 Пояс Кобура",
        "description": "Специализированный пояс с кобурой для ношения оружия.",
        "price": "5 250 руб",
        "category": "Экипировка",
        "details": "• Материал: кожа\n• Подходит: для ПМ, ТТ\n• Регулировка: да\n• Цвет: черный, коричневый"
    },
    "zashita_nog": {
        "name": "🦵 Бронезащита ног",
        "description": "Полная защита нижних конечностей. Защищает бедра, колени, голени.",
        "price": "79 800 руб",
        "category": "Доп. защита",
        "details": "• Защита: 3 класс\n• Вес: 3.5 кг\n• Регулировка: по размеру\n• Материал: кевлар+пластик"
    },
    "zaryadka_ak": {
        "name": "🔋 Заряжалка АК",
        "description": "Заряжалка для автомата Калашникова. Ускоряет процесс заряжания магазинов.",
        "price": "1 575 руб",
        "category": "Аксессуары",
        "details": "• Совместимость: АК-74, АКМ\n• Материал: пластик+металл\n• Вес: 0.3 кг\n• Цвет: черный"
    },
    "ukazatel_miny": {
        "name": "⚠️ Указатель Мины",
        "description": "Специализированный указатель минной опасности. Яркий и заметный.",
        "price": "63 руб",
        "category": "Аксессуары",
        "details": "• Материал: пластик\n• Цвет: красный/оранжевый\n• Высота: 45 см\n• Погодоустойчивость: да"
    },
    "stelki": {
        "name": "👞 Стельки",
        "description": "Специальные стельки для тактической обуви. Амортизация и комфорт.",
        "price": "5 250 руб",
        "category": "Аксессуары",
        "details": "• Материал: гель+пена\n• Размеры: 36-47\n• Антибактериальные: да\n• Срок службы: 1 год"
    },
    "tacticheskaya_sumka": {
        "name": "🎒 Тактическая сумка-баул",
        "description": "Вместительная тактическая сумка для переноски снаряжения.",
        "price": "6 650 руб",
        "category": "Экипировка",
        "details": "• Объем: 40 л\n• Материал: Cordura 1000D\n• Отделения: 3 основных\n• Ремни: регулируемые"
    },
    "nosilki": {
        "name": "🚑 Эвакуационные носилки Классный Спасатель (КОБ)",
        "description": "Профессиональные эвакуационные носилки для спасработ. Жесткая конструкция.",
        "price": "656 250 руб",
        "category": "Мед. оборудование",
        "details": "• Грузоподъемность: 180 кг\n• Вес: 8.5 кг\n• Материал: алюминий+пластик\n• Складная конструкция: да"
    },
    "bronelity": {
        "name": "🛡️ Бронеплиты",
        "description": "Сменные бронеплиты для бронежилетов. Керамические или стальные.",
        "price": "5 500 руб",
        "category": "Комплектующие",
        "details": "• Размер: 25x30 см\n• Вес: 2.1 кг\n• Класс защиты: 4\n• Совместимость: универсальная"
    },
    "bronepakety": {
        "name": "📦 Бронепакеты",
        "description": "Бронепакеты для усиления защиты. Легкие и эффективные.",
        "price": "5 000 руб",
        "category": "Комплектующие",
        "details": "• Размер: 20x25 см\n• Вес: 1.8 кг\n• Класс защиты: 3а\n• Материал: полиэтилен"
    }
}

# Частые вопросы
FAQ = {
    "delivery": {
        "question": "🚚 Доставка и сроки",
        "answer": "• Доставка по России: 1-3 рабочих дня\n• Самовывоз: г. Москва, ул. Защитная, 15\n• Курьерская доставка: бесплатно от 50 000 руб\n• Срочная доставка: +50% к стоимости"
    },
    "payment": {
        "question": "💳 Способы оплаты",
        "answer": "• Наличные при получении\n• Банковская карта (онлайн)\n• Безналичный расчет для юр. лиц\n• Рассрочка на 3 месяца"
    },
    "warranty": {
        "question": "🔧 Гарантия и возврат",
        "answer": "• Гарантия: 12 месяцев\n• Возврат в течение 14 дней\n• Обмен неисправного товара\n• Сервисное обслуживание"
    },
    "certification": {
        "question": "📋 Сертификация",
        "answer": "• Все товары сертифицированы по ГОСТ\n• Соответствуют стандартам МВД\n• Имеют паспорта качества\n• Прошли баллистические испытания"
    },
    "sizes": {
        "question": "📏 Подбор размера",
        "answer": "• Бесплатная консультация по размерам\n• Таблица размеров на сайте\n• Возможность примерки в шоуруме\n• Обмен размера в течение 7 дней"
    }
}


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.effective_user.id} started the bot")

    keyboard = [
        [KeyboardButton("🛍️ Каталог товаров"), KeyboardButton("❓ Частые вопросы")],
        [KeyboardButton("ℹ️ О компании"), KeyboardButton("📞 Контакты")],
        [KeyboardButton("🔥 Топ товары"), KeyboardButton("🛒 Корзина")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "🛡️ Добро пожаловать в магазин защитной экипировки и бронежилетов!\n\n"
        "Мы предлагаем полный спектр средств защиты для вашей безопасности.\n\n"
        "Выберите действие:",
        reply_markup=reply_markup
    )


# Показ каталога товаров
async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []

    # Группируем товары по категориям
    categories = {}
    for product_id, product in PRODUCTS.items():
        category = product["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append((product_id, product))

    # Создаем кнопки для каждой категории
    for category in sorted(categories.keys()):
        keyboard.append([InlineKeyboardButton(f"📂 {category}", callback_data=f"category_{category}")])

    keyboard.append([InlineKeyboardButton("🔥 Все товары списком", callback_data="all_products")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            "🛍️ Каталог защитной экипировки:\n\n"
            "Выберите категорию товаров:",
            reply_markup=reply_markup
        )
    else:
        await update.callback_query.message.reply_text(
            "🛍️ Каталог защитной экипировки:\n\n"
            "Выберите категорию товаров:",
            reply_markup=reply_markup
        )


# Показ частых вопросов
async def show_faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []

    for faq_id, faq in FAQ.items():
        keyboard.append([InlineKeyboardButton(faq["question"], callback_data=f"faq_{faq_id}")])

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "❓ Частые вопросы:\n\n"
        "Выберите интересующий вас вопрос:",
        reply_markup=reply_markup
    )


# Показ ответа на вопрос
async def show_faq_answer(query, faq_id):
    faq = FAQ[faq_id]

    text = f"{faq['question']}\n\n{faq['answer']}"

    keyboard = [
        [InlineKeyboardButton("📋 Все вопросы", callback_data="back_to_faq")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text, reply_markup=reply_markup)


# Показ товаров по категориям
async def show_category(query, category_name):
    keyboard = []

    # Находим товары в выбранной категории
    category_products = []
    for product_id, product in PRODUCTS.items():
        if product["category"] == category_name:
            category_products.append((product_id, product))

    # Сортируем товары по цене
    category_products.sort(key=lambda x: int(''.join(x[1]["price"].split()[:-1])))

    for product_id, product in category_products:
        keyboard.append([InlineKeyboardButton(
            f"{product['name']} - {product['price']}",
            callback_data=f"product_{product_id}"
        )])

    keyboard.append([InlineKeyboardButton("🔙 Назад к категориям", callback_data="back_to_catalog")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"📂 {category_name}:\n\n"
        f"Найдено товаров: {len(category_products)}\n"
        "Выберите товар для подробной информации:",
        reply_markup=reply_markup
    )


# Показ всех товаров списком
async def show_all_products(query):
    keyboard = []

    # Сортируем товары по цене
    sorted_products = sorted(PRODUCTS.items(), key=lambda x: int(''.join(x[1]["price"].split()[:-1])))

    for product_id, product in sorted_products:
        keyboard.append([InlineKeyboardButton(
            f"{product['name']} - {product['price']}",
            callback_data=f"product_{product_id}"
        )])

    keyboard.append([InlineKeyboardButton("🔙 Назад к категориям", callback_data="back_to_catalog")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "🔥 Все товары:\n\n"
        "Выберите товар для подробной информации:",
        reply_markup=reply_markup
    )


# Показ топ товаров
async def show_top_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Выбираем несколько товаров как "топ"
    top_products_ids = [
        "komplekt_shturmovoy",
        "ciklon",
        "taifun",
        "zashita_nog",
        "nosilki"
    ]

    keyboard = []

    for product_id in top_products_ids:
        if product_id in PRODUCTS:
            product = PRODUCTS[product_id]
            keyboard.append([InlineKeyboardButton(
                f"{product['name']} - {product['price']}",
                callback_data=f"product_{product_id}"
            )])

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🔥 Самые популярные товары:\n\n"
        "Проверенные решения для вашей безопасности:",
        reply_markup=reply_markup
    )


# Информация о компании
async def about_company(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏢 О компании:\n\n"
        "Лучший  поставщик защитной экипировки и бронежилетов в России. С нашими бронежилетами даже супермену не страшен криптонит \n\n"
        "✅ Все товары сертифицированы\n"
        "✅ Гарантия качества ГОСТ\n"
        "✅ Доставка по всей России\n"
        "✅ Консультация специалистов\n"
        "✅ Большой опыт работы"
    )


# Контакты
async def contacts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📞 Контакты:\n\n"
        "📞 Телефон: +79319728435\n"
        "📧 Email: Пока нету\n"
        "🌐 Сайт: https://technokryptonite.ru/\n"
        "📍 Адрес: ул. Маршала Тухачевского, 22, Санкт-Петербург\n\n"
        "⏰ Время работы: Пн-Пт 9:00-18:00\n"
        "🚚 Доставка: 1-3 рабочих дня"
    )


# Обработка инлайн кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    logger.info(f"Button pressed: {data}")

    try:
        if data.startswith("product_"):
            # Исправляем обработку product_id - берем всю строку после "product_"
            product_id = data[8:]  # Берем все после "product_"
            await show_product(query, product_id)
        elif data.startswith("category_"):
            category_name = data[9:]  # Берем все после "category_"
            await show_category(query, category_name)
        elif data.startswith("faq_"):
            faq_id = data[4:]  # Берем все после "faq_"
            await show_faq_answer(query, faq_id)
        elif data == "all_products":
            await show_all_products(query)
        elif data == "back_to_catalog":
            await show_catalog_from_button(query)
        elif data == "back_to_faq":
            await show_faq_from_button(query)
        elif data == "back_to_main":
            await back_to_main(query)
        elif data == "buy_now":
            await buy_now(query)
    except Exception as e:
        logger.error(f"Error in button handler: {e}")
        await query.message.reply_text("❌ Произошла ошибка. Попробуйте еще раз.")


# Показ информации о товаре
async def show_product(query, product_id):
    try:
        if product_id not in PRODUCTS:
            await query.message.reply_text("❌ Товар не найден.")
            return

        product = PRODUCTS[product_id]

        # Проверяем есть ли детальная информация
        details = product.get("details", "• Информация уточняется у менеджера\n• Все характеристики соответствуют ГОСТ")

        text = (
            f"{product['name']}\n\n"
            f"{product['description']}\n\n"
            f"📂 Категория: {product['category']}\n"
            f"💰 Цена: {product['price']}\n\n"
            f"📋 Характеристики:\n{details}\n\n"
            "✅ В наличии на складе\n"
            "✅ Доставка 1-3 дня\n"
            "✅ Гарантия 12 месяцев\n"
            "✅ Сертифицированная продукция"
        )

        keyboard = [
            [InlineKeyboardButton("🛒 Купить сейчас", callback_data="buy_now")],
            [InlineKeyboardButton("📂 Назад к каталогу", callback_data="back_to_catalog")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Error showing product {product_id}: {e}")
        await query.message.reply_text("❌ Ошибка при загрузке информации о товаре.")


# Показ каталога из кнопки
async def show_catalog_from_button(query):
    keyboard = []

    categories = {}
    for product_id, product in PRODUCTS.items():
        category = product["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append((product_id, product))

    for category in sorted(categories.keys()):
        keyboard.append([InlineKeyboardButton(f"📂 {category}", callback_data=f"category_{category}")])

    keyboard.append([InlineKeyboardButton("🔥 Все товары списком", callback_data="all_products")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "🛍️ Каталог защитной экипировки:\n\n"
        "Выберите категорию товаров:",
        reply_markup=reply_markup
    )


# Показ FAQ из кнопки
async def show_faq_from_button(query):
    keyboard = []

    for faq_id, faq in FAQ.items():
        keyboard.append([InlineKeyboardButton(faq["question"], callback_data=f"faq_{faq_id}")])

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "❓ Частые вопросы:\n\n"
        "Выберите интересующий вас вопрос:",
        reply_markup=reply_markup
    )


# Возврат в главное меню
async def back_to_main(query):
    keyboard = [
        [KeyboardButton("🛍️ Каталог товаров"), KeyboardButton("❓ Частые вопросы")],
        [KeyboardButton("ℹ️ О компании"), KeyboardButton("📞 Контакты")],
        [KeyboardButton("🔥 Топ товары"), KeyboardButton("🛒 Корзина")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await query.message.reply_text(
        "Главное меню. Выберите действие:",
        reply_markup=reply_markup
    )


# Оформление заказа
async def buy_now(query):
    await query.edit_message_text(
        "🛒 Для оформления заказа:\n\n"
        "📞 Позвоните: +79319728435\n"
        "📧 Напишите: ПОка email нету\n"
        "💬 Или напишите нам в WhatsApp/Telegram\n\n"
        "При заказе укажите:\n"
        "• Название товара\n"
        "• Количество\n"
        "• Адрес доставки\n"
        "• Контактные данные\n\n"
        "📦 Доставим за 1-3 дня по всей России!"
    )


# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    logger.info(f"Message received: {text}")

    try:
        if text == "🛍️ Каталог товаров":
            await show_catalog(update, context)
        elif text == "❓ Частые вопросы":
            await show_faq(update, context)
        elif text == "ℹ️ О компании":
            await about_company(update, context)
        elif text == "📞 Контакты":
            await contacts(update, context)
        elif text == "🔥 Топ товары":
            await show_top_products(update, context)
        elif text == "🛒 Корзина":
            await update.message.reply_text(
                "🛒 Для оформления заказа используйте кнопку 'Купить сейчас' в карточке товара.\n\n"
                "Или свяжитесь с нами:\n"
                "📞 ++79319728435\n"

            )
        else:
            await update.message.reply_text("Используйте кнопки меню для навигации.")
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте еще раз.")


# Обработка ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Exception while handling an update: {context.error}")


# Основная функция
def main():
    # Проверяем токен
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("❌ ОШИБКА: Замените BOT_TOKEN на ваш настоящий токен бота!")
        return

    try:
        application = Application.builder().token(BOT_TOKEN).build()

        # Обработчики команд
        application.add_handler(CommandHandler("start", start))

        # Обработчики кнопок
        application.add_handler(CallbackQueryHandler(button_handler))

        # Обработчики сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Обработчик ошибок
        application.add_error_handler(error_handler)

        # Запуск бота
        print("🤖 Бот запускается...")
        application.run_polling()
        print("✅ Бот успешно запущен!")

    except Exception as e:
        print(f"❌ Ошибка при запуске бота: {e}")


if __name__ == "__main__":

    main()
