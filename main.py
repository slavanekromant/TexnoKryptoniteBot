import logging
import os
import re
import uuid
from typing import Any, Dict

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      KeyboardButton, ReplyKeyboardMarkup, Update)
from telegram.ext import (Application, CallbackQueryHandler, CommandHandler,
                          ContextTypes, ConversationHandler, MessageHandler,
                          filters)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния для ConversationHandler
COLOR, SIZE, PHONE, NAME, ADDRESS, CONFIRM_ORDER = range(6)


# Конфигурация через Pydantic
class Settings(BaseSettings):
    """Конфигурация приложения через Pydantic"""

    bot_token: str = Field(..., validation_alias="BOT_TOKEN")

    model_config = SettingsConfigDict(
        # env_file='.env',
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Инициализация конфигурации
try:
    settings = Settings()
    BOT_TOKEN = settings.bot_token
    logger.info("Конфигурация успешно загружена")
except Exception as e:
    logger.error(f"Ошибка загрузки конфигурации: {e}")
    # Fallback на переменные окружения
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не найден в конфигурации или переменных окружения")
        raise ValueError("BOT_TOKEN не найден. Создайте файл .env с BOT_TOKEN=ваш_токен")

# Данные о товарах (сокращено для примера)
PRODUCTS = {
    "komplekt_protivooskolochny": {
        "name": "🛡️ Комплект Противоосколочный",
        "description": "Полный комплект противоосколочной защиты для максимальной безопасности в условиях повышенного риска. Включает бронежилет, шлем и защиту конечностей.",
        "price": "199 500 руб",
        "category": "Комплекты",
        "details": "• Комплектация:\nБронешлем БР2 степени защиты\nБронежилет «Тайфун» с интегрированной защитой шеи\nЗащита плеч\nНапашник (увеличенный, лепестковый)\nПятиточечник (увеличенный, двойной)\nРазгрузочно-поясная система (РПС) с баллистической защитой, каркасом и подтяжками\nБронезащита ног (модели бедер и голени)\nПротивогрязевые гамаши\nКомплект документов\nСумка-переноска",
        "image": "images/comprotivooskoloch.webp",
    },
    "komplekt_shturmovoy": {
        "name": "⚡ Комплект Штурмовой",
        "description": "Профессиональный набор для спецподразделений, идеально подходящий для операций любой сложности.",
        "price": "210 000 руб",
        "category": "Комплекты",
        "details": "• Состав комплекта:\nБронешлем БР2\nЗащита шеи\nЗащита плеч\nБронежилет «Шторм» с круговой баллистикой и системой КАП\nВзаимозаменяемые модули под плиты\nРазгрузочно-поясная система (РПС) с баллистической защитой, каркасом и подтяжками\nНапашник (увеличенный, лепестковый)\nПятиточечник (увеличенный, двойной)\nБронезащита для ног (модули на бедра и голени)\nПротивогрязевые гамаши\nПлиты бронезащиты от БР3 до БР5 (сталь, керамика, оксид алюминия)\nКомплект документов (сертификат, паспорт)\nСумка для переноски",
        "image": "images/comshturm.webp",
    },
    "podarochny_sertifikat": {
        "name": "🎁 Подарочный Сертификат",
        "description": "Идеальное решение для тех, кто ценит безопасность. Подарите возможность выбора защитной экипировки.",
        "price": "100 000 руб",
        "category": "Сертификаты",
        "details": "• Номинал: 100 000 руб\n• Срок действия: 1 год\n• Можно комбинировать с другими покупками\n• Электронный или бумажный формат",
        "image": "images/podarok.webp",
    },
    "purga": {
        "name": "❄️ Бронежилет Пурга",
        "description": "Ваш надежный защитник в экстремальных условиях. Легкость и максимальная защита — вот что делает этот бронежилет незаменимым.",
        "price": "23 100 руб / 45 500 руб (без/с баллистикой)",
        "category": "Бронежилеты",
        "details": "• Класс защиты: БР 1\n• Вес: 3.3 кг\n• Система быстрого сброса: да\n• Увеличенная площадь защиты: да\n• Универсальный карман под плиты: да\n• Модульная передняя панель: да\n• ИК-ремиссия: да\n• Эвакуационная стропа: да",
        "image": "images/purga.webp",
    },
    "mirazh": {
        "name": "🌫️ Бронежилет Мираж",
        "description": "Легкий и маневренный бронежилет, созданный для максимальной защиты и комфорта. Идеально подходит для скрытого ношения.",
        "price": "39 900 руб",
        "category": "Бронежилеты",
        "details": "• Класс защиты: Бр1-2\n• Вес: 2.5-3 кг\n• Ношение: скрытое/наружное\n• Разгружает спину при длительном использовании\n• Обеспечивает надежную защиту благодаря современным материалам",
        "image": "images/mirash.webp",
    },
    "ciklon": {
        "name": "🌀 Бронежилет Циклон",
        "description": "Детский бронежилет класса Бр1, созданный совместно с врачами. Это не просто защита, это забота о вашем ребенке.",
        "price": "55 650 руб",
        "category": "Бронежилеты",
        "details": "• Класс защиты: БР 1\n• Вес: до 3 кг\n• Светоотражающие элементы: да\n• Клапан-компенсатор: да\n• Карман для маячка: да\n• Эвакуационная стропа: да\n• Создан совместно с врачами: да",
        "image": "images/zhiklon.webp",
    },
    "promyshlenny": {
        "name": "🏭 Бронежилет Промышленный",
        "description": "Специализированный бронежилет для охраны промышленных объектов и предприятий. Защитите своих сотрудников с надежной бронеодеждой!",
        "price": "63 000 руб",
        "category": "Бронежилеты",
        "details": "• Класс защиты: Бр1\n• Вес: 3 кг\n• Модульность: да\n• Эвакуационная стропа: да\n• Фиксаторы для инструмента: да\n• Атрибутика и цвет компании: по запросу\n• Дышащий материал: да\n• Крепление для инструментов и дополнительного снаряжения: да",
        "image": "images/promshlenn.webp",
    },
    "taifun": {
        "name": "🌪️ Бронежилет Тайфун",
        "description": "Идеальный выбор для экипажа боевых машин, сотрудников штаба, водителей и разведчиков. Ваш надежный спутник в любой ситуации!",
        "price": "69 300 руб",
        "category": "Бронежилеты",
        "details": "• Класс защиты: БР1\n• Вес: 3 кг\n• Модульность: да\n• Эвакуационная стропа: да\n• ИК-ремиссия: да\n• Фиксатор тангенты/гарнитуры: да\n• Защита шеи: да\n• Защита аорты: да\n• Увеличенная защита области ребер: да",
        "image": "images/taifun.webp",
    },
    "shtorm": {
        "name": "🌊 Бронежилет Шторм",
        "description": "Ваш надёжный защитник! Всего 4.2 кг веса для полной круговой защиты, включая шею и защиту от фугасов. Готовьтесь к любым вызовам!",
        "price": "73 920 руб",
        "category": "Бронежилеты",
        "details": "• Класс защиты: БР1\n• Вес: 4.2 кг\n• Взаимозаменяемые модули под плиты: да\n• Универсальный карман для бронеплит: да\n• Эвакуационная стропа: да\n• Интегрированная защита шеи: да\n• ИК-ремиссия: да\n• Боевая рубаха: да",
        "image": "images/shtorm.webp",
    },
    "zashita_shei": {
        "name": "🦵 Защита Шеи",
        "description": "Критически важная защита уязвимой зоны. Легкая и удобная, не ограничивает обзор и подвижность.",
        "price": "23 100 руб",
        "category": "Доп. защита",
        "details": "• Класс защиты: БР1\n• Вес: 1,5 кг\n• ИК-ремиссия: да\n• Возможность регулировки: да\n• Передний съемный модуль: да",
        "image": "images/bronneck.webp",
    },
    "zashita_plech": {
        "name": "💪 Защита Плеч",
        "description": "Надежная бронезащита плечевых суставов. Обеспечивает безопасность, не сковывая движений.",
        "price": "15 750 руб",
        "category": "Доп. защита",
        "details": "• Класс защиты: БР1\n• Вес: 1 кг\n• ИК-ремиссия: да\n• Удобная фиксация: да\n• Быстрый съем: да",
        "image": "images/bronplech.webp",
    },
    "napashnik": {
        "name": "🎽 Напашник Пятиточечник",
        "description": "Удобный и функциональный элемент экипировки, повышающий вашу защищенность и эффективность.",
        "price": "15 750 руб",
        "category": "Экипировка",
        "details": "• Материал: Cordura\n• Защита: БР1\n• Совместимость: полная (не конфликтует)\n• ИК-ремиссия: да",
        "image": "images/hui.webp",
    },
    "razgruzochny_poyas": {
        "name": "🦺 Разгрузочный пояс",
        "description": "Тактический разгрузочный пояс — ключевой элемент вашей боевой экипировки.",
        "price": "23 000 руб",
        "category": "Экипировка",
        "details": "• Класс защиты: БР1\n• Вес: 1 кг\n• Каркасная конструкция: да\n• Возможность регулировки: да\n• Амортизационный элемент: да\n• Возможность установки плит: да\n• Ширина: 19 см (на уровне поясничного отдела)\n• ИК-ремиссия: да",
        "image": "images/rasgrusohnpoys.webp",
    },
    "poyas_kobura": {
        "name": "🔫 Пояс Кобура",
        "description": "Специализированный пояс для безопасного и удобного ношения оружия. Надежность в каждой детали.",
        "price": "5 250 руб",
        "category": "Экипировка",
        "details": "• Материал: эластичный шнур\n• Подходит: для ПМ, ТТ\n• Регулировка: да\n• Цвет: черный, коричневый",
        "image": "images/poyskob.webp",
    },
    "zashita_nog": {
        "name": "🦵 Бронезащита ног",
        "description": "Комплексная защита для ваших ног. Восемь бронемодулей обеспечивают всестороннюю безопасность при максимальной подвижности.",
        "price": "79 800 руб",
        "category": "Доп. защита",
        "details": "• Защита: БР1-2\n• Вес: 2-4 кг\n• Регулировка: по размеру\n• ИК-ремиссия: да\n• Не сковывает движение: да\n• Быстрый сброс: да",
        "image": "images/bronnog.webp",
    },
    "zaryadka_ak": {
        "name": "🔋 Приспособление для снаряжения магазина АК",
        "description": "Ускоряет процесс заряжания магазинов в два раза! Быстрая и удобная зарядка магазинов.",
        "price": "1 575 руб",
        "category": "Аксессуары",
        "details": "• Совместимость: Подходит для всех магазинов 5.45×39 мм\n• Материал: пластик+металл\n• Вес: 0.41 кг\n• Цвет: черный",
        "image": "images/zarak.webp",
    },
    "ukazatel_miny": {
        "name": "⚠️ Указатель Мины",
        "description": "Специализированный указатель минной опасности. Яркий и заметный. Обеспечивает высокую видимость и устойчивость к неблагоприятным погодным условиям.",
        "price": "63 руб",
        "category": "Аксессуары",
        "details": "• Материал: металл и ПВХ\n• Цвет: красный\n• Высота: от 9 см\n• Погодоустойчивость: да",
        "image": "images/min.webp",
    },
    "stelki": {
        "name": "👞 Противоосколочные стельки",
        "description": "Защитите свои ноги с комфортом. Ортопедические стельки с противоосколочными свойствами.",
        "price": "5 250 руб",
        "category": "Аксессуары",
        "details": "• Материал: арамид\n• Размеры: 38-46\n• Антибактериальные: да\n• Ортопедические: да\n• Срок службы: 1 год",
        "image": "images/steliki.jpg",
    },
    "tacticheskaya_sumka": {
        "name": "🎒 Тактическая сумка-баул",
        "description": "Вместительная и надежная сумка для переноски всего необходимого снаряжения.",
        "price": "6 650 руб",
        "category": "Экипировка",
        "details": "• Объем: 100 л\n• Размеры (ШхГхВ): 79х34х34 см\n• ИК-ремиссия: да",
        "image": "images/taktsumbayl.jpg",
    },
    "spasatel": {
        "name": "🚑 Спасатель (КОБ)",
        "description": "Надежное оборудование для эвакуации раненых в сложных условиях.",
        "price": "656 250 руб",
        "category": "Мед. оборудование",
        "details": "• Металлический шкаф с необходимым снаряжением:\n* Бронежилеты классов БР2 С2\n* Фонари\n* Термоодеяла\n* Свистки\n* Маски для защиты органов дыхания\n* Комплексная аптечка\n* Трос-самоспасатель\n* Складные бескаркасные носилки",
        "image": "images/KOB.webp",
    },
    "nosilki": {
        "name": "🚑 Эвакуационные носилки",
        "description": "Удобные эвакуационные носилки. Легкие и прочные для быстрой и безопасной транспортировки. Незаменимы при любых чрезвычайных ситуациях.",
        "price": "15 750 руб",
        "category": "Мед. оборудование",
        "details": "• Грузоподъемность: 180 кг\n• Вес: менее 3 кг\n• 4 точки крепления для фиксации пациента\n• Возможность крепления в автомобиле\n• Компактный чехол-тубус\n• Складная конструкция",
        "image": "images/nosilki.webp",
    },
    "bronelity": {
        "name": "🛡️ Бронеплиты",
        "description": "Сменные бронеплиты для усиления защиты вашего бронежилета. Разные технологии для ваших задач.",
        "price": "от 5 500 руб",
        "category": "Комплектующие",
        "details": "• Керамические бронеплиты\n• Металлические бронеплиты (стальные)\n• Комбинированные бронеплиты\n• Бронеплиты СВМПЭ",
        "image": "images/broneplit.webp",
    },
}
# Частые вопросы (остались без изменений)
FAQ = {
    "ballistics": {
        "question": "🛡️ Какая баллистика используется в изделиях?",
        "answer": "Мы используем арамидную ткань (кевлар), но по запросу также можем использовать СВМПЭ. Баллистический пакет запаян в водонепроницаемый чехол.",
    },
    "production": {
        "question": "🏭 Где находится производство? Можно приехать примерить, посмотреть?",
        "answer": "Конечно! Адрес офиса: СПб, ул. Маршала Тухачевского 22, БЦ Сова, 2 этаж, офис 216\nАдрес производства: СПб, ул. Львовская д.9",
    },
    "protection_level": {
        "question": "📊 Какая степень защиты у противоосколочного бронепакета?",
        "answer": "В рамках ГОСТ принято считать, что БР1 дает 15-18 слоев кевлара. Мы же устанавливаем 24 слоя, поэтому смело можно считать его усиленным-БР1+",
    },
    "discounts": {
        "question": "💸 Есть ли скидки?",
        "answer": "У нас существует система скидок для общественных организаций, фондов, епархий. Для физических лиц мы можем предоставить персональную скидку, которая рассчитывается индивидуально.",
    },
    "weight": {
        "question": "⚖️ Какой вес полного комплекта?",
        "answer": "Вес комплекта зависит от наполнения заказа, в среднем от 7 до 15 кг.",
    },
    "sizes": {
        "question": "📏 Есть ли большие размеры?",
        "answer": "Да, у нас свое производство, изделия ручной работы. Все размеры уточняются при консультировании и соответствуют русским стандартам. Шьем от самого маленького до самого большого.",
    },
    "delivery": {
        "question": "🚚 Есть ли доставка?",
        "answer": "Мы дарим клиентам бесплатную доставку по всей РФ при заказе от 100 000 рублей",
    },
    "customization": {
        "question": "🎨 Можно ли изменить под индивидуальные потребности?",
        "answer": "Да, мы можем изменить имеющиеся изделия или разработать новое, в зависимости от пожеланий клиента.",
    },
    "certificates": {
        "question": "📋 Есть ли сертификаты, протоколы испытаний?",
        "answer": "Да, каждое изделие направляется вместе с документами соответствия (сертификаты, паспорта)",
    },
    "repair": {
        "question": "🔧 Можете ли отремонтировать уже имеющийся бронежилет?",
        "answer": "Да, у нас есть сервисное обслуживание бронезащиты. Мы можем отремонтировать ваш бронежилет, а также в случае необходимости, купленный у нас.",
    },
    "vat": {
        "question": "💰 Работаете с НДС или без НДС?",
        "answer": "У нас возможна любая форма оплаты.",
    },
    "price": {
        "question": "💎 Почему так дорого?",
        "answer": "Мы используем высококачественные проверенные материалы и фурнитуру. Самые прочные лавсановые нити. Самая большая площадь противоосколочной защиты. Шьем вручную (все швы спрятаны внутрь, что обезопасит клиентов от натирания). Даём большой гарантийный срок и сервис по обслуживанию.",
    },
}

# Хранилище корзин пользователей
user_carts: Dict[int, "Cart"] = {}

# Хранилище заказов
user_orders: Dict[str, Dict[str, Any]] = {}


class Cart:
    def __init__(self):
        self.items: Dict[str, int] = {}

    def add_item(self, product_id: str, quantity: int = 1):
        if product_id in self.items:
            self.items[product_id] += quantity
        else:
            self.items[product_id] = quantity

    def remove_item(self, product_id: str, quantity: int = 1):
        if product_id in self.items:
            if self.items[product_id] <= quantity:
                del self.items[product_id]
            else:
                self.items[product_id] -= quantity

    def clear(self):
        self.items.clear()

    def get_total_price(self) -> int:
        total = 0
        for product_id, quantity in self.items.items():
            if product_id in PRODUCTS:
                price_str = PRODUCTS[product_id]["price"]
                price = extract_price(price_str)
                total += price * quantity
        return total

    def get_items_details(self) -> list:
        items_details = []
        for product_id, quantity in self.items.items():
            if product_id in PRODUCTS:
                product = PRODUCTS[product_id]
                price = extract_price(product["price"])
                items_details.append(
                    {
                        "name": product["name"],
                        "quantity": quantity,
                        "price": price,
                        "total": price * quantity,
                    }
                )
        return items_details


# Функция для извлечения числовой цены из строки
def extract_price(price_str: str) -> int:
    try:
        # Убираем "руб" и пробелы, оставляем только цифры
        price_clean = price_str.replace("руб", "").replace(" ", "").strip()
        # Если есть другие символы, берем только первую часть до нецифрового символа
        if not price_clean.isdigit():
            # Ищем первую последовательность цифр
            match = re.search(r"\d+", price_clean)
            if match:
                price_clean = match.group()
        return int(price_clean)
    except (ValueError, AttributeError):
        return 0


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"User {update.effective_user.id} started the bot")

    # Инициализация корзины для пользователя
    user_id = update.effective_user.id
    if user_id not in user_carts:
        user_carts[user_id] = Cart()

    keyboard = [
        [KeyboardButton("🛍️ Каталог товаров"), KeyboardButton("❓ Частые вопросы")],
        [KeyboardButton("ℹ️ О компании"), KeyboardButton("📞 Контакты")],
        [KeyboardButton("🔥 Топ товары"), KeyboardButton("🛒 Корзина")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "🛡️ Добро пожаловать в магазин защитной экипировки и бронежилетов!\n\n"
        "Мы предлагаем полный спектр средств защиты для вашей безопасности.\n\n"
        "Выберите действие:",
        reply_markup=reply_markup,
    )


# Показ корзины
async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    if user_id not in user_carts or not user_carts[user_id].items:
        await update.message.reply_text("🛒 Ваша корзина пуста")
        return

    cart = user_carts[user_id]
    items_details = cart.get_items_details()

    message = "🛒 Ваша корзина:\n\n"
    total = 0

    for item in items_details:
        message += f"{item['name']}\n"
        message += (
            f"Количество: {item['quantity']} × {item['price']:,} руб = {item['total']:,} руб\n\n"
        )
        total += item["total"]

    message += f"💎 Общая сумма: {total:,} руб"

    keyboard = [
        [InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout")],
        [InlineKeyboardButton("🗑️ Очистить корзину", callback_data="clear_cart")],
        [InlineKeyboardButton("🛍️ Продолжить покупки", callback_data="back_to_catalog")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(message, reply_markup=reply_markup)


# Добавление товара в корзину
async def add_to_cart_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    product_id = query.data.replace("add_to_cart_", "")

    if user_id not in user_carts:
        user_carts[user_id] = Cart()

    user_carts[user_id].add_item(product_id)

    product = PRODUCTS[product_id]
    await query.message.reply_text(f"✅ {product['name']} добавлен в корзину!")


# Начало оформления заказа из callback
async def start_checkout_from_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    user_id = query.from_user.id

    if user_id not in user_carts or not user_carts[user_id].items:
        await query.message.reply_text("❌ Ваша корзина пуста")
        return ConversationHandler.END

    await ask_color_from_callback(query, context)
    return COLOR


# Спрашиваем цвет из callback
async def ask_color_from_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Черный", callback_data="color_black")],
        [InlineKeyboardButton("Хаки", callback_data="color_khaki")],
        [InlineKeyboardButton("Оливковый", callback_data="color_olive")],
        [InlineKeyboardButton("Отменить", callback_data="cancel_order")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("🎨 Выберите цвет товара:", reply_markup=reply_markup)


# Спрашиваем размер
async def ask_size(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    color = query.data.replace("color_", "")
    context.user_data["color"] = color

    keyboard = [
        [
            InlineKeyboardButton("S", callback_data="size_S"),
            InlineKeyboardButton("M", callback_data="size_M"),
        ],
        [
            InlineKeyboardButton("L", callback_data="size_L"),
            InlineKeyboardButton("XL", callback_data="size_XL"),
        ],
        [InlineKeyboardButton("XXL", callback_data="size_XXL")],
        [
            InlineKeyboardButton("Назад", callback_data="back_to_color"),
            InlineKeyboardButton("Отменить", callback_data="cancel_order"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("📏 Выберите размер:", reply_markup=reply_markup)
    return SIZE


# Спрашиваем номер телефона
async def ask_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    size = query.data.replace("size_", "")
    context.user_data["size"] = size

    keyboard = [[InlineKeyboardButton("Отменить", callback_data="cancel_order")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "📞 Введите номер телефона для связи:\n\nПример: +79123456789 или 89123456789",
        reply_markup=reply_markup,
    )
    return PHONE


# Спрашиваем ФИО
async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    phone = update.message.text
    # Простая валидация номера телефона
    cleaned_phone = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not re.match(r"^(\+7|8)\d{10}$", cleaned_phone):
        await update.message.reply_text("❌ Неверный формат номера. Попробуйте еще раз:")
        return PHONE

    context.user_data["phone"] = cleaned_phone

    await update.message.reply_text(
        "👤 Введите ваше ФИО или имя:\n\nПример: Иванов Иван Иванович или Иван"
    )
    return NAME


# Спрашиваем адрес доставки
async def ask_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text
    if len(name) < 2:
        await update.message.reply_text("❌ Имя слишком короткое. Введите еще раз:")
        return NAME

    context.user_data["name"] = name

    await update.message.reply_text(
        "🏠 Введите адрес доставки:\n\nПример: г. Москва, ул. Ленина, д. 1, кв. 1"
    )
    return ADDRESS


# Подтверждение заказа
async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    address = update.message.text
    if len(address) < 10:
        await update.message.reply_text("❌ Адрес слишком короткий. Введите еще раз:")
        return ADDRESS

    context.user_data["address"] = address

    # Формируем информацию о заказе
    user_id = update.effective_user.id
    cart = user_carts[user_id]
    items_details = cart.get_items_details()

    order_summary = "📋 Подтверждение заказа:\n\n"
    order_summary += "🛒 Состав заказа:\n"

    for item in items_details:
        order_summary += f"• {item['name']} × {item['quantity']} = {item['total']:,} руб\n"

    order_summary += f"\n💎 Итого: {cart.get_total_price():,} руб\n\n"
    order_summary += "📝 Данные для доставки:\n"
    order_summary += f"🎨 Цвет: {context.user_data['color']}\n"
    order_summary += f"📏 Размер: {context.user_data['size']}\n"
    order_summary += f"📞 Телефон: {context.user_data['phone']}\n"
    order_summary += f"👤 ФИО: {context.user_data['name']}\n"
    order_summary += f"🏠 Адрес: {context.user_data['address']}\n\n"
    order_summary += "Подтверждаете заказ?"

    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить заказ", callback_data="final_confirm")],
        [InlineKeyboardButton("✏️ Изменить данные", callback_data="change_data")],
        [InlineKeyboardButton("❌ Отменить заказ", callback_data="cancel_order")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(order_summary, reply_markup=reply_markup)
    return CONFIRM_ORDER


# Отправка заказа администратору
async def send_order_to_admin(
    context: ContextTypes.DEFAULT_TYPE,
    order_id: str,
    order_data: Dict[str, Any],
    user_info: Dict[str, Any],
) -> bool:
    try:
        # Формируем сообщение для администратора
        admin_message = f"🆕 НОВЫЙ ЗАКАЗ #{order_id}\n\n"
        admin_message += f"👤 Пользователь: @{user_info['username']} (ID: {user_info['id']})\n"
        admin_message += f"📞 Телефон: {order_data['phone']}\n"
        admin_message += f"👤 ФИО: {order_data['name']}\n\n"

        admin_message += "🛒 Состав заказа:\n"
        for item in order_data["items_details"]:
            admin_message += f"• {item['name']} × {item['quantity']} = {item['total']:,} руб\n"

        admin_message += f"\n💎 Сумма заказа: {order_data['total_amount']:,} руб\n\n"
        admin_message += "📝 Данные доставки:\n"
        admin_message += f"🎨 Цвет: {order_data['color']}\n"
        admin_message += f"📏 Размер: {order_data['size']}\n"
        admin_message += f"🏠 Адрес: {order_data['address']}\n\n"
        admin_message += f"🆔 ID заказа: {order_id}"

        # ЗАМЕНИТЕ ЭТОТ CHAT_ID НА ВАШ РЕАЛЬНЫЙ CHAT ID
        ADMIN_CHAT_ID = 903065504  # Замените на ваш Chat ID

        # Отправляем сообщение по Chat ID
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_message)

        logger.info(f"Заказ #{order_id} отправлен администратору (Chat ID: {ADMIN_CHAT_ID})")
        return True

    except Exception as e:
        logger.error(f"Ошибка отправки заказа администратору: {e}")
        return False


# Завершение заказа и отправка QR-кода
async def complete_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not in user_carts or not user_carts[user_id].items:
        await query.edit_message_text("❌ Ошибка: корзина пуста")
        return ConversationHandler.END

    # Создаем заказ
    order_id = str(uuid.uuid4())[:8].upper()
    cart = user_carts[user_id]
    total_amount = cart.get_total_price()
    items_details = cart.get_items_details()

    # Сохраняем заказ
    order_data = {
        "user_id": user_id,
        "items": cart.items.copy(),
        "items_details": items_details,
        "color": context.user_data["color"],
        "size": context.user_data["size"],
        "phone": context.user_data["phone"],
        "name": context.user_data["name"],
        "address": context.user_data["address"],
        "total_amount": total_amount,
        "status": "pending",
    }

    user_orders[order_id] = order_data

    # Отправляем заказ администратору
    user_info = {"id": user_id, "username": query.from_user.username or "Не указан"}

    # Передаем context для отправки сообщения
    await send_order_to_admin(context, order_id, order_data, user_info)

    # Формируем сообщение с деталями заказа для пользователя
    order_message = f"✅ Заказ #{order_id} оформлен!\n\n"
    order_message += "🛒 Состав заказа:\n"

    for item in items_details:
        order_message += f"• {item['name']} × {item['quantity']} = {item['total']:,} руб\n"

    order_message += f"\n💎 К оплате: {total_amount:,} руб\n\n"
    order_message += "📝 Данные доставки:\n"
    order_message += f"🎨 Цвет: {context.user_data['color']}\n"
    order_message += f"📏 Размер: {context.user_data['size']}\n"
    order_message += f"📞 Телефон: {context.user_data['phone']}\n"
    order_message += f"👤 ФИО: {context.user_data['name']}\n"
    order_message += f"🏠 Адрес: {context.user_data['address']}\n\n"
    order_message += "💳 Выберите способ оплаты:"

    keyboard = [
        [InlineKeyboardButton("💳 Оплатить картой", callback_data=f"pay_card_{order_id}")],
        [InlineKeyboardButton("📱 Оплатить по QR-коду", callback_data=f"pay_qr_{order_id}")],
        [InlineKeyboardButton("📞 Связаться для оплаты", url="https://t.me/tk_operator")],
        [InlineKeyboardButton("🛍️ Вернуться в каталог", callback_data="back_to_catalog")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(order_message, reply_markup=reply_markup)

    # Очищаем корзину
    cart.clear()

    # Очищаем данные пользователя
    context.user_data.clear()

    return ConversationHandler.END


# Показ QR-кода для оплаты
async def show_qr_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    order_id = query.data.replace("pay_qr_", "")

    if order_id not in user_orders:
        await query.edit_message_text("❌ Заказ не найден")
        return

    order = user_orders[order_id]

    # Сохраняем order_id в context для использования в callback
    context.user_data["current_order_id"] = order_id

    # Проверяем наличие QR-кода
    qr_code_path = "images/qr.png"
    if os.path.exists(qr_code_path):
        try:
            with open(qr_code_path, "rb") as photo:
                caption = (
                    f"📱 QR-код для оплаты заказа #{order_id}\n\n"
                    f"💎 Сумма к оплате: {order['total_amount']:,} руб\n\n"
                    f"После оплаты нажмите кнопку '✅ Я оплатил(а)'"
                )

                keyboard = [
                    [InlineKeyboardButton("✅ Я оплатил(а)", callback_data=f"paid_{order_id}")],
                    [
                        InlineKeyboardButton(
                            "📞 Связаться с оператором", url="https://t.me/tk_operator"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🛍️ Вернуться в каталог", callback_data="back_to_catalog"
                        )
                    ],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                # Отправляем новое сообщение с фото
                await query.message.reply_photo(
                    photo=photo, caption=caption, reply_markup=reply_markup
                )
                # Удаляем предыдущее сообщение с выбором оплаты
                try:
                    await query.delete_message()
                except:
                    pass  # Игнорируем ошибку удаления сообщения

        except Exception as e:
            logger.error(f"Ошибка отправки QR-кода: {e}")
            # Если не удалось отправить фото, показываем текстовую версию
            await show_qr_code_fallback(query, order_id, order)
    else:
        # Если QR-код не найден
        await show_qr_code_fallback(query, order_id, order)


# Фолбэк для случая когда QR-код недоступен
async def show_qr_code_fallback(query, order_id: str, order: Dict[str, Any]) -> None:
    keyboard = [
        [InlineKeyboardButton("✅ Я оплатил(а)", callback_data=f"paid_{order_id}")],
        [InlineKeyboardButton("📞 Связаться с оператором", url="https://t.me/tk_operator")],
        [InlineKeyboardButton("💳 Оплатить картой", callback_data=f"pay_card_{order_id}")],
        [InlineKeyboardButton("🛍️ Вернуться в каталог", callback_data="back_to_catalog")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"❌ QR-код временно недоступен\n\n"
        f"Для оплаты заказа #{order_id}:\n"
        f"💎 Сумма к оплате: {order['total_amount']:,} руб\n\n"
        f"Реквизиты для перевода:\n"
        f"• Банк: ТК-Банк\n"
        f"• Счет: 0000 0000 0000 0000\n"
        f"• Получатель: ТК Групп\n\n"
        f"После оплаты нажмите кнопку '✅ Я оплатил(а)'",
        reply_markup=reply_markup,
    )


# Обработка оплаты картой
async def pay_by_card(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    order_id = query.data.replace("pay_card_", "")

    if order_id not in user_orders:
        await query.message.reply_text("❌ Заказ не найден")
        return

    order = user_orders[order_id]

    card_payment_message = (
        f"💳 Оплата картой для заказа #{order_id}\n\n"
        f"💎 Сумма к оплате: {order['total_amount']:,} руб\n\n"
        f"Реквизиты для оплаты:\n"
        f"• Номер карты: 0000 0000 0000 0000\n"
        f"• Получатель: ТК Групп\n"
        f"• Банк: ТК-Банк\n\n"
        f"📝 В комментарии к платежу укажите:\n"
        f"   'Заказ #{order_id}'\n\n"
        f"После оплаты нажмите кнопку '✅ Я оплатил(а)' или свяжитесь с оператором"
    )

    keyboard = [
        [InlineKeyboardButton("✅ Я оплатил(а)", callback_data=f"paid_{order_id}")],
        [InlineKeyboardButton("📞 Связаться с оператором", url="https://t.me/tk_operator")],
        [InlineKeyboardButton("📱 Оплатить по QR-коду", callback_data=f"pay_qr_{order_id}")],
        [InlineKeyboardButton("🛍️ Вернуться в каталог", callback_data="back_to_catalog")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(card_payment_message, reply_markup=reply_markup)


# Подтверждение оплаты
async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    order_id = query.data.replace("paid_", "")
    logger.info(f"Confirming payment for order {order_id}")

    if order_id not in user_orders:
        logger.error(f"Order {order_id} not found in user_orders")
        await query.edit_message_text("❌ Заказ не найден")
        return

    # Обновляем статус заказа
    user_orders[order_id]["status"] = "payment_pending"
    logger.info(f"Order {order_id} status updated to payment_pending")

    payment_confirmation = (
        f"✅ Спасибо! Ваша оплата по заказу #{order_id} принята к проверке.\n\n"
        f"📞 Наш оператор свяжется с вами в течение 15 минут для подтверждения оплаты "
        f"и уточнения деталей доставки.\n\n"
        f"Если у вас есть вопросы, вы можете связаться с нами:\n"
        f"📞 +78122009264\n"
        f"💬 @tk_operator\n\n"
        f"Благодарим за заказ! 🛡️"
    )

    keyboard = [
        [InlineKeyboardButton("📞 Связаться с оператором", url="https://t.me/tk_operator")],
        [InlineKeyboardButton("🛍️ Продолжить покупки", callback_data="back_to_catalog")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(payment_confirmation, reply_markup=reply_markup)
        logger.info(f"Payment confirmation sent for order {order_id}")
    except Exception as e:
        logger.error(f"Error editing message for payment confirmation: {e}")
        # Fallback: отправляем новое сообщение
        await query.message.reply_text(payment_confirmation, reply_markup=reply_markup)


# Отмена заказа
async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # Очищаем данные пользователя
    if context.user_data:
        context.user_data.clear()

    await query.edit_message_text("❌ Заказ отменен")
    return ConversationHandler.END


# Очистка корзины
async def clear_cart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id in user_carts:
        user_carts[user_id].clear()

    await query.edit_message_text("🗑️ Корзина очищена")


# Назад к выбору цвета
async def back_to_color(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    await ask_color_from_callback(query, context)
    return COLOR


# Изменение данных заказа
async def change_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    await ask_color_from_callback(query, context)
    return COLOR


# Показ каталога товаров
async def show_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        keyboard.append(
            [InlineKeyboardButton(f"📂 {category}", callback_data=f"category_{category}")]
        )

    keyboard.append([InlineKeyboardButton("🔥 Все товары списком", callback_data="all_products")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            "🛍️ Каталог защитной экипировки:\n\nВыберите категорию товаров:",
            reply_markup=reply_markup,
        )
    else:
        await update.callback_query.edit_message_text(
            "🛍️ Каталог защитной экипировки:\n\nВыберите категорию товаров:",
            reply_markup=reply_markup,
        )


# Показ товаров по категориям
async def show_category(query, category_name: str) -> None:
    keyboard = []

    # Находим товары в выбранной категории
    category_products = []
    for product_id, product in PRODUCTS.items():
        if product["category"] == category_name:
            category_products.append((product_id, product))

    # Сортируем товары по цене (используем безопасную функцию)
    category_products.sort(key=lambda x: extract_price(x[1]["price"]))

    for product_id, product in category_products:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{product['name']} - {product['price']}",
                    callback_data=f"product_{product_id}",
                )
            ]
        )

    keyboard.append(
        [InlineKeyboardButton("🔙 Назад к категориям", callback_data="back_to_catalog")]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"📂 {category_name}:\n\n"
        f"Найдено товаров: {len(category_products)}\n"
        "Выберите товар для подробной информации:",
        reply_markup=reply_markup,
    )


# Показ всех товаров списком
async def show_all_products(query) -> None:
    keyboard = []

    # Сортируем товары по цене (используем безопасную функцию)
    sorted_products = sorted(PRODUCTS.items(), key=lambda x: extract_price(x[1]["price"]))

    for product_id, product in sorted_products:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{product['name']} - {product['price']}",
                    callback_data=f"product_{product_id}",
                )
            ]
        )

    keyboard.append(
        [InlineKeyboardButton("🔙 Назад к категориям", callback_data="back_to_catalog")]
    )

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "🔥 Все товары:\n\nВыберите товар для подробной информации:",
        reply_markup=reply_markup,
    )


# Показ информации о товаре
async def show_product(query, product_id: str) -> None:
    try:
        if product_id not in PRODUCTS:
            await query.message.reply_text("❌ Товар не найден.")
            return

        product = PRODUCTS[product_id]

        details = product.get(
            "details",
            "• Информация уточняется у менеджера\n• Все характеристики соответствуют ГОСТ",
        )

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

        # ИСПРАВЛЕННАЯ КЛАВИАТУРА БЕЗ КНОПКИ "КУПИТЬ СЕЙЧАС"
        keyboard = [
            [
                InlineKeyboardButton(
                    "🛒 Добавить в корзину", callback_data=f"add_to_cart_{product_id}"
                )
            ],
            [InlineKeyboardButton("📂 Назад к каталогу", callback_data="back_to_catalog")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Проверяем наличие изображения и отправляем его
        image_path = product.get("image")
        if image_path and os.path.exists(image_path):
            try:
                with open(image_path, "rb") as photo:
                    # Отправляем новое сообщение с фото
                    await query.message.reply_photo(
                        photo=photo, caption=text, reply_markup=reply_markup
                    )
                # Удаляем предыдущее сообщение с кнопками товара
                try:
                    await query.delete_message()
                except:
                    pass  # Игнорируем ошибку удаления сообщения
            except Exception as e:
                logger.error(f"Error sending image for product {product_id}: {e}")
                # Если не удалось отправить изображение, отправляем текст
                await query.edit_message_text(text, reply_markup=reply_markup)
        else:
            # Если изображения нет, отправляем только текст
            await query.edit_message_text(text, reply_markup=reply_markup)

    except Exception as e:
        logger.error(f"Error showing product {product_id}: {e}")
        await query.message.reply_text("❌ Ошибка при загрузке информации о товаре.")


# Показ каталога из кнопки
async def show_catalog_from_button(query) -> None:
    keyboard = []

    categories = {}
    for product_id, product in PRODUCTS.items():
        category = product["category"]
        if category not in categories:
            categories[category] = []
        categories[category].append((product_id, product))

    for category in sorted(categories.keys()):
        keyboard.append(
            [InlineKeyboardButton(f"📂 {category}", callback_data=f"category_{category}")]
        )

    keyboard.append([InlineKeyboardButton("🔥 Все товары списком", callback_data="all_products")])
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(
            "🛍️ Каталог защитной экипировки:\n\nВыберите категорию товаров:",
            reply_markup=reply_markup,
        )
    except Exception as e:
        logger.error(f"Error editing catalog message: {e}")
        # Если не удалось отредактировать сообщение, отправляем новое
        await query.message.reply_text(
            "🛍️ Каталог защитной экипировки:\n\nВыберите категорию товаров:",
            reply_markup=reply_markup,
        )


# Возврат в главное меню
async def back_to_main(query) -> None:
    keyboard = [
        [KeyboardButton("🛍️ Каталог товаров"), KeyboardButton("❓ Частые вопросы")],
        [KeyboardButton("ℹ️ О компании"), KeyboardButton("📞 Контакты")],
        [KeyboardButton("🔥 Топ товары"), KeyboardButton("🛒 Корзина")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await query.message.reply_text("Главное меню. Выберите действие:", reply_markup=reply_markup)


# Показ FAQ
async def show_faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = []

    for faq_id, faq in FAQ.items():
        keyboard.append([InlineKeyboardButton(faq["question"], callback_data=f"faq_{faq_id}")])

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            "❓ Частые вопросы:\n\nВыберите интересующий вас вопрос:",
            reply_markup=reply_markup,
        )
    else:
        await update.callback_query.edit_message_text(
            "❓ Частые вопросы:\n\nВыберите интересующий вас вопрос:",
            reply_markup=reply_markup,
        )


# Показ ответа на вопрос FAQ
async def show_faq_answer(query, faq_id: str) -> None:
    faq = FAQ[faq_id]

    text = f"{faq['question']}\n\n{faq['answer']}"

    keyboard = [
        [InlineKeyboardButton("📋 Все вопросы", callback_data="back_to_faq")],
        [InlineKeyboardButton("🔙 Главное меню", callback_data="back_to_main")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(text, reply_markup=reply_markup)


# Показ FAQ из кнопки
async def show_faq_from_button(query) -> None:
    keyboard = []

    for faq_id, faq in FAQ.items():
        keyboard.append([InlineKeyboardButton(faq["question"], callback_data=f"faq_{faq_id}")])

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await query.edit_message_text(
            "❓ Частые вопросы:\n\nВыберите интересующий вас вопрос:",
            reply_markup=reply_markup,
        )
    except Exception as e:
        logger.error(f"Error editing FAQ message: {e}")
        # Если не удалось отредактировать сообщение, отправляем новое
        await query.message.reply_text(
            "❓ Частые вопросы:\n\nВыберите интересующий вас вопрос:",
            reply_markup=reply_markup,
        )


# О компании
async def about_company(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🏢 О компании:\n\n"
        "Мы — ведущий производитель современных средств защиты: бронежилетов, тентов, укрытий, одежды и эвакуационных устройств."
    )

    if update.message:
        await update.message.reply_text(text)
    else:
        await update.callback_query.message.reply_text(text)


# Контакты
async def contacts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📞 Контакты:\n\n"
        "📞 Телефон: +78122009264\n+78007773876\n"
        "📧 Email: tkgroupooo@ya.ru\n"
        "🌐 Сайт: https://technokryptonite.ru/"
    )

    if update.message:
        await update.message.reply_text(text, parse_mode="HTML", disable_web_page_preview=False)
    else:
        await update.callback_query.message.reply_text(
            text, parse_mode="HTML", disable_web_page_preview=False
        )


# Показ топ товаров
async def show_top_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Выбираем несколько товаров как "топ"
    top_products_ids = ["komplekt_shturmovoy", "komplekt_protivooskolochny"]

    keyboard = []

    for product_id in top_products_ids:
        if product_id in PRODUCTS:
            product = PRODUCTS[product_id]
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{product['name']} - {product['price']}",
                        callback_data=f"product_{product_id}",
                    )
                ]
            )

    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="back_to_main")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            "🔥 Самые популярные товары:\n\nПроверенные решения для вашей безопасности:",
            reply_markup=reply_markup,
        )
    else:
        await update.callback_query.edit_message_text(
            "🔥 Самые популярные товары:\n\nПроверенные решения для вашей безопасности:",
            reply_markup=reply_markup,
        )


# Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id
    logger.info(f"Button pressed: {data} by user {user_id}")

    try:
        if data.startswith("product_"):
            product_id = data[8:]
            logger.info(f"Showing product: {product_id}")
            await show_product(query, product_id)

        elif data.startswith("category_"):
            category_name = data[9:]
            logger.info(f"Showing category: {category_name}")
            await show_category(query, category_name)

        elif data.startswith("faq_"):
            faq_id = data[4:]
            logger.info(f"Showing FAQ: {faq_id}")
            await show_faq_answer(query, faq_id)

        elif data.startswith("add_to_cart_"):
            product_id = data[12:]
            logger.info(f"Adding to cart: {product_id}")
            await add_to_cart_callback(update, context)

        elif data.startswith("paid_"):
            order_id = data[5:]
            logger.info(f"Payment confirmed for order: {order_id}")
            await confirm_payment(update, context)

        elif data.startswith("pay_qr_"):
            order_id = data[7:]
            logger.info(f"Showing QR code for order: {order_id}")
            await show_qr_code(update, context)

        elif data.startswith("pay_card_"):
            order_id = data[9:]
            logger.info(f"Showing card payment for order: {order_id}")
            await pay_by_card(update, context)

        elif data == "all_products":
            logger.info("Showing all products")
            await show_all_products(query)

        elif data == "back_to_catalog":
            logger.info("Returning to catalog")
            await show_catalog_from_button(query)

        elif data == "back_to_faq":
            logger.info("Returning to FAQ")
            await show_faq_from_button(query)

        elif data == "back_to_main":
            logger.info("Returning to main menu")
            await back_to_main(query)

        elif data == "checkout":
            logger.info("Starting checkout process")
            await start_checkout_from_callback(update, context)

        elif data == "clear_cart":
            logger.info("Clearing cart")
            await clear_cart_handler(update, context)

        elif data.startswith("color_"):
            color = data[6:]
            logger.info(f"Color selected: {color}")
            await ask_size(update, context)

        elif data.startswith("size_"):
            size = data[5:]
            logger.info(f"Size selected: {size}")
            await ask_phone(update, context)

        elif data == "back_to_color":
            logger.info("Returning to color selection")
            await back_to_color(update, context)

        elif data == "final_confirm":
            logger.info("Final order confirmation")
            await complete_order(update, context)

        elif data == "change_data":
            logger.info("Changing order data")
            await change_data(update, context)

        elif data == "cancel_order":
            logger.info("Cancelling order")
            await cancel_order(update, context)

        else:
            logger.warning(f"Unknown button data: {data}")
            await query.message.reply_text("❌ Неизвестная команда. Попробуйте еще раз.")

    except Exception as e:
        logger.error(f"Error in button handler for data '{data}': {e}", exc_info=True)

        # Более конкретные сообщения об ошибках
        error_message = "❌ Произошла ошибка при обработке запроса. Попробуйте еще раз."

        if "Message is not modified" in str(e):
            # Игнорируем эту ошибку - сообщение не изменилось
            return
        elif "Query is too old" in str(e):
            error_message = "❌ Время действия кнопки истекло. Пожалуйста, начните заново."
        elif "Message to edit not found" in str(e):
            error_message = (
                "❌ Сообщение не найдено. Возможно, оно было удалено. Пожалуйста, начните заново."
            )

        try:
            await query.edit_message_text(error_message)
        except:
            try:
                await query.message.reply_text(error_message)
            except:
                logger.error("Could not send error message to user")


# Обработка текстовых сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
            await show_cart(update, context)
        else:
            await update.message.reply_text("Используйте кнопки меню для навигации.")
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        await update.message.reply_text("❌ Произошла ошибка. Попробуйте еще раз.")


# Обработка ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Exception while handling an update: {context.error}")


# Создаем ConversationHandler для оформления заказа
def get_checkout_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(start_checkout_from_callback, pattern="^checkout$")],
        states={
            COLOR: [CallbackQueryHandler(ask_size, pattern="^color_")],
            SIZE: [
                CallbackQueryHandler(ask_phone, pattern="^size_"),
                CallbackQueryHandler(back_to_color, pattern="^back_to_color$"),
            ],
            PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name),
                CallbackQueryHandler(cancel_order, pattern="^cancel_order$"),
            ],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_address)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_order)],
            CONFIRM_ORDER: [
                CallbackQueryHandler(complete_order, pattern="^final_confirm$"),
                CallbackQueryHandler(change_data, pattern="^change_data$"),
                CallbackQueryHandler(cancel_order, pattern="^cancel_order$"),
            ],
        },
        fallbacks=[CallbackQueryHandler(cancel_order, pattern="^cancel_order$")],
        allow_reentry=True,
    )


# Основная функция
def main() -> None:
    # Проверяем токен
    if not BOT_TOKEN:
        print("❌ ОШИБКА: BOT_TOKEN не найден!")
        return

    try:
        application = Application.builder().token(BOT_TOKEN).build()

        # Обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("cart", show_cart))

        # ConversationHandler для оформления заказа
        application.add_handler(get_checkout_conversation_handler())

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
