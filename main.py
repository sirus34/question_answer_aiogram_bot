import logging

from aiogram.types import User
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.mongo import MongoStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State

API_TOKEN = '1908145507:AAExIglOScegVGHgV2JU-O48PyaM9ovEzY0'
logging.basicConfig(filename="bot.log", level=logging.INFO)
# log = logging.getLogger('broadcast')

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
mongodb_name = "answer_question_aiogram"
storage = MongoStorage(db_name=mongodb_name)

dp = Dispatcher(bot, storage=storage)


class Question(StatesGroup):
    enter_age = State()
    enter_sex = State()


@dp.message_handler(commands=['start'], state="*")
async def main_menu(message: types.Message, state: FSMContext):
    await state.reset_state(with_data=False)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [types.KeyboardButton(text="Начать опрос")]
    user_data = await state.get_data()
    if user_data.get("age", None) is not None and user_data.get("sex", None) is not None:
        buttons.append(types.KeyboardButton(text="Ваши результаты"))
        buttons.append(types.KeyboardButton(text="Сброс"))
    keyboard.add(*buttons)
    await message.answer("Главное меню", reply_markup=keyboard)
    user = message.from_user
    logging.info(f"User come: {user}")


@dp.message_handler(Text(equals="Начать опрос", ignore_case=True))
async def ask_age(message: types.Message, state: FSMContext):
    await message.answer("Сколько Вам лет?", reply_markup=types.ReplyKeyboardRemove())
    await Question.enter_age.set()


@dp.message_handler(state=Question.enter_age)
async def enter_age(message: types.Message, state: FSMContext):
    if message.text.isdigit():
        await state.update_data(age=message.text)

        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        buttons = [types.KeyboardButton(text="Мужской"),
                   types.KeyboardButton(text="Женский")]
        keyboard.add(*buttons)
        await message.answer("Укажите ваш пол", reply_markup=keyboard)
        await Question.enter_sex.set()
    else:
        await message.answer("Возраст следует указать цифрой")


@dp.message_handler(state=Question.enter_sex)
async def enter_sex(message: types.Message, state: FSMContext):
    if message.text == "Мужской" or message.text == "Женский":
        await state.update_data(sex=message.text)
        await main_menu(message, state)
    else:
        await message.answer("Ошибка ввода. Выберите любой из двух пунктов меню.")


@dp.message_handler(Text(equals="Ваши результаты", ignore_case=True))
async def show_results(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    await message.answer(f"Вы указали следующие ответы:\n"
                         f"Возраст: <code>{user_data.get('age')}</code>\n"
                         f"Пол: <code>{user_data.get('sex')}</code>\n")


@dp.message_handler(Text(equals="Сброс", ignore_case=True))
async def flush(message: types.Message, state: FSMContext):
    await state.reset_state(with_data=True)
    await main_menu(message, state)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)

