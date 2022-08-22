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
    download(message, link)


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


def download(message, link):  # download media by user request
    try:
        youtube_media = YouTube(link)  # pytube lib
        user_id = message.from_user.id
        mode = user_mode_check(user_id)
        length = youtube_media.length  # if the video is too long - do not start downloading

        if mode == 1 and length >= 900 or mode == 2 and length >= 900:
            bot.send_message(message.chat.id, f"The video that you want to download is too large.\n"
                                              f"Video that was found by your request is [here]({link}).\n\n"
                                              f"For try to download this content as audio only - "
                                              f"change your mode to *3* using /settings command. Or change your "
                                              f"searching request for download another video.", parse_mode="Markdown")
        elif mode == 3 and length >= 4200:
            bot.send_message(message.chat.id, f"The audio that you want to download is too large. "
                                              f"Audio that was found by your request is [here]({link}).\n\n"
                                              f"Please, try to change your searching request.", parse_mode="Markdown")
        else:
            bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id + 1,
                                  text="Your media download has begun ⬇")
            if mode == 1:
                youtube_video = youtube_media.streams.get_lowest_resolution().download()
                upload(message, "video", youtube_video)
                youtube_audio = youtube_media.streams.get_audio_only().download()
                upload(message, "audio", youtube_audio)
            elif mode == 2:
                youtube_video = youtube_media.streams.get_lowest_resolution().download()
                upload(message, "video", youtube_video)
            elif mode == 3:
                youtube_audio = youtube_media.streams.get_audio_only().download()
                upload(message, "audio", youtube_audio)
    except Exception as ex:
        print(ex)
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id + 1,
                              text="Your request cannot be downloaded ✖")


def upload(message, file_type, file_name):  # upload media to Telegram
    file = open(f"{file_name}", "rb")
    try:
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id + 1,
                              text=f"Your {file_type} is starting to upload ⬆")
        if file_type == "video":
            bot.send_video(message.chat.id, file, timeout=240)
        elif file_type == "audio":
            bot.send_audio(message.chat.id, file, timeout=120)
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id + 1,
                              text=f"Your {file_type} was successfully sent ✔")
    except Exception as ex:
        print(ex)
        bot.edit_message_text(chat_id=message.chat.id, message_id=message.message_id + 1,
                              text=f"Your {file_type} is failed to upload ✖")
        bot.send_message(message.chat.id, f"This {file_type} cannot be uploaded to the Telegram servers, because the "
                                          f"{file_type} is over the size limit. Try to change your request.")
    file.close()
    os.remove(file_name)


def user_mode_check(user_id):
    db_object.execute(f"SELECT mode FROM users WHERE user_id = {user_id}")
    result = db_object.fetchone()
    return result[0]


def buttons(message):
    user_id = message.from_user.id
    mode = user_mode_check(user_id)

    keyboard = types.InlineKeyboardMarkup()
    button_one = types.InlineKeyboardButton(text="Mode 1️⃣", callback_data="mode_one")
    button_two = types.InlineKeyboardButton(text="Mode 2️⃣", callback_data="mode_two")
    button_three = types.InlineKeyboardButton(text="Mode 3️⃣", callback_data="mode_three")
    keyboard.add(button_one, button_two, button_three)

    bot.send_message(message.chat.id, f"Choose mode of bot work.\n"
                                      f"Your mode now is {mode}.", parse_mode="Markdown", reply_markup=keyboard)


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
