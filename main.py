import logging

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.mongo import MongoStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.callback_data import CallbackData

from local_vars import API_TOKEN

# logging.basicConfig(filename="bot.log", level=logging.INFO)
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, parse_mode=types.ParseMode.HTML)
mongodb_name = "answer_question_aiogram"
storage = MongoStorage(db_name=mongodb_name)

dp = Dispatcher(bot, storage=storage)
cb_place = CallbackData('place', 'is_city')


class Question(StatesGroup):
    enter_age = State()
    enter_sex = State()
    enter_place = State()


@dp.message_handler(commands=['start'], state="*")
async def main_menu(message: types.Message, state: FSMContext):
    await state.reset_state(with_data=False)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [types.KeyboardButton(text="Начать опрос")]
    user_data = await state.get_data()
    if user_data.get("age", None) is not None and \
            user_data.get("sex", None) is not None:
        buttons.append(types.KeyboardButton(text="Ваши результаты"))
        buttons.append(types.KeyboardButton(text="Сброс"))
    keyboard.add(*buttons)
    await message.answer("<u>Главное меню</u>", reply_markup=keyboard)
    user = message.from_user


@dp.message_handler(Text(equals="Начать опрос", ignore_case=True))
async def ask_age(message: types.Message):
    await message.answer("Сколько Вам лет?",
                         reply_markup=types.ReplyKeyboardRemove())
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
        # await main_menu(message, state)
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        cb_data = cb_place.new(is_city=True)
        buttons = [types.InlineKeyboardButton(text="В городе", callback_data=cb_data)]
        cb_data = cb_place.new(is_city=False)
        buttons.append(types.InlineKeyboardButton(text="За городом", callback_data=cb_data))
        keyboard.add(*buttons)
        await message.answer("Где вы проживаете?", reply_markup=keyboard)
        await Question.enter_place.set()
    else:
        await message.answer("Ошибка ввода. Выберите любой из двух"
                             "пунктов меню.")


@dp.callback_query_handler(cb_place.filter(), state=Question.enter_place)
async def place_choose(call: types.CallbackQuery, callback_data: dict, state: FSMContext):
    is_city = callback_data.get("is_city", None)
    if is_city is not None:
        await state.update_data(is_city=is_city)
        await call.message.answer(text="<b><u>Спасибо за Ваши ответы!</u></b> 👍\n\n")
        await call.answer("")
        await main_menu(call.message, state)


@dp.message_handler(Text(equals="Ваши результаты", ignore_case=True))
async def show_results(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    if user_data.get('is_city') is True:
        place = "Город"
    else:
        place = "Загород"
    await message.answer(f"Вы указали следующие ответы:\n"
                         f"Возраст: <code>{user_data.get('age')}</code>\n"
                         f"Пол: <code>{user_data.get('sex')}</code>\n"
                         f"Место проживания: <code>{place}</code>")


@dp.message_handler(Text(equals="Сброс", ignore_case=True))
async def flush(message: types.Message, state: FSMContext):
    await state.reset_state(with_data=True)
    await main_menu(message, state)


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=False)
