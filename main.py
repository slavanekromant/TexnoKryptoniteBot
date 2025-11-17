import logging
import os
import re
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
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# Конфигурация через Pydantic
class Settings(BaseSettings):
    """Конфигурация приложения через Pydantic"""
    bot_token: str = Field(..., validation_alias='BOT_TOKEN')

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )


# Инициализация конфигурации
try:
    settings = Settings()
    BOT_TOKEN = settings.bot_token
    logger.info("Конфигурация успешно загружена")
except Exception as e:
    logger.error(f"Ошибка загрузки конфигурации: {e}")
    # Fallback на переменные окружения
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не найден в конфигурации или переменных окружения")
        raise ValueError("BOT_TOKEN не найден. Создайте файл .env с BOT_TOKEN=ваш_токен")

# Данные о товарах
PRODUCTS = {
    "komplekt_protivooskolochny": {
        "name": "🛡️ Комплект Противоосколочный",
        "description": "Полный комплект противоосколочной защиты для максимальной безопасности в условиях повышенного риска. Включает бронежилет, шлем и защиту конечностей.",
        "price": "199 500 руб",
        "category": "Комплекты",
        "details": "• Комплектация:\nБронешлем БР2 степени защиты\nБронежилет «Тайфун» с интегрированной защитой шеи\nЗащита плеч\nНапашник (стандартный, лепестковый)\nПятиточечник\nРПС (разгрузочно-поясная система) с баллистикой и подтяжками\nБронезащита ног (модели бедер и голени)\nПротивогрязевые гамаши\nКомплект документов\nСумка-переноска\n• Срок службы: 5 лет\n• Гарантия: 60 месяцев"
    },
    "komplekt_shturmovoy": {
        "name": "⚡ Комплект Штурмовой",
        "description": "Профессиональный штурмовой комплект для спецподразделений. Полная экипировка для проведения операций любого уровня сложности.",
        "price": "210 000 руб",
        "category": "Комплекты",
        "details": "• Комплектация:\nБронешлем БР2 степени защиты\nЗащита шеи\nУвеличенная защита плеч\nБронежилет «Пурга» с круговой баллистикой и системой КАП\nРПС (разгрузочно-поясная система) с баллистикой и встроенными подтяжками\nНапашник (стандартный, лепестковый)\nПятиточечник\nБронезащита ног (модули на бедра и голени)\nПротивогрязевые гамаши\nПлиты от БР3 до БР5 степень защиты(сталь, керамика, оксид алюминия)\nКомплект документов(сертификаты, паспорта)\nСумка-переноска\n• Гарантия: 60 месяцев"
    },
    "podarochny_sertifikat": {
        "name": "🎁 Подарочный Сертификат",
        "description": "Идеальное решение для тех, кто ценит безопасность. Подарите возможность выбора защитной экипировки.",
        "price": "100 000 руб",
        "category": "Сертификаты",
        "details": "• Номинал: 100 000 руб\n• Срок действия: 1 год\n• Можно комбинировать с другими покупками\n• Электронный или бумажный формат"
    },
    "purga": {
        "name": "❄️ Бронежилет Пурга",
        "description": "Надежный бронежилет для экстремальных условий. Баланс защиты, веса и функциональности.",
        "price": "23 100 руб / 45 500 руб (без/с баллистикой)",
        "category": "Бронежилеты",
        "details": "• Класс защиты: БР 1\n• Вес: 3.5 кг\n• Быстросброс: да\n• Универсальность: да\n• Регулировка размерности: да\n• Универсальный карман под плиты\n• ИК-ремиссия: да\n• Съемная планка\n• Увеличенная площадь защиты"
    },
    "mirazh": {
        "name": "🌫️ Бронежилет Мираж",
        "description": "Легкий и маневренный бронежилет для тех, кто ценит мобильность без ущерба для защиты.",
        "price": "39 900 руб",
        "category": "Бронежилеты",
        "details": "• Класс защиты: Бр1-2\n• Вес: 2.5-3 кг\n• Ношение: скрытое/наружное"
    },
    "ciklon": {
        "name": "🌀 Бронежилет Циклон",
        "description": "Специально разработанный детский бронежилет. Защита самого ценного — вашего ребенка.",
        "price": "55 650 руб",
        "category": "Бронежилеты",
        "details": "• Класс защиты: БР 1\n• Вес: до 3 кг"
    },
    "promyshlenny": {
        "name": "🏭 Бронежилет Промышленный",
        "description": "Специализированная защита для охраны промышленных объектов и сотрудников службы безопасности.",
        "price": "63 000 руб",
        "category": "Бронежилеты",
        "details": "• Класс защиты: Бр1\n• Вес: 3 кг\n• Модульность: да\n• Эвакуационная стропа: да"
    },
    "taifun": {
        "name": "🌪️ Бронежилет Тайфун",
        "description": "Идеальный выбор для экипажа боевых машин, водителей и разведчиков. Интегрированная защита ключевых зон.",
        "price": "69 300 руб",
        "category": "Бронежилеты",
        "details": "• Класс защиты: БР1\n• Вес: 3 кг\n• Интегрированная защита шеи\n• Защита аорты\n• Эвакуационная стропа"
    },
    "shtorm": {
        "name": "🌊 Бронежилет Шторм",
        "description": "Ваш надёжный защитник! Всего 4.2 кг веса для полной круговой защиты, включая шею. Система быстрого сброса делает его готовым к любым сценариям.",
        "price": "73 920 руб",
        "category": "Бронежилеты",
        "details": "• Класс защиты: БР1 (без плит)\n• Вес: 4.2 кг\n• Взаимозаменяемые модули под плиты\n• Универсальный карман\n• Эвакуационная стропа\n• Интегрированная защита шеи"
    },
    "zashita_shei": {
        "name": "🦵 Защита Шеи",
        "description": "Критически важная защита уязвимой зоны. Легкая и удобная, не ограничивает обзор и подвижность.",
        "price": "23 100 руб",
        "category": "Доп. защита",
        "details": "• Класс защиты: БР1\n• Вес: 500 г\n• ИК-ремиссия: да"
    },
    "zashita_plech": {
        "name": "💪 Защита Плеч",
        "description": "Надежная бронезащита плечевых суставов. Обеспечивает безопасность, не сковывая движений.",
        "price": "15 750 руб",
        "category": "Доп. защита",
        "details": "• Класс защиты: БР1\n• Вес: 500 г\n• ИК-ремиссия: да"
    },
    "napashnik": {
        "name": "🎽 Напашник Пятиточечник",
        "description": "Удобный и функциональный элемент экипировки, повышающий вашу защищенность и эффективность.",
        "price": "15 750 руб",
        "category": "Экипировка",
        "details": "• Материал: Cordura\n• Цвет: черный, хаки\n• Совместимость: стандартная\n• ИК-ремиссия: да"
    },
    "razgruzochny_poyas": {
        "name": "🦺 Разгрузочный пояс",
        "description": "Профессиональный разгрузочный пояс для тактического снаряжения. Основа вашей боевой экипировки.",
        "price": "23 000 руб",
        "category": "Экипировка",
        "details": "• В комплекте: Напашник Пятиточечник\n• Класс защиты: БР1\n• Вес: 1 кг\n• Ширина: 19 см (поясничная)\n• Кольца: 4 шт\n• ИК-ремиссия: да"
    },
    "poyas_kobura": {
        "name": "🔫 Пояс Кобура",
        "description": "Специализированный пояс для безопасного и удобного ношения оружия. Надежность в каждой детали.",
        "price": "5 250 руб",
        "category": "Экипировка",
        "details": "• Материал: эластичный шнур\n• Подходит: для ПМ, ТТ\n• Регулировка: да\n• Цвет: черный, коричневый"
    },
    "zashita_nog": {
        "name": "🦵 Бронезащита ног",
        "description": "Комплексная защита для ваших ног. Восемь бронемодулей обеспечивают всестороннюю безопасность при максимальной подвижности.",
        "price": "79 800 руб",
        "category": "Доп. защита",
        "details": "• Защита: БР1-2\n• Вес: 2-4 кг\n• Регулировка: по размеру\n• ИК-ремиссия: да"
    },
    "zaryadka_ak": {
        "name": "🔋 Приспособление для снаряжения магазина АК",
        "description": "Существенно ускорьте процесс заряжания магазинов. Простота и надежность в использовании.",
        "price": "1 575 руб",
        "category": "Аксессуары",
        "details": "• Совместимость: Подходит для всех магазинов 5.45×39 мм\n• Материал: пластик+металл\n• Вес: 0.41 кг\n• Цвет: черный\n• ИК-ремиссия: да"
    },
    "ukazatel_miny": {
        "name": "⚠️ Указатель Мины",
        "description": "Яркий и заметный указатель для маркировки минной опасности. Важный элемент обеспечения безопасности периметра.",
        "price": "63 руб",
        "category": "Аксессуары",
        "details": "• Материал: металл, флажок из ПВХ\n• Цвет: красный\n• Высота: 9 см\n• Погодоустойчивость: да"
    },
    "stelki": {
        "name": "👞 Противоосколочные стельки",
        "description": "Защитите свои ноги с комфортом. Ортопедические стельки с противоосколочными свойствами.",
        "price": "5 250 руб",
        "category": "Аксессуары",
        "details": "• Материал: арамид\n• Размеры: 38-46\n• Антибактериальные: да\n• Ортопедические: да\n• Срок службы: 1 год"
    },
    "tacticheskaya_sumka": {
        "name": "🎒 Тактическая сумка-баул",
        "description": "Вместительная и надежная сумка для переноски всего необходимого снаряжения.",
        "price": "6 650 руб",
        "category": "Экипировка",
        "details": "• Объем: 100 л\n• Размеры (ШхГхВ): 79х34х34 см\n• ИК-ремиссия: да"
    },
    "spasatel": {
        "name": "🚑 Классный Спасатель (КОБ)",
        "description": "Профессиональное оборудование для эвакуации раненых в сложных условиях. Надежда в бою.",
        "price": "656 250 руб",
        "category": "Мед. оборудование",
        "details": "• Грузоподъемность: 180 кг\n• Вес: 8.5 кг\n• Материал: алюминий+пластик\n• Складная конструкция: да"
    },
    "nosilki": {
        "name": "🚑 Эвакуационные носилки",
        "description": "Прочные и легкие носилки для быстрой и безопасной эвакуации. Незаменимы в любой операции.",
        "price": "15 750 руб",
        "category": "Мед. оборудование",
        "details": "• Грузоподъемность: 180 кг\n• Вес: 8.5 кг\n• Материал: алюминий+пластик\n• Складная конструкция: да"
    },
    "bronelity": {
        "name": "🛡️ Бронеплиты",
        "description": "Сменные бронеплиты для усиления защиты вашего бронежилета. Разные технологии для ваших задач.",
        "price": "5 500 руб",
        "category": "Комплектующие",
        "details": "• Керамические бронеплиты\n• Металлические бронеплиты (стальные)\n• Комбинированные бронеплиты\n• Полиэтиленовые бронеплиты"
    },
    "bronepaket_plitnik": {
        "name": "📦 Бронепакет Плитник",
        "description": "Универсальный бронепакет для базовой защиты. Надежность и доступность.",
        "price": "22 600 руб",
        "category": "Бронепакеты",
        "details": "• Тип: Плитник\n• Класс защиты: БР1\n• Универсальное применение"
    },
    "bronepaket_shturmovoy": {
        "name": "⚡ Бронепакет Штурмовой",
        "description": "Профессиональный бронепакет для штурмовых операций. Максимальная защита и мобильность.",
        "price": "41 000 руб (48-50), 46 400 руб (52-54), 51 000 руб (56-58)",
        "category": "Бронепакеты",
        "details": "• Тип: Штурмовой\n• Класс защиты: БР1-2\n• Размеры: 48-50, 52-54, 56-58"
    },
    "bronepaket_skryty": {
        "name": "🕶️ Бронепакет Скрытый",
        "description": "Бронепакет для скрытого ношения. Защита, которую не видно, но всегда чувствуется.",
        "price": "25 500 руб (48-50), 29 000 руб (52-54), 33 500 руб (56-58)",
        "category": "Бронепакеты",
        "details": "• Тип: Скрытый\n• Класс защиты: БР1\n• Размеры: 48-50, 52-54, 56-58\n• Для скрытого ношения"
    },
    "bronepaket_tankovy": {
        "name": "🎯 Бронепакет Танковый",
        "description": "Специализированный бронепакет для экипажей боевых машин. Оптимален для работы в ограниченном пространстве.",
        "price": "42 300 руб (48-50), 47 100 руб (52-54), 51 900 руб (56-58)",
        "category": "Бронепакеты",
        "details": "• Тип: Танковый\n• Класс защиты: БР1\n• Размеры: 48-50, 52-54, 56-58\n• Для экипажей боевых машин"
    },
    "napashnik_lepetstkovy": {
        "name": "🎽 Напашник Лепестковый",
        "description": "Усовершенствованный лепестковый напашник для повышенного комфорта и защиты.",
        "price": "10 300 руб",
        "category": "Бронепакеты",
        "details": "• Тип: Лепестковый напашник\n• Конструкция: лепестковая\n• Материал: высокопрочная ткань"
    },
    "pyatitochechnik": {
        "name": "⭐ Пятиточечник",
        "description": "Надежная система крепления и распределения нагрузки. Комфорт при длительном ношении.",
        "price": "8 000 руб",
        "category": "Бронепакеты",
        "details": "• Тип: Пятиточечник\n• Система крепления: 5-точечная\n• Равномерное распределение нагрузки"
    },
    "bronepaket_plechi": {
        "name": "💪 Бронепакет Плечи",
        "description": "Специализированная защита плечевых суставов. Не ограничивает подвижность в бою.",
        "price": "9 700 руб",
        "category": "Бронепакеты",
        "details": "• Тип: Защита плеч\n• Класс защиты: БР1\n• Анатомическая форма"
    },
    "bronepaket_sheya": {
        "name": "🦵 Бронепакет Шея",
        "description": "Критически важная защита шеи. Легкая и эффективная защита уязвимой зоны.",
        "price": "14 600 руб",
        "category": "Бронепакеты",
        "details": "• Тип: Защита шеи\n• Класс защиты: БР1\n• Вес: минимальный"
    },
    "bronepakety": {
        "name": "📦 Бронепакеты",
        "description": "Полный ассортимент бронепакетов для любых задач. От базовой до специализированной защиты.",
        "price": "от 8 000 руб",
        "category": "Комплектующие",
        "details": "• Материал: арамид\n• Различные типы и размеры\n• *Полный каталог бронепакетов смотрите выше*"
    }
}

# Частые вопросы
FAQ = {
    "ballistics": {
        "question": "🛡️ Какая баллистика используется в изделиях?",
        "answer": "Мы используем арамидную ткань (кевлар), но по запросу также можем использовать СВМПЭ. Баллистический пакет запаян в водонепроницаемый чехол."
    },
    "production": {
        "question": "🏭 Где находится производство? Можно приехать примерить, посмотреть?",
        "answer": "Конечно! Адрес офиса: СПб, ул. Маршала Тухачевского 22, БЦ Сова, 2 этаж, офис 216\nАдрес производства: СПб, ул. Львовская д.9"
    },
    "protection_level": {
        "question": "📊 Какая степень защиты у противоосколочного бронепакета?",
        "answer": "В рамках ГОСТ принято считать, что БР1 дает 15-18 слоев кевлара. Мы же устанавливаем 24 слоя, поэтому смело можно считать его усиленным-БР1+"
    },
    "discounts": {
        "question": "💸 Есть ли скидки?",
        "answer": "У нас существует система скидок для общественных организаций, фондов, епархий. Для физических лиц мы можем предоставить персональную скидку, которая рассчитывается индивидуально."
    },
    "weight": {
        "question": "⚖️ Какой вес полного комплекта?",
        "answer": "Вес комплекта зависит от наполнения заказа, в среднем от 7 до 15 кг."
    },
    "sizes": {
        "question": "📏 Есть ли большие размеры?",
        "answer": "Да, у нас свое производство, изделия ручной работы. Все размеры уточняются при консультировании и соответствуют русским стандартам. Шьем от самого маленького до самого большого."
    },
    "delivery": {
        "question": "🚚 Есть ли доставка?",
        "answer": "Мы дарим клиентам бесплатную доставку по всей РФ при заказе от 100 000 рублей"
    },
    "customization": {
        "question": "🎨 Можно ли изменить под индивидуальные потребности?",
        "answer": "Да, мы можем изменить имеющиеся изделия или разработать новое, в зависимости от пожеланий клиента."
    },
    "certificates": {
        "question": "📋 Есть ли сертификаты, протоколы испытаний?",
        "answer": "Да, каждое изделие направляется вместе с документами соответствия (сертификаты, паспорта)"
    },
    "repair": {
        "question": "🔧 Можете ли отремонтировать уже имеющийся бронежилет?",
        "answer": "Да, у нас есть сервисное обслуживание бронезащиты. Мы можем отремонтировать ваш бронежилет, а также в случае необходимости, купленный у нас."
    },
    "vat": {
        "question": "💰 Работаете с НДС или без НДС?",
        "answer": "У нас возможна любая форма оплаты."
    },
    "price": {
        "question": "💎 Почему так дорого?",
        "answer": "Мы используем высококачественные проверенные материалы и фурнитуру. Самые прочные лавсановые нити. Самая большая площадь противоосколочной защиты. Шьем вручную (все швы спрятаны внутрь, что обезопасит клиентов от натирания). Даём большой гарантийный срок и сервис по обслуживанию."
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


# Функция для извлечения числовой цены из строки
def extract_price(price_str):
    try:
        # Убираем "руб" и пробелы, оставляем только цифры
        price_clean = price_str.replace('руб', '').replace(' ', '').strip()
        # Если есть другие символы, берем только первую часть до нецифрового символа
        if not price_clean.isdigit():
            # Ищем первую последовательность цифр
            match = re.search(r'\d+', price_clean)
            if match:
                price_clean = match.group()
        return int(price_clean)
    except (ValueError, AttributeError):
        return 0


# Показ товаров по категориям
async def show_category(query, category_name):
    keyboard = []

    # Находим товары в выбранной категории
    category_products = []
    for product_id, product in PRODUCTS.items():
        if product["category"] == category_name:
            category_products.append((product_id, product))

    # Сортируем товары по цене (используем безопасную функцию)
    category_products.sort(key=lambda x: extract_price(x[1]["price"]))

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

    # Сортируем товары по цене (используем безопасную функцию)
    sorted_products = sorted(PRODUCTS.items(), key=lambda x: extract_price(x[1]["price"]))

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
        "Наша компания специализируется на разработке и производстве бронежилетов для детей, военных, спецподразделений, а также моделей скрытого ношения. Мы тщательно контролируем каждый этап производства, ведь внимание к деталям делает нас лидерами в отрасли. С нашими бронежилетами даже супермену не страшен криптонит \n\n"
        "В своей работе мы используем только высококачественные материалы и новейшее оборудование. Это позволяет нам повышать эффективность производства, снижая временные и финансовые затраты без ущерба для качества. Наши передовые технологии обеспечивают бронежилетам исключительные защитные свойства, удобную посадку и комфорт даже при длительном использовании. Прежде чем попасть на рынок, вся продукция проходит строгие проверки.Наша команда — это опытные профессионалы, работающие в сфере разработки и производства средств индивидуальной защиты более десяти лет. Глубокое знание отраслевых стандартов и потребностей рынка позволяет нам создавать бронежилеты, соответствующие самым высоким требованиям безопасности. С нашими бронежилетами даже супермену не страшен криптонит \n\n"
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
        "📞 Телефон: +78122009264\n+78007773876\n"
        "📧 Email: tkgroupooo@ya.ru\n"
        "🌐 Сайт: https://technokryptonite.ru/\n"
        "📍 Адрес: г. Санкт-Петербург  БЦ «Сова» ул. Маршала Tухачевского 22, офис 216, этаж 2\n\n"
        " Telegram оператор: https://t.me/tk_operator\n"
        " Vk сообщество: https://vk.com/tk__group\n"
        " Telegram сообщество: https://t.me/tk_group\n"
        " Vk сообщество швейного производства : https://vk.com/tk_operator\n"
        " Vk личная страница  Виталия Невмержицкого: https://vk.com/vitnev\n"
        " Vk деловое сообщество Виталия Невмержицкого: https://vk.com/tkvitnev\n"
        "⏰ Время работы: Пн-Пт 9:00-18:00\n"
        "🚚 Доставка: 1-3 рабочих дня"
    )


# Оформление заказа
async def buy_now(query):
    await query.edit_message_text(
        "🛒 Для оформления заказа:\n\n"
        "📞 Позвоните: +78122009264\n+78007773876\n"
        "📧 Напишите: tkgroupooo@ya.ru\n"
        "💬 Или напишите нам в WhatsApp/Telegram\n\n"
        "При заказе укажите:\n"
        "• Название товара\n"
        "• Количество\n"
        "• Адрес доставки\n"
        "• Контактные данные\n\n"
        "📦 Доставим за 1-3 дня по всей России!"
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


# Обработка инлайн кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    logger.info(f"Button pressed: {data}")

    try:
        if data.startswith("product_"):
            product_id = data[8:]
            await show_product(query, product_id)
        elif data.startswith("category_"):
            category_name = data[9:]
            await show_category(query, category_name)
        elif data.startswith("faq_"):
            faq_id = data[4:]
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

        details = product.get("details", "• Информация уточняется у менеджера\n• Все характеристики соответствуют ГОСТ")

        text = (
            f"{product['name']}\n\n"
            f"{product['description']}\n\n"
            f"📂 Категория: {product['category']}\n"
            f"💰 Цена: {product['price']}\n\n"
            f"📋 Характеристики:\n{details}\n\n"
            "✅ В наличии на складе\n"
            "✅ Доставка 1-3 дня\n"
            "✅ Гарантия 60 месяцев\n"
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
                "🛒 Для оформления заказа свяжитесь с нами:\n"
                "📞 +78122009264\n+78007773876\n"
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
    if not BOT_TOKEN:
        print("❌ ОШИБКА: BOT_TOKEN не найден!")
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
