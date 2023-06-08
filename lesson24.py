import os
import json
import logging

from datetime import datetime

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from decouple import config

API_TOKEN = config('TELEGRAM_BOT_TOKEN')

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class RegistrationStudent(StatesGroup):
    first_name = State()
    last_name = State()
    age = State()
    number_phone = State()
    photo = State()
    programing_language = State()
    level = State()
    about_me = State()
    check = State()
    
levels = ['😖', '😟', '😐', '🙂', '😀']


def save_data(data, filename='students.json'):
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            json.dump([], f)
    
    with open(filename, 'r') as f:
        users = json.load(f)
    
    users.append(data)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)
    
        
    




@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    text = 'Прівіт, радий тебе бачити!\n\n' \
            'Якщо ти хочеш дізнатися, що я вмію, то напиши /help'
    await message.reply(text)

    
@dp.message_handler(commands=['help'])
async def help_command(message: types.Message):
    await message.reply("Я бот для навчання Python. Поки що я вмію тільки це.")

@dp.message_handler(commands=['reg'])
async def reg_command(message: types.Message):
    await message.reply("Вітаю в Університеті HILLEL!\n" \
                        "Для реєстрації треба відповісти на кілька питань.\n" \
                        "Ваше ім'я?")
    logging.info(f"User {message.from_user.id} start registration")
    await RegistrationStudent.first_name.set()
    
@dp.message_handler(state=RegistrationStudent.first_name)
async def answer_first_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text) # Записуємо в state дані з першого питання
    await message.reply("Ваше прізвище?")
    logging.info(f"User {message.from_user.id} answer on question 1")
    await RegistrationStudent.next() # Переходимо до наступного питання

@dp.message_handler(state=RegistrationStudent.last_name)
async def answer_last_name(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await message.reply("Напишіть дату свого народження в форматі дд.мм.рррр\n Наприклад: 30.01.2000")
    logging.info(f"User {message.from_user.id} answer on question 2")
    await RegistrationStudent.next()

@dp.message_handler(state=RegistrationStudent.age)
async def answer_age(message: types.Message, state: FSMContext):
    try:
        user_age = datetime.strptime(message.text, '%d.%m.%Y')
    except ValueError:
        await message.reply("Ви ввели неправильний формат дати. Спробуйте ще раз")
        return
        
    await state.update_data(age=message.text)
    murkup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    murkup.add(types.KeyboardButton("Відправити свій номер телефону", request_contact=True))
    await message.reply("Відправте свій номер телефону\n 🔽Нажміть на кнопку нижче🔽", reply_markup=murkup)
    logging.info(f"User {message.from_user.id} answer on question 3")
    await RegistrationStudent.next()
    
@dp.message_handler(state=RegistrationStudent.number_phone, content_types=types.ContentTypes.CONTACT)
async def answer_number_phone(message: types.Message, state: FSMContext):
    await state.update_data(number_phone=message.contact.phone_number)
    await message.reply("Відправте своє фото в профіль або 3х4", reply_markup=types.ReplyKeyboardRemove())
    logging.info(f"User {message.from_user.id} answer on question 4")
    await RegistrationStudent.next()
    

@dp.message_handler(state=RegistrationStudent.photo, content_types=types.ContentTypes.PHOTO)
async def answer_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    murkup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    murkup.add(types.KeyboardButton("Python"), types.KeyboardButton("Java"), types.KeyboardButton("C#"), types.KeyboardButton("C++"))
    await message.reply("Виберіть мову програмування, яку хочете вивчати", reply_markup=murkup)
    logging.info(f"User {message.from_user.id} answer on question 5")
    await RegistrationStudent.next()
    
@dp.message_handler(state=RegistrationStudent.programing_language)
async def answer_programing_language(message: types.Message, state: FSMContext):
    if message.text not in ("Python", "Java", "C#", "C++"):
        await message.reply("Виберіть мову програмування, яку хочете вивчати з клавіатури")
        return
    
    await state.update_data(programing_language=message.text)
    
    murkup = types.InlineKeyboardMarkup()
    for i, level in enumerate(levels):
        murkup.insert(types.InlineKeyboardButton(level, callback_data=str(i)))
    await message.answer("Готово!\n", reply_markup=types.ReplyKeyboardRemove())
    await message.reply("Виберіть рівень володіння мовою програмування", reply_markup=murkup)
    logging.info(f"User {message.from_user.id} answer on question 6")
    await RegistrationStudent.next()        

@dp.callback_query_handler(state=RegistrationStudent.level)
async def answer_level(call: types.CallbackQuery, state: FSMContext):
    await call.answer('Вибрано рівень володіння мовою програмування\n Дякую!', show_alert=True)
    await state.update_data(level=call.data)
    await call.message.edit_text("Напишіть про себе і що ви очікуєте від навчання")
    logging.info(f"User {call.from_user.id} answer on question 7")
    await RegistrationStudent.next()
    
@dp.message_handler(state=RegistrationStudent.about_me)
async def answer_about_me(message: types.Message, state: FSMContext):
    await state.update_data(about_me=message.text)
    data = await state.get_data()
    text = "Ваші дані:\n"
    text += f"Ім'я: {data['first_name']}\n"
    text += f"Прізвище: {data['last_name']}\n"
    text += f"Дата народження: {data['age']}\n"
    text += f"Номер телефону: {data['number_phone']}\n"
    text += f"Мова програмування: {data['programing_language']}\n"
    text += f"Рівень володіння мовою програмування: {levels[int(data['level'])]}\n"
    text += f"Про себе: {data['about_me']}\n"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👍Підтвердити", callback_data="confirm"))
    markup.add(types.InlineKeyboardButton("👎Відмінити", callback_data="cancel"))
    await message.answer_photo(data['photo'], caption=text, reply_markup=markup)
    logging.info(f"User {message.from_user.id} answer on question 8")
    await RegistrationStudent.next()

@dp.callback_query_handler(state=RegistrationStudent.check, text="confirm")
async def confirm_registration(call: types.CallbackQuery, state: FSMContext):
    await call.answer("Почекайте, реєструю вас...", show_alert=True)
    data = await state.get_data()
    save_data(data)
    await call.message.edit_caption(f"Ви успішно зареєструвались!\n\n{call.message.caption}")
    logging.info(f"User {call.from_user.id} answer on question 9")
    await state.finish()

@dp.callback_query_handler(state=RegistrationStudent.check, text="cancel")
async def cancel_registration(call: types.CallbackQuery, state: FSMContext):    
    await call.answer("Ви відмінили реєстрацію", show_alert=True)
    await call.message.delete()
    logging.info(f"User {call.from_user.id} answer on question 9")
    await state.finish()
    



if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    

