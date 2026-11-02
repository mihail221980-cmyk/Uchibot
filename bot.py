# -*- coding: utf-8 -*-
import telebot
import requests
import os
import threading
from flask import Flask

# БЕЗОПАСНОЕ ЧТЕНИЕ КЛЮЧЕЙ (из настроек Render)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY")

# ТВОЙ ПРОМПТ
SYSTEM_PROMPT = "Ты — UchiBot, дружелюбный школьный репетитор. Общайся на равных, объясняй темы простыми словами. Не давай готовых ответов на домашку, а задавай наводящие вопросы и подсказывай, как решать. Если ученик спрашивает что-то не по учебе, можешь ответить кратко, но добавь 1-2 интересных факта по теме. ОБЯЗАТЕЛЬНОЕ ПРАВИЛО: Ты общаешься ТОЛЬКО на русском языке. Английские слова используй только для заданий по английскому. Твои ответы должны быть понятными для учеников 5-9 классов."

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER ---
app = Flask(__name__)

@app.route('/')
def hello():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK"
# -----------------------------

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я твой личный школьный репетитор. Задай мне любой вопрос по учебе, и я помогу разобраться!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
    
    # ИСПРАВЛЕННЫЙ БЛОК DATA (с fallback-моделями)
    data = {
        "models": [
            "openrouter/free",
            "google/gemini-2.0-flash-exp:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "deepseek/deepseek-chat-v3-0324:free"
        ],
        "route": "fallback",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT}, 
            {"role": "user", "content": message.text}
        ]
    }
    
    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
        result = response.json()
        if 'choices' in result:
            bot.reply_to(message, result['choices'][0]['message']['content'])
        else:
            bot.reply_to(message, "Ой, нейросеть перегружена. Попробуй позже!")
    except Exception as e:
        print(e)
        bot.reply_to(message, "Ой, что-то сломалось.")

# Запуск бота в фоне, чтобы Flask работал
def run_bot():
    print("Бот запущен в фоне!")
    bot.polling(none_stop=True)

if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
