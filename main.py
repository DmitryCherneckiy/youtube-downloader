import os
import logging
import requests
import psycopg2
import telebot
from telebot import types
from pytube import YouTube
from config import BOT_TOKEN, DB_URL


bot = telebot.TeleBot(BOT_TOKEN)
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


if __name__ == '__main__':
    bot.polling(True)
