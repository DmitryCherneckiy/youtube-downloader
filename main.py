import os
import logging
import requests
import psycopg2
import telebot
from telebot import types
from pytube import YouTube
from config import BOT_TOKEN, DB_URL


bot = telebot.TeleBot(BOT_TOKEN)
logger = telebot.logger
logger.setLevel(logging.DEBUG)
db_connection = psycopg2.connect(DB_URL, sslmode="require")
db_object = db_connection.cursor()


@bot.message_handler(commands=["start"])
def start_message(message):  # add user_id to database and sending welcome message.
    user_id = message.from_user.id

    db_object.execute(f"SELECT user_id FROM users WHERE user_id = {user_id}")
    result = db_object.fetchone()
    if not result:
        db_object.execute("INSERT INTO users (user_id) VALUES (%s)", [user_id])
        db_connection.commit()

    bot.send_message(message.chat.id, "This bot can download any music from YouTube. For start downloading - "
                                      "send your searching request to the bot.\n\n"
                                      "The bot has 3 modes of work:\n"
                                      "1️⃣ - Download video and audio (default).\n"
                                      "2️⃣ - Download only video.\n"
                                      "3️⃣ - Download only audio.\n\n"
                                      "If you want to change your mode - use the /settings command.")


@bot.message_handler(commands=["settings"])  # bot mode selection
def call_settings_buttons(message):
    buttons(message)


@bot.message_handler(content_types=["text"])
def text_handler(message):
    request_from_user = message.text
    link = search(request_from_user)
    bot.send_message(message.chat.id, "Your request was found ✔")


def search(topic):
    url = f"https://www.youtube.com/results?q={topic}"
    count = 0
    request = requests.get(url)
    data = request.content
    data = str(data)
    lst = data.split('"')
    for i in lst:
        count += 1
        if i == "WEB_PAGE_TYPE_WATCH":
            break
    return f"https://www.youtube.com{lst[count - 5]}"


def buttons(message):
    user_id = message.from_user.id
    db_object.execute(f"SELECT mode FROM users WHERE user_id = {user_id}")
    result = db_object.fetchone()
    user_mode = result[0]  # user mode check

    keyboard = types.InlineKeyboardMarkup()
    button_one = types.InlineKeyboardButton(text="Mode 1️⃣", callback_data="mode_one")
    button_two = types.InlineKeyboardButton(text="Mode 2️⃣", callback_data="mode_two")
    button_three = types.InlineKeyboardButton(text="Mode 3️⃣", callback_data="mode_three")
    keyboard.add(button_one, button_two, button_three)

    bot.send_message(message.chat.id, f"Choose mode of bot work.\n"
                                      f"Your mode now is {user_mode}.", parse_mode="Markdown", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def buttons_handler(call):  # mode switches
    user_id = call.from_user.id
    if call.data == "mode_one":
        db_object.execute(f"UPDATE users SET mode = 1 WHERE user_id = {user_id}")
        bot.send_message(call.message.chat.id, "Your mode was set to 1️⃣\n"
                                               "Video and audio download.")
    elif call.data == "mode_two":
        db_object.execute(f"UPDATE users SET mode = 2 WHERE user_id = {user_id}")
        bot.send_message(call.message.chat.id, "Your mode was set to 2️⃣\n"
                                               "Only video download.")
    elif call.data == "mode_three":
        db_object.execute(f"UPDATE users SET mode = 3 WHERE user_id = {user_id}")
        bot.send_message(call.message.chat.id, "Your mode was set to 3️⃣\n"
                                               "Only audio download.")
    db_connection.commit()


if __name__ == '__main__':
    bot.polling(True)
