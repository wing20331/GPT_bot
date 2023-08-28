import telebot
import openai
import urllib.request
import io
import speech_recognition as sr
from pydub import AudioSegment
import tempfile
import os
from gtts import gTTS

TOKEN = "6169631938:AAHD4zPWDNzWHmL4Dotl_9UlWsA1G4JlhEo"
CHAT_ID = "-1001942807627"
bot = telebot.TeleBot(TOKEN)

openai.api_key = "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"

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет, я телеграм бот Александр! Иногда Алиса и Андрей))")

@bot.message_handler(commands=['help'])
def help(message):
    bot.reply_to(message, "Я могу все! Только задай вопрос правильно)")

def send_message_to_chat(chat_id, message):
    bot.send_message(chat_id, message)

@bot.message_handler(content_types=['voice'])
def voice_handler(message):
    if message.voice.duration < 2:
        bot.reply_to(message, "Ваше голосовое сообщение слишком короткое. Пожалуйста, отправьте сообщение длительностью более двух секунд.")
        return

    voice_info = bot.get_file(message.voice.file_id)
    voice_file = urllib.request.urlopen(f'https://api.telegram.org/file/bot{TOKEN}/{voice_info.file_path}').read()

    with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as f:
        f.write(voice_file)
        audio_segment = AudioSegment.from_file(f.name, format='ogg')
        audio_wav = io.BytesIO()
        audio_segment.export(audio_wav, format='wav')
        audio_wav.seek(0)

    os.remove(f.name)

    recognizer = sr.Recognizer()
    with sr.AudioFile(audio_wav) as source:
        audio = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio, language='ru-RU')
        except sr.UnknownValueError:
            bot.reply_to(message, "Я не понимаю, что вы говорите. Повторите, пожалуйста!")
            return

        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=text,
            temperature=0.1,
            max_tokens=1024,
            top_p=1.0,
            frequency_penalty=0.5,
            presence_penalty=0.0,
        )
        response_text = response.choices[0].text.strip()

        log_message = f"{message.from_user.username}: {text}\nБот: {response_text}\n"
        send_message_to_chat(CHAT_ID, log_message)

        bot.reply_to(message, response_text)

        voice_file = text_to_voice(response_text)
        with open(voice_file, 'rb') as f:
            bot.send_voice(message.chat.id, f)
        try:
            os.remove(voice_file)
        except FileNotFoundError:
            print(f"File {voice_file} not found")

def text_to_voice(text, language='ru'):
    tts = gTTS(text, lang=language)
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
        tts.save(f.name)

    return f.name

@bot.message_handler(func=lambda message: True)
def text_handler(message):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=message.text,
        temperature=0.1,
        max_tokens=4000,
        top_p=1.0,
        frequency_penalty=0.5,
        presence_penalty=0.0,
    )
    response_text = response.choices[0].text.strip()

    log_message = f"{message.from_user.username}: {message.text}\nБот: {response_text}\n"
    send_message_to_chat(CHAT_ID, log_message)

    bot.reply_to(message, response_text)

    voice_file = text_to_voice(response_text)
    with open(voice_file, 'rb') as f:
        bot.send_voice(message.chat.id, f)
    try:
        os.remove(f.name)
    except FileNotFoundError:
        pass

bot.polling()

