import os
import random
import json
import re
from pathlib import Path
from io import BytesIO
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# ================== Настройки ==================
# 🔐 Токен берётся из переменных окружения
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("🚨 ОШИБКА: Не задан токен бота!")
    print("Создайте переменную окружения BOT_TOKEN или добавьте токен в .env файл")
    exit(1)

DATA_FILE = Path("megabot_data.json")

# ================== Данные ==================
if DATA_FILE.exists():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {"players": {}, "events": [], "chats": []}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_player(user_id: str):
    if user_id not in data["players"]:
        data["players"][user_id] = {"balance":100, "bank":0, "xp":0, "level":1}
        save_data()
    return data["players"][user_id]

def user_name(update: Update):
    return update.effective_user.first_name

def format_currency(amount):
    return f"{amount}💰"

# ================== Команды ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id=str(update.effective_chat.id)
    if chat_id not in data["chats"]:
        data["chats"].append(chat_id)
        save_data()
    await update.message.reply_text(f"Привет, {user_name(update)}! Я твой МЕГА-БОТ 🎮\nНапиши /helpMark для команд.")

async def helpMark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text="""
💰 Экономика:
/balance — баланс
/work — заработать
/deposit <сумма> — положить в банк
/withdraw <сумма> — снять из банка

🎲 Казино:
/slots <ставка> — слоты
/coin <ставка> — орёл/решка
/dice <ставка> — кубик
/guess <число> — угадай число от 1 до 10

😂 Мемы и приколы:
/mem — мем (только текст)
/sosal — сосал
/joke — шутка

⏱ События:
/time <текст> — сохранить
/timeK — посмотреть все события
"""
    await update.message.reply_text(text)

# ================== Экономика ==================
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p=get_player(str(update.effective_user.id))
    await update.message.reply_text(f"💰 Баланс: {format_currency(p['balance'])}\n🏦 Банк: {format_currency(p['bank'])}")

async def work(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p=get_player(str(update.effective_user.id))
    earn=random.randint(10,50)
    p["balance"] += earn
    p["xp"] += 10
    save_data()
    await update.message.reply_text(f"💼 Ты заработал {format_currency(earn)} и получил 10 XP")

async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p=get_player(str(update.effective_user.id))
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Используй: /deposit <сумма>")
        return
    amt = int(context.args[0])
    if amt > p["balance"]:
        await update.message.reply_text("❌ Недостаточно денег")
        return
    p["balance"] -= amt
    p["bank"] += amt
    save_data()
    await update.message.reply_text(f"🏦 Положено {format_currency(amt)} в банк")

async def withdraw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p=get_player(str(update.effective_user.id))
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Используй: /withdraw <сумма>")
        return
    amt = int(context.args[0])
    if amt > p["bank"]:
        await update.message.reply_text("❌ Недостаточно в банке")
        return
    p["balance"] += amt
    p["bank"] -= amt
    save_data()
    await update.message.reply_text(f"💰 Снято {format_currency(amt)} из банка")

# ================== Казино ==================
async def slots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p=get_player(str(update.effective_user.id))
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Используй: /slots <ставка>")
        return
    bet=int(context.args[0])
    if bet>p["balance"]:
        await update.message.reply_text("❌ Недостаточно денег")
        return
    p["balance"]-=bet
    roll=[random.choice(["🍒","🍋","💎","7️⃣"]) for _ in range(3)]
    win=0
    if roll[0]==roll[1]==roll[2]:
        win=bet*5
        p["balance"]+=win
    save_data()
    await update.message.reply_text(f"{roll}\n{'🎉 Вы выиграли '+str(win)+'💰!' if win else '😢 Проигрыш'}")

async def coin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p=get_player(str(update.effective_user.id))
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Используй: /coin <ставка>")
        return
    bet=int(context.args[0])
    if bet>p["balance"]:
        await update.message.reply_text("❌ Недостаточно денег")
        return
    p["balance"]-=bet
    res=random.choice(["Орёл","Решка"])
    win=bet*2 if random.choice([True,False]) else 0
    p["balance"]+=win
    save_data()
    await update.message.reply_text(f"🪙 {res}\n{'🎉 Вы выиграли '+str(win)+'💰!' if win else '😢 Проигрыш'}")

async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    p=get_player(str(update.effective_user.id))
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Используй: /dice <ставка>")
        return
    bet=int(context.args[0])
    if bet>p["balance"]:
        await update.message.reply_text("❌ Недостаточно денег")
        return
    p["balance"]-=bet
    roll=random.randint(1,6)
    win=bet*roll if roll>=4 else 0
    p["balance"]+=win
    save_data()
    await update.message.reply_text(f"🎲 Выпало {roll}\n{'🎉 Вы выиграли '+str(win)+'💰!' if win else '😢 Проигрыш'}")

# ================== Мини-игры ==================
async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Угадай число: /guess <число от 1 до 10>")
        return
    user_guess=int(context.args[0])
    number=random.randint(1,10)
    if user_guess==number:
        await update.message.reply_text(f"🎉 Правильно! Было {number}")
    else:
        await update.message.reply_text(f"❌ Неправильно! Было {number}")

# ================== Мемы ==================
memes=["КОГДА КОД РАБОТАЕТ","КОГДА НАШЕЛ БАГ","КОГДА СПАМ В ЧАТЕ","КОГДА ПРЕДПРОЕКТ ГОТОВ"]
async def mem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет случайный мем текстом (без PIL)"""
    meme_text = random.choice(memes)
    await update.message.reply_text(f"😂 {meme_text}")

async def sosal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target=update.message.reply_to_message.from_user.first_name if update.message.reply_to_message else user_name(update)
    await update.message.reply_text(f"💀 {target} сосал")

jokes=["Почему программист не видит лес? Потому что он в дереве ошибок!","Код без теста — как кофе без сахара","Когда баг найден — радость неописуемая"]
async def joke(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(jokes))

# ================== События ==================
async def time_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Используй: /time <текст>")
        return
    text=" ".join(context.args)
    data["events"].append(text)
    save_data()
    await update.message.reply_text("⏱ Событие сохранено")

async def timeK(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not data["events"]:
        await update.message.reply_text("Событий нет")
        return
    await update.message.reply_text("\n".join(data["events"]))

# ================== Калькулятор ==================
async def calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text=update.message.text
    if re.fullmatch(r"[0-9+\-*/(). ]+",text):
        try:
            result=eval(text)
            await update.message.reply_text(f"🧮 {result}")
        except:
            pass

# ================== Запуск ==================
app=ApplicationBuilder().token(TOKEN).build()

# Команды
app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("helpMark",helpMark))
app.add_handler(CommandHandler("balance",balance))
app.add_handler(CommandHandler("work",work))
app.add_handler(CommandHandler("deposit",deposit))
app.add_handler(CommandHandler("withdraw",withdraw))
app.add_handler(CommandHandler("slots",slots))
app.add_handler(CommandHandler("coin",coin))
app.add_handler(CommandHandler("dice",dice))
app.add_handler(CommandHandler("guess",guess))
app.add_handler(CommandHandler("mem",mem))
app.add_handler(CommandHandler("sosal",sosal))
app.add_handler(CommandHandler("joke",joke))
app.add_handler(CommandHandler("time",time_cmd))
app.add_handler(CommandHandler("timeK",timeK))

# Сообщения: калькулятор
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, calc))

print("🚀 МЕГА-БОТ без ИИ с мини-играми, мемами (текст) и экономикой запущен!")
app.run_polling()
