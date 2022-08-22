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


if __name__ == '__main__':
    bot.polling(True)
