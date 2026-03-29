import telebot
from telebot.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton, MenuButtonWebApp

# ВНИМАНИЕ: Сюда нужно вставить твой токен от BotFather
TOKEN = "8645219490:AAF1s6ePsBJODfRduO9L2s3MbNsAHlbLkkU"

bot = telebot.TeleBot(TOKEN)

# 1. Системная кнопка МЕНЮ (работает везде, висит слева внизу)
bot.set_chat_menu_button(
    menu_button=MenuButtonWebApp(type='web_app', text='🛠 AI Scanner', web_app=WebAppInfo(url="https://softhunterpro.com/ai-car-diagnostic-app/"))
)

# Реакция на команду /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    # 2. Инлайн-кнопка прямо под сообщением (100% поддержка в Telegram Web)
    inline_markup = InlineKeyboardMarkup()
    web_app = WebAppInfo(url="https://softhunterpro.com/ai-car-diagnostic-app/")
    inline_markup.add(InlineKeyboardButton(text="🛠️ Open AI Scanner", web_app=web_app))

    text = (
        "Hello! I am the AI-Garage Assistant 🤖\n\n"
        "I can help you diagnose engine noises (belt squeal, valve tick, knocking) "
        "and save you $100+ on mechanic fees.\n\n"
        "Click the button below to launch our Free Neural Scanner directly!"
    )
    bot.send_message(message.chat.id, text, reply_markup=inline_markup)

# Реакция, если человек кидает аудио или голосовое сообщение
@bot.message_handler(content_types=['audio', 'voice', 'document'])
def handle_audio(message):
    inline_markup = InlineKeyboardMarkup()
    inline_markup.add(InlineKeyboardButton(text="Start AI Scan on Website", url="https://softhunterpro.com/ai-car-diagnostic-app/"))
    
    text = (
        "Got it! 🎧 To process this sound through our full neural network "
        "and get specific Amazon part recommendations, please upload it to our web scanner 👇"
    )
    bot.reply_to(message, text, reply_markup=inline_markup)

# Реакция на любой другой текст
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    inline_markup = InlineKeyboardMarkup()
    web_app = WebAppInfo(url="https://softhunterpro.com/ai-car-diagnostic-app/")
    inline_markup.add(InlineKeyboardButton(text="🛠️ Open AI Scanner", web_app=web_app))
    
    bot.reply_to(message, "Please click the button below to diagnose your engine sound!", reply_markup=inline_markup)

if __name__ == "__main__":
    print("🤖 Бот успешно запущен с Инлайн-кнопками и готов к работе...")
    bot.polling(none_stop=True)