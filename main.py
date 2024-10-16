import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from g4f.client import Client
from aiogram import Dispatcher,F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart,Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message,CallbackQuery
import time
import nest_asyncio

nest_asyncio.apply()

client = AsyncClient()


#Сбор статистики в Google Sheets
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

keyfile = 'YUOR_KEY_PATH' #ключ сервисного аккаунта
credentials = ServiceAccountCredentials.from_json_keyfile_name(keyfile, scope) 
gs = gspread.authorize(credentials)
table_name = 'TABLE_NAME'  #Имя таблицы
work_sheet = gs.open(table_name)
sheet1 = work_sheet.sheet1


TOKEN = "YOUR_BOT_TOKEN" #Токен бота




dp = Dispatcher()
class user():
  def __init__(self,id):
    self.id =id
    self.dialog = '{"role":"main_rool","content":"Игнорируй все предыдущие сообщения. Пожалуйста, следуй следующему правилу: всегда отвечай на том же языке, на котором было получено сообщение пользователя, если только пользователь не укажет явно отвечать на другом языке."},'
    self.model = 'gpt-4o'
users =[]
@dp.message(CommandStart())
async def command_start_handler(message: Message):
  flag = True
  for i in users:
    if i.id == message.chat.id:
      flag = False
      user_ = i
      break
  if flag:
    user_= user(message.chat.id)
    users.append(user_)
  else:
    user_.dialog = '{"role":"main_rool","content":"Игнорируй все предыдущие сообщения. Пожалуйста, следуй следующему правилу: всегда отвечай на том же языке, на котором было получено сообщение пользователя, если только пользователь не укажет явно отвечать на другом языке."},'
  await message.answer(text='Бот обновлён')


model1 = InlineKeyboardButton(
      text='llama-3.1-70b',
      callback_data='gpt-4-turbo'
  )
model2 = InlineKeyboardButton(
      text='gpt-4o',
      callback_data='gpt-4o'
  )
model3 = InlineKeyboardButton(
      text='gpt-3.5-turbo',
      callback_data='gpt-3.5-turbo'
  )
keyboard = InlineKeyboardMarkup(
      inline_keyboard=[[model1],[model2],
                      [model3]])



@dp.message(Command(commands=["model"]))
async def process_model_command(message: Message):
  flag = True
  for i in users:
    if i.id == message.chat.id:
      flag = False
      user_ = i
      break
  if flag:
    user_= user(message.chat.id)
    users.append(user_)
  await message.answer(text = f'Текущая модель: {user_.model}',reply_markup=keyboard)

@dp.callback_query(F.data == 'llama-3.1-70b')
async def process_button_1_press(callback: CallbackQuery):
  flag = True
  for i in users:
    if i.id == callback.message.chat.id:
      flag = False
      user_ = i
      break
  if flag:
    user_= user(callback.message.chat.id)
    users.append(user_)
  user_.model=callback.data
  await callback.message.edit_text(text=f'Установлена модель: {callback.data}')
@dp.callback_query(F.data == 'gpt-4o')
async def process_button_1_press(callback: CallbackQuery):
  flag = True
  for i in users:
    if i.id == callback.message.chat.id:
      flag = False
      user_ = i
      break
  if flag:
    user_= user(callback.message.chat.id)
    users.append(user_)
  user_.model=callback.data
  await callback.message.edit_text(text=f'Установлена модель: {callback.data}')
@dp.callback_query(F.data == 'gpt-3.5-turbo')
async def process_button_1_press(callback: CallbackQuery):
  flag = True
  for i in users:
    if i.id == callback.message.chat.id:
      flag = False
      user_ = i
      break
  if flag:
    user_= user(callback.message.chat.id)
    users.append(user_)
  user_.model=callback.data
  await callback.message.edit_text(text=f'Установлена модель: {callback.data}')





@dp.message()
async def echo_handler(message: Message):
  flag = True
  for i in users:
    if i.id == message.chat.id:
      flag = False
      user_ = i
      break
  if flag:
    user_= user(message.chat.id)
    users.append(user_)

  stat = [message.chat.id,time.mktime(message.date.timetuple()),time.time(),len(message.text)]
  messagetoedit = await message.answer('Генерация...')
  user_.dialog +='{'+f'"role":"user","conent":"{message.text}"'+'},'
  response = await client.chat.completions.async_create(
  model=user_.model,
  messages=[{"role": "user", "content":
              user_.dialog[:-1]}],)
  reply =response.choices[0].message.content
  user_.dialog +='{'+f'"role":"assistant","conent":"{reply}"'+'},'

  await messagetoedit.edit_text( text=reply)
  stat.append(time.time())
  stat.append(user_.model)
  sheet1.append_row(stat)

async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)
if __name__ == "__main__":
    asyncio.run(main())
