import sys
import asyncio
import json
import os
import time
import logging
import signal
import platform
import random

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.dispatcher.middlewares.error import ErrorsMiddleware


API_TOKEN = "8358618571:AAHmQGl3Vl7KA612YyfJ5MKjotGXQ8-ycEA"
DONATE_LINK = "https://www.donationalerts.com/r/dungeonadventures"  # Замените на вашу ссылку для донатов

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

PLANTS_FILE = "plants.json"
USERS_FILE = "users.json"

emoji_dict = {
    "shop": "🌾",
    "buy": "🛒",
    "plant": "🌱",
    "harvest": "🌿",
    "status": "📈",
    "help": "❓",
    "balance": "💰",
    "seed": "📦",
    "empty_garden": "🪴",
    "success": "✅",
    "error": "❌",
    "hourglass": "⏳",
    "trophy": "🏆",
    "donate": "❤️",
}

translations = {
    "welcome": {
        "uk": f"{emoji_dict['plant']} Вітаю у Grow a Garden! Натисніть кнопку нижче для початку.",
        "ru": f"{emoji_dict['plant']} Добро пожаловать в Grow a Garden! Нажмите кнопку ниже, чтобы начать.",
        "en": f"{emoji_dict['plant']} Welcome to Grow a Garden! Press button below to start.",
    },
    "choose_language": {
        "uk": f"{emoji_dict['shop']} Оберіть мову:",
        "ru": f"{emoji_dict['shop']} Выберите язык:",
        "en": f"{emoji_dict['shop']} Choose language:",
    },
    "language_set": {
        "uk": f"{emoji_dict['success']} Мова встановлена на українську.",
        "ru": f"{emoji_dict['success']} Язык установлен на русский.",
        "en": f"{emoji_dict['success']} Language set to English.",
    },
    "bought_seed": {
        "uk": "{amount} пакет насіння {name} куплено. Залишок: {balance} монет.",
        "ru": "{amount} пакет семян {name} куплено. Остаток: {balance} монет.",
        "en": "{amount} pack(s) of {name} bought. Balance: {balance} coins.",
    },
    "planted_plant": {
        "uk": "Посаджено {name}! Залишок насіння: {left}",
        "ru": "Посажено {name}! Остаток семян: {left}",
        "en": "{name} planted! Seeds left: {left}",
    },
    "planted_plants": {
        "uk": "Посаджені рослини",
        "ru": "Посаженные растения",
        "en": "Planted plants",
    },
    "status_empty_garden": {
        "uk": f"{emoji_dict['empty_garden']} Ваш сад порожній. Посадіть щось командою /plant.",
        "ru": f"{emoji_dict['empty_garden']} Ваш сад пуст. Посадите что-нибудь командой /plant.",
        "en": f"{emoji_dict['empty_garden']} Your garden is empty. Plant something with /plant.",
    },
    "help_text": {
        "uk": f"{emoji_dict['help']} Команди:\n/shop - магазин насіння\n/buy - купити насіння\n/plant - посадити рослину\n/harvest - зібрати урожай\n/status - подивитися сад і баланс\n/top - Топ 10 гравців за монетами\n/donate - Підтримати розробника",
        "ru": f"{emoji_dict['help']} Команды:\n/shop - магазин семян\n/buy - купить семена\n/plant - посадить растение\n/harvest - собрать урожай\n/status - посмотреть сад и баланс\n/top - Топ 10 игроков по монетам\n/donate - Поддержать разработчика",
        "en": f"{emoji_dict['help']} Commands:\n/shop - seed shop\n/buy - buy seeds\n/plant - plant\n/harvest - harvest\n/status - view garden and balance\n/top - Top 10 players by coins\n/donate - Support the developer",
    },
    "buy_no_seed": {
        "uk": f"{emoji_dict['error']} У вас немає пакету насіння {{name}}.",
        "ru": f"{emoji_dict['error']} У вас нет пакета семян {{name}}.",
        "en": f"{emoji_dict['error']} You have no seed pack {{name}}.",
    },
    "not_enough_money": {
        "uk": f"{emoji_dict['error']} Недостатньо грошей для купівлі насіння.",
        "ru": f"{emoji_dict['error']} Недостаточно денег для покупки семян.",
        "en": f"{emoji_dict['error']} Not enough money to buy seeds.",
    },
    "no_planted": {
        "uk": f"{emoji_dict['error']} Ви ще не садили цю рослину.",
        "ru": f"{emoji_dict['error']} Вы еще не сажали это растение.",
        "en": f"{emoji_dict['error']} You have not planted this plant yet.",
    },
    "no_seeds": {
        "uk": f"{emoji_dict['seed']} У вас немає насіння. Купіть у магазині (/shop).",
        "ru": f"{emoji_dict['seed']} У вас нет семян. Купите в магазине (/shop).",
        "en": f"{emoji_dict['seed']} You have no seeds. Buy in shop (/shop).",
    },
    "harvest_not_ready": {
        "uk": f"{emoji_dict['hourglass']} {{name}} ще не дозріла. Зачекайте {{sec}} секунд.",
        "ru": f"{emoji_dict['hourglass']} {{name}} еще не созрела. Подождите {{sec}} секунд.",
        "en": f"{emoji_dict['hourglass']} {{name}} is not ripe yet. Wait {{sec}} seconds.",
    },
    "harvest_success": {
        "uk": f"{emoji_dict['success']} Урожай {{name}} зібрано! Ви заробили {{price}} монет. Баланс: {{money}} монет.",
        "ru": f"{emoji_dict['success']} Урожай {{name}} собран! Вы заработали {{price}} монет. Баланс: {{money}} монет.",
        "en": f"{emoji_dict['success']} {{name}} harvest collected! You earned {{price}} coins. Balance: {{money}} coins.",
    },
    "unknown_command": {
        "uk": f"{emoji_dict['error']} Невідома команда. Використайте кнопку /help для довідки.",
        "ru": f"{emoji_dict['error']} Неизвестная команда. Используйте кнопку /help для справки.",
        "en": f"{emoji_dict['error']} Unknown command. Use /help button for help.",
    },
    "top_title": {
        "uk": f"{emoji_dict['trophy']} Топ 10 гравців за монетами:",
        "ru": f"{emoji_dict['trophy']} Топ 10 игроков по монетам:",
        "en": f"{emoji_dict['trophy']} Top 10 players by coins:",
    },
    "top_player_line": {
        "uk": "Гравець {mention} - {money} монет",
        "ru": "Игрок {mention} - {money} монет",
        "en": "Player {mention} - {money} coins",
    },
    "top_no_players": {
        "uk": "Поки немає гравців для відображення.",
        "ru": "Пока нет игроков для отображения.",
        "en": "No players to show yet.",
    },
    "donate_text": {
        "uk": f"{emoji_dict['donate']} Дякуємо за підтримку! Ваш внесок допомагає розвивати бота. Посилання для донату: {DONATE_LINK}",
        "ru": f"{emoji_dict['donate']} Спасибо за поддержку! Ваш вклад помогает развивать бота. Ссылка для доната: {DONATE_LINK}",
        "en": f"{emoji_dict['donate']} Thank you for your support! Your contribution helps develop the bot. Donation link: {DONATE_LINK}",
    },
}

def load_json_file(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            f.seek(0)
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки или пустой файл {path}: {e}")
        return {}

def load_plants():
    return load_json_file(PLANTS_FILE)

def load_users():
    return load_json_file(USERS_FILE)

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

def migrate_garden_data(users):
    changed = False
    for user in users.values():
        garden = user.get("garden", {})
        if not isinstance(garden, dict):
            continue
        for plant, val in list(garden.items()):
            if isinstance(val, (float, int)):
                garden[plant] = [float(val)]
                changed = True
            elif not isinstance(val, list):
                garden[plant] = []
                changed = True
    if changed:
        save_users(users)

def get_user_language(user_id):
    users = load_users()
    user = users.get(str(user_id))
    if isinstance(user, dict):
        lang = user.get("language")
        if lang in ("uk", "ru", "en"):
            return lang
    return "en"

def get_plant_name(plant, lang):
    if isinstance(plant, dict):
        name = plant.get("name")
        if isinstance(name, dict):
            return name.get(lang, name.get("en", "Unknown"))
        elif isinstance(name, str):
            return name
    elif isinstance(plant, str):
        return plant
    return "Unknown"

def main_menu_keyboard(lang):
    builder = ReplyKeyboardBuilder()
    builder.add(
        types.KeyboardButton(text="/shop"),
        types.KeyboardButton(text="/buy"),
    )
    builder.add(
        types.KeyboardButton(text="/plant"),
        types.KeyboardButton(text="/harvest"),
    )
    builder.add(
        types.KeyboardButton(text="/status"),
        types.KeyboardButton(text="/help"),
    )
    builder.add(
        types.KeyboardButton(text="/top"),
        types.KeyboardButton(text="/donate"),
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)


class ErrorHandler(ErrorsMiddleware):
    def __init__(self, dispatcher: Dispatcher):
        super().__init__(dispatcher)

    async def __call__(self, handler, event, data):
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Error in handler: {e}", exc_info=True)
            if hasattr(event, "message") and event.message:
                await event.message.answer(f"{emoji_dict['error']} Щось пішло не так, спробуйте пізніше.")
            elif hasattr(event, "callback_query") and event.callback_query:
                await event.callback_query.message.answer(f"{emoji_dict['error']} Щось пішло не так, спробуйте пізніше.")
            return None

dp.message.middleware(ErrorHandler(dp))
dp.callback_query.middleware(ErrorHandler(dp))


@dp.message(Command("start"))
async def start_handler(message: types.Message):
    users = load_users()
    user_id = str(message.from_user.id)
    if user_id not in users or not users[user_id].get("language"):
        users[user_id] = {"money": 100, "garden": {}, "seeds": {}, "language": None}
        save_users(users)
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="🇺🇦 Українська", callback_data="setlang_uk")
        keyboard.button(text="🇷🇺 Русский", callback_data="setlang_ru")
        keyboard.button(text="🇬🇧 English", callback_data="setlang_en")
        await message.answer(translations["welcome"]["en"])
        await message.answer(translations["choose_language"]["en"], reply_markup=keyboard.as_markup())
        return
    lang = get_user_language(message.from_user.id)
    await message.answer(translations["welcome"][lang], reply_markup=main_menu_keyboard(lang))


@dp.callback_query(lambda c: c.data and c.data.startswith("setlang_"))
async def set_language_callback(callback: types.CallbackQuery):
    lang = callback.data[8:]
    users = load_users()
    user_id = str(callback.from_user.id)
    if user_id not in users:
        users[user_id] = {"money": 100, "garden": {}, "seeds": {}, "language": lang}
    else:
        users[user_id]["language"] = lang
    save_users(users)
    await callback.message.answer(translations["language_set"][lang])
    await callback.message.answer(translations["welcome"][lang], reply_markup=main_menu_keyboard(lang))
    await callback.answer()


@dp.message(Command("shop"))
async def shop_handler(message: types.Message):
    lang = get_user_language(message.from_user.id)
    plants = load_plants()
    response = f"{emoji_dict['shop']} " + {
        "uk": "🏪Магазин насіння:\n",
        "ru": "🏪Магазин семян:\n",
        "en": "🏪Seed Shop:\n"
    }[lang]

    builder = InlineKeyboardBuilder()
    for key, plant in plants.items():
        price = plant.get("price", 1)
        name = get_plant_name(plant, lang)
        price_str = f"{price} монет" if lang != "en" else f"{price} coins"
        response += f"• {name} ({key}): {price_str}\n"
        builder.button(text=f"{emoji_dict['buy']} {name}", callback_data=f"buy_{key}")

    builder.adjust(3, 2)

    await message.answer(response)
    await message.answer({
        "uk": "🌱Оберіть насіння для купівлі:",
        "ru": "🌱Выберите семена для покупки:",
        "en": "🌱Choose seeds to buy:"
    }[lang], reply_markup=builder.as_markup())

@dp.callback_query(lambda c: c.data and c.data.startswith("buy_"))
async def buy_seed_callback(callback: types.CallbackQuery):
    lang = get_user_language(callback.from_user.id)
    seed_key = callback.data[4:]
    users = load_users()
    migrate_garden_data(users)
    user = users.get(str(callback.from_user.id))
    plants = load_plants()
    if seed_key not in plants:
        await callback.message.answer(translations["buy_no_seed"][lang].format(name=seed_key))
        await callback.answer()
        return
    price = plants[seed_key]["price"]
    if user["money"] < price:
        await callback.message.answer(translations["not_enough_money"][lang])
        await callback.answer()
        return
    user["money"] -= price
    user["seeds"][seed_key] = user["seeds"].get(seed_key, 0) + 1
    save_users(users)
    await callback.message.answer(f"{emoji_dict['success']} " + translations["bought_seed"][lang].format(
        amount=1,
        name=plants[seed_key]['name'][lang],
        balance=user['money']
    ))
    await callback.answer()


@dp.message(Command("plant"))
async def plant_handler(message: types.Message):
    lang = get_user_language(message.from_user.id)
    users = load_users()
    migrate_garden_data(users)
    user = users.get(str(message.from_user.id))
    seeds = user.get("seeds", {})
    plants = load_plants()
    if not seeds:
        await message.answer(f"{emoji_dict['error']} {translations['no_seeds'][lang]}")
        return

    builder = InlineKeyboardBuilder()
    for key, count in seeds.items():
        if count > 0:
            name = get_plant_name(plants.get(key, {}), lang)
            builder.button(
                text=f"{emoji_dict['plant']} {name} ({count} шт.)",
                callback_data=f"plant_{key}"
            )

    if not builder.buttons:
        await message.answer(translations["status_empty_garden"][lang])
        return

    builder.adjust(3, 2)

    await message.answer({
        "uk": "🌻Оберіть насіння для посадки:",
        "ru": "🌻Выберите семена для посадки:",
        "en": "🌻Select seeds to plant:"
    }[lang], reply_markup=builder.as_markup())


@dp.callback_query(lambda c: c.data and c.data.startswith("plant_"))
async def plant_seed_callback(callback: types.CallbackQuery):
    lang = get_user_language(callback.from_user.id)
    seed_key = callback.data[6:]
    users = load_users()
    migrate_garden_data(users)
    user = users.get(str(callback.from_user.id))
    plants = load_plants()

    if seed_key not in user.get("seeds", {}) or user["seeds"][seed_key] <= 0:
        await callback.message.answer(translations["buy_no_seed"][lang].format(name=plants.get(seed_key, {}).get("name", {}).get(lang, seed_key)))
        await callback.answer()
        return

    # Уменьшаем количество семян
    user["seeds"][seed_key] -= 1
    if user["seeds"][seed_key] == 0:
        del user["seeds"][seed_key]

    # Добавляем растение в сад
    user["garden"].setdefault(seed_key, []).append(time.time())

    save_users(users)

    # Обновляем клавиатуру и сообщение с новым количеством
    seeds = user.get("seeds", {})
    builder = InlineKeyboardBuilder()
    for key, count in seeds.items():
        name = get_plant_name(plants.get(key, {}), lang)
        builder.button(
            text=f"{emoji_dict['plant']} {name} ({count} шт.)",
            callback_data=f"plant_{key}"
        )

    if not builder.buttons:
        # Нет доступных семян
        await callback.message.edit_text(
            translations["status_empty_garden"][lang],
            reply_markup=None
        )
    else:
        builder.adjust(3, 2)
        await callback.message.edit_text(
            {
                "uk": "🌻Оберіть насіння для посадки:",
                "ru": "🌻Выберите семена для посадки:",
                "en": "🌻Select seeds to plant:",
            }[lang],
            reply_markup=builder.as_markup()
        )

    await callback.answer(f"{emoji_dict['success']} " + translations["planted_plant"][lang].format(
        name=plants[seed_key]['name'][lang],
        left=user.get('seeds', {}).get(seed_key, 0)
    ))


@dp.message(Command("harvest"))
async def harvest_handler(message: types.Message):
    lang = get_user_language(message.from_user.id)
    users = load_users()
    migrate_garden_data(users)
    user = users.get(str(message.from_user.id))
    garden = user.get("garden", {})
    if not garden:
        await message.answer(f"{emoji_dict['error']} {translations['no_planted'][lang]}")
        return
    plants = load_plants()
    builder = InlineKeyboardBuilder()
    for key in garden.keys():
        name = get_plant_name(plants.get(key, {}), lang)
        builder.button(text=f"{emoji_dict['harvest']} {name}", callback_data=f"harvest_{key}")

    builder.adjust(3, 3, 3, 3, 3, 3, 3)

    await message.answer({
        "uk": "🌾Виберіть рослину для збору урожаю:",
        "ru": "🌾Выберите растение для сбора урожая:",
        "en": "🌾Select plant to harvest:"
    }[lang], reply_markup=builder.as_markup())


@dp.callback_query(lambda c: c.data and c.data.startswith("harvest_"))
async def harvest_crop_callback(callback: types.CallbackQuery):
    lang = get_user_language(callback.from_user.id)
    plant_key = callback.data[8:]
    users = load_users()
    migrate_garden_data(users)
    user = users.get(str(callback.from_user.id))
    plants = load_plants()
    if plant_key not in user.get("garden", {}) or not user["garden"][plant_key]:
        await callback.message.answer(translations["no_planted"][lang])
        await callback.answer()
        return
    grow_time = plants[plant_key]["grow_time"]
    planted_times = user["garden"][plant_key]
    now = time.time()
    ready_index = None
    for i, planted_time in enumerate(planted_times):
        if now - planted_time >= grow_time:
            ready_index = i
            break
    if ready_index is None:
        wait_sec = int(grow_time - (now - planted_times[0]))
        await callback.message.answer(translations["harvest_not_ready"][lang].format(
            name=plants[plant_key]["name"][lang],
            sec=wait_sec
        ))
        await callback.answer()
        return
    planted_times.pop(ready_index)
    if not planted_times:
        del user["garden"][plant_key]

    x = random.uniform(0, 100)
    base_price = plants[plant_key]["price"]
    price_factor = max(0.3, 30 / base_price)

    mults = [
        (30, 1.0),
        (15 * price_factor, 1.1),
        (10 * price_factor, 1.2),
        (5 * price_factor, 1.3),
        (4 * price_factor, 1.4),
        (3 * price_factor, 1.5),
        (2 * price_factor, 1.6),
        (1 * price_factor, 1.7),
        (0.5 * price_factor, 1.8),
        (0.3 * price_factor, 1.9),
        (0.1 * price_factor, 2.0),
    ]
    total = 0
    multiplier = 1.0
    for chance, mult in mults:
        total += chance
        if x <= total:
            multiplier = mult
            break

    earned = int(base_price * multiplier)
    user["money"] += earned
    save_users(users)

    multiplier_part = f" (x{multiplier:.1f})" if multiplier > 1 else ""

    await callback.message.answer(
        f"{emoji_dict['success']} " +
        translations["harvest_success"][lang].format(
            name=plants[plant_key]["name"][lang],
            price=earned,
            money=user["money"]
        ) + multiplier_part
    )
    await callback.answer()


@dp.message(Command("status"))
async def status_handler(message: types.Message):
    lang = get_user_language(message.from_user.id)
    users = load_users()
    migrate_garden_data(users)
    user = users.get(str(message.from_user.id), {})
    balance = user.get("money", 0)
    plants = load_plants()

    response = f"{emoji_dict['balance']} " + {
        "uk": "💰Баланс",
        "ru": "💰Баланс",
        "en": "💰Balance"
    }[lang] + f": {balance} " + {
        "uk": "монет",
        "ru": "монет",
        "en": "coins"
    }[lang] + "\n\n"

    if not user.get("garden"):
        response += translations["status_empty_garden"][lang]
        await message.answer(response)
        return

    response += f"{emoji_dict['plant']} {translations['planted_plants'][lang]}:\n"
    now = time.time()
    total_plants = 0

    for plant_key, planted_times in user.get("garden", {}).items():
        plant = plants.get(plant_key, {})
        name = get_plant_name(plant, lang)
        count = len(planted_times)
        total_plants += count

        times_left = []
        grow_time = plant.get("grow_time", 0)

        for t in planted_times:
            left = max(0, grow_time - (now - t))
            m, s = divmod(int(left), 60)
            times_left.append(f"{m}m {s}s")

        times_left_text = ", ".join(times_left)
        harvest_text = "" if lang != "en" else "left to harvest"
        response += f"- {name}: {count} " + {
            "uk": "рослин(а)",
            "ru": "растени(е)",
            "en": "plant(s)"
        }[lang] + f"; {times_left_text} {harvest_text}\n"

    response += {
        "uk": f"\n{emoji_dict['plant']} 🌿Всього рослин у саду: {total_plants}\n",
        "ru": f"\n{emoji_dict['plant']} 🌿Всего растений в саду: {total_plants}\n",
        "en": f"\n{emoji_dict['plant']} 🌿Total plants in garden: {total_plants}\n",
    }[lang]

    seeds = user.get("seeds", {})
    if seeds:
        response += {
            "uk": f"\n{emoji_dict['seed']} 🍀Наявні насіння:\n",
            "ru": f"\n{emoji_dict['seed']} 🍀Доступные семена:\n",
            "en": f"\n{emoji_dict['seed']} 🍀Available seeds:\n",
        }[lang]
        for key, amt in seeds.items():
            seed_name = get_plant_name(plants.get(key, {}), lang)
            packs_txt = {
                "uk": "пакет(ів)",
                "ru": "пакет(ов)",
                "en": "pack(s)"
            }[lang]
            response += f"- {seed_name}: {amt} {packs_txt}\n"
    else:
        response += {
            "uk": f"\n{emoji_dict['seed']} {translations['no_seeds'][lang]}\n",
            "ru": f"\n{emoji_dict['seed']} {translations['no_seeds'][lang]}\n",
            "en": f"\n{emoji_dict['seed']} {translations['no_seeds'][lang]}\n",
        }[lang]

    await message.answer(response)


@dp.message(Command("help"))
async def help_handler(message: types.Message):
    lang = get_user_language(message.from_user.id)
    await message.answer(f"{emoji_dict['help']} {translations['help_text'][lang]}")


@dp.message(Command("top"))
async def top_handler(message: types.Message):
    lang = get_user_language(message.from_user.id)
    users = load_users()
    top_users = sorted(users.items(), key=lambda x: x[1].get("money", 0), reverse=True)[:10]
    if not top_users:
        await message.answer(translations["top_no_players"][lang])
        return
    lines = [translations["top_title"][lang]]
    for user_id, data in top_users:
        money = data.get("money", 0)
        username = data.get("username")
        mention = f"@{username}" if username else f"[{user_id}](tg://user?id={user_id})"
        lines.append(translations["top_player_line"][lang].format(mention=mention, money=money))
    await message.answer("\n".join(lines), parse_mode="Markdown")


@dp.message(Command("donate"))
async def donate_handler(message: types.Message):
    lang = get_user_language(message.from_user.id)
    await message.answer(translations["donate_text"][lang])


@dp.message()
async def fallback_handler(message: types.Message):
    lang = get_user_language(message.from_user.id)
    await message.answer(f"{emoji_dict['error']} {translations['unknown_command'][lang]}")


def _signal_handler():
    logger.info("SIGINT received, shutting down...")
    asyncio.create_task(bot.session.close())
    sys.exit(0)


async def main():
    loop = asyncio.get_running_loop()
    if platform.system() != "Windows":
        loop.add_signal_handler(signal.SIGINT, _signal_handler)
    while True:
        try:
            await dp.start_polling(bot, skip_updates=True)
        except Exception as e:
            logger.error(f"Polling error: {e}")
            await asyncio.sleep(10)
        else:
            break


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually.")