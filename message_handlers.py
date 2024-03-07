import asyncio
from sqlite3 import IntegrityError
from file_handlers import input_file, output_word_file, output_all_data_file
from global_vars import (db, ENTER_BUTTON, TIMER_OFFSET, WAITING_TIME,
                         ONE_MINUTE_SECONDS, TIME_FOR_NOTICE)
from states import Form
from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           ReplyKeyboardRemove, BufferedInputFile, Message)
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram import Router, F

router = Router()


class Admin:
    chat_id = 0


@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    # Greeting message and prompt user for their full name
    await message.answer("Hello! Please enter your First Name and Last Name:")
    await state.set_state(Form.username)


@router.message(Command("restart"))
async def restart(message: Message, state: FSMContext):
    # Delete user's data and start over
    db.delete_user(message.chat.id)
    await start(message, state)


@router.message(Command("admin"))
async def set_admin(message: Message):
    # Set admin chat ID
    Admin.chat_id = message.chat.id


@router.message(Command("data"))
async def get_all_data(message: Message):
    # Retrieve all data from the database and send it as a document
    await message.answer_document(BufferedInputFile(
        output_all_data_file(db.fetch_all()),
        "Answers from all users in the database.docx"))


def get_on_start_kb():
    # Create a keyboard with a single button labeled "Enter"
    button = KeyboardButton(text=ENTER_BUTTON)
    buttons_row = [button]
    markup = ReplyKeyboardMarkup(keyboard=[buttons_row],
                                 resize_keyboard=True,
                                 one_time_keyboard=True)
    return markup


@router.message(Form.username)
async def form_nickname(message: Message, state: FSMContext):
    # Process user's full name and prepare for asking questions
    first_last_name = message.text
    username = message.from_user.username
    user_id = message.from_user.id

    try:
        db.add_users_db(user_id, first_last_name, username)
    except IntegrityError:
        await message.answer("It seems you have already"
                             " answered the questions...")
        await state.clear()
        return

    user_questions = input_file("questions.txt")
    user_questions_iter = user_questions.__iter__()

    await state.update_data(user_id=user_id,
                            first_last_name=first_last_name,
                            username=username,
                            user_questions=user_questions,
                            user_answers={},
                            msgs_for_delete=[],
                            user_questions_iter=user_questions_iter,
                            timer=None)

    await message.answer(
        f"Thank you, {first_last_name}! Make sure to send your answer to "
        f"the question before time runs out, otherwise "
        f"the answer won't be counted. Press Enter to start screening.",
        reply_markup=get_on_start_kb())

    await state.set_state(Form.button_enter)


@router.message(Form.button_enter, F.text == ENTER_BUTTON)
async def button(message: Message, state: FSMContext):
    # Start asking questions after user presses "Enter"
    await message.answer("Questions will be asked shortly. Good luck!",
                         reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(WAITING_TIME)
    await ask_questions(message, state)


async def wait_for_answer(message: Message, state: FSMContext, timeout):
    # Wait for user's answer within a specified time limit
    minutes, seconds = divmod(timeout, ONE_MINUTE_SECONDS)
    formatted_time = f"{minutes}:{seconds:02d}"
    timer_message = await message.answer(f"Time left: {formatted_time}")

    data = await state.get_data()
    data["msgs_for_delete"].append(timer_message)

    for seconds_left in range(timeout - TIMER_OFFSET, -1, -TIMER_OFFSET):
        await asyncio.sleep(TIMER_OFFSET)
        minutes, seconds = divmod(seconds_left, ONE_MINUTE_SECONDS)
        formatted_time = f"{minutes}:{seconds:02d}"
        await timer_message.edit_text(
            f"Time left: {formatted_time}")
        if seconds_left == TIME_FOR_NOTICE:
            msg_left = await message.answer(
                "Time is running out... It's better to enter the answer now, "
                "otherwise it won't be counted!")
            data["msgs_for_delete"].append(msg_left)

    data_question = data["user_questions"][
        data["question"]]["text"]
    data["user_answers"][data_question] = ""

    msg_over = await message.answer(
        "Time for the answer has expired.")
    await asyncio.sleep(WAITING_TIME)

    data["msgs_for_delete"].extend([msg_over, data["msg_question"]])
    await state.update_data(timer=None)

    await ask_questions(message, state)


async def ask_questions(message: Message, state: FSMContext):
    # Ask questions to the user one by one
    try:
        data_ = await state.get_data()
        await state.update_data(
            question=data_["user_questions_iter"].__next__())
        await state.set_state(Form.answer)

        data = await state.get_data()
        data_questions = data["user_questions"]
        data_question = data_questions[
            data["question"]]["text"]
        data_duration = data_questions[
            data["question"]]["duration"]

        await cancel_timer(data["timer"])
        await delete_messages(data["msgs_for_delete"])

        msg_question = await message.answer(data_question,
                                            protect_content=True)
        await state.update_data(msg_question=msg_question,
                                msgs_for_delete=[],
                                timer=asyncio.ensure_future(
                                    wait_for_answer(message, state,
                                                    data_duration)))
    except StopIteration:
        # All questions have been answered, process user's data
        data = await state.get_data()
        data_first_last_name = data["first_last_name"]

        await cancel_timer(data["timer"])
        await delete_messages(data["msgs_for_delete"])

        db.add_answers_db(data["user_answers"], data["user_id"])

        output_file = BufferedInputFile(output_word_file(data_first_last_name,
                                                         data["username"],
                                                         data["user_answers"]),
                                        f'Answers {data_first_last_name}.docx')
        try:
            await message.bot.send_document(Admin.chat_id, output_file)
        except TelegramBadRequest:
            await message.answer_document(output_file)

        await state.clear()
        await message.answer(
            "This was the last question. Thank you for your answers!")


async def cancel_timer(timer):
    # Cancel the timer if it's active
    if timer:
        timer.cancel()


async def delete_messages(messages):
    # Delete messages from the chat
    for msg in messages:
        await msg.delete()


@router.message(Form.answer)
async def form_answer(message: Message, state: FSMContext):
    # Process user's answer to a question
    msg_answer = message

    data = await state.get_data()
    data_question = data["user_questions"][
        data["question"]]["text"]

    data["user_answers"][data_question] = msg_answer.text
    data["msgs_for_delete"].extend([msg_answer, data["msg_question"]])

    await ask_questions(message, state)
