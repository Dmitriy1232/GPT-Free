import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from g4f.client import Client
from aiogram import Dispatcher, F, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery, ContentType
import time
import nest_asyncio
import configparser
from pydub import AudioSegment
from io import BytesIO
import speech_recognition as sr

nest_asyncio.apply()

client = Client()

config = configparser.ConfigParser()

config.read('config.ini')

# Сбор статистики в Google Sheets
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

keyfile = config.get('Data', 'keyfile')  # ключ сервисного аккаунта
credentials = ServiceAccountCredentials.from_json_keyfile_name(keyfile, scope)
gs = gspread.authorize(credentials)
table_name = config.get('Data', 'table_name')  # Имя таблицы
work_sheet = gs.open(table_name)
sheet1 = work_sheet.sheet1

dp = Dispatcher()
TOKEN = config.get('Data', 'TOKEN')  # Токен бота
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


class users():
    users = []
    system_mes = [{'user': 'system', 'content': config.get('Data', 'system_mes')}]

    class user():
        def __init__(self, id):
            self.id = id
            self.dialog = users.system_mes
            self.model = config.get('Data', 'start_model')

    def create_user(id):
        users.users.append(users.user(id))

    def get_user(id):
        for i in users.users:
            if i.id == id:
                return i
        users.create_user(id)
        return users.get_user(id)


class create_models():
    def __init__(self, models, dp):
        self.dp = dp
        self.models = models
        self.keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=i, callback_data=i)] for i in self.models])
        for model in models:
            self.create_dec(model, dp)

    def create_dec(self, model, dp):
        @self.dp.callback_query(F.data == model)
        async def model_choose_push(callback):
            user_ = users.get_user(callback.message.chat.id)
            user_.model = callback.data
            await callback.message.edit_text(text=f'Установлена модель: {callback.data}')


models = create_models(config.get('Data', 'models').split(', '), dp)


@dp.message(Command(commands=["start"]))
async def command_start_handler(message: Message):
    user_ = users.get_user(message.chat.id)
    user_.dialog = users.system_mes
    await message.answer(text='Бот обновлён')


@dp.message(Command(commands=["feedback"]))
async def command_start_handler(message: Message):
    await message.answer(text='Переходи ->> t.me/gpt_by_dimas')


@dp.message(Command(commands=["model"]))
async def process_model_command(message: Message):
    user_ = users.get_user(message.chat.id)
    await message.answer(text=f'Текущая модель: {user_.model}', reply_markup=models.keyboard)


@dp.message(F.content_type == ContentType.VOICE)
async def voice_message_handler(message: Message):
    user_ = users.get_user(message.chat.id)
    file = await bot.get_file(message.voice.file_id)
    file = await bot.download_file(file.file_path)
    audio = AudioSegment.from_ogg(BytesIO(file.getvalue()))
    wav_io = BytesIO()
    audio.export(wav_io, format='wav')
    wav_io.seek(0)
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_io) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language="ru-RU")
            await message.answer(text=f"Распознанный текст: {text}")
            stat = [message.chat.id, time.mktime(message.date.timetuple()), time.time(), len(text)]
            messagetoedit = await message.answer('Генерация...')
            user_.dialog.append({"role": "user", "content": text})
            response = await client.chat.completions.async_create(
                model=user_.model,
                messages=user_.dialog)
            reply = response.choices[0].message.content
            user_.dialog.append({"role": "assistant", "content": reply})

            await messagetoedit.edit_text(text=reply)
            stat.append(time.time())
            sheet1.append_row(stat)
        except:
            await message.answer(text="Не удалось распознать аудио.")


@dp.message()
async def echo_handler(message: Message):
    user_ = users.get_user(message.chat.id)

    stat = [message.chat.id, time.mktime(message.date.timetuple()), time.time(), len(message.text)]
    messagetoedit = await message.answer('Генерация...')
    user_.dialog.append({"role": "user", "content": message.text})
    response = await client.chat.completions.async_create(
        model=user_.model,
        messages=user_.dialog)
    reply = response.choices[0].message.content
    user_.dialog.append({"role": "assistant", "content": reply})

    await messagetoedit.edit_text(text=reply)
    stat.append(time.time())
    sheet1.append_row(stat)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
