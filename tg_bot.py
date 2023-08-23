from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Updater,
    CallbackContext,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    Filters,
)
from questions import get_questions, check_answer
from redis import Redis
from dotenv import dotenv_values
import json
import logging
import enum
import argparse
import random


logger = logging.getLogger(__name__)


class DialogStatus(enum.Enum):
    USER_CHOICE = 0


def start(update: Update, context: CallbackContext) -> DialogStatus:
    reply_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    markup = ReplyKeyboardMarkup(reply_keyboard)

    user_id = update.effective_user.id
    user_statistics = {'question': None, 'counter': 0}
    context.bot_data['db'].set(user_id, json.dumps(user_statistics))

    update.message.reply_text(
        'Привет! Я бот для викторины.',
        reply_markup=markup
    )

    logger.info(f'Пользователь {user_id} начал викторину.')

    return DialogStatus.USER_CHOICE


def handler_new_question_request(
                    update: Update, context: CallbackContext) -> DialogStatus:
    user_id = update.effective_user.id
    user_statistics = json.loads(context.bot_data['db'].get(user_id))
    question = random.choice(list(context.bot_data['questions'].keys()))
    user_statistics['question'] = question
    context.bot_data['db'].set(user_id, json.dumps(user_statistics))
    update.message.reply_text(question)
    return DialogStatus.USER_CHOICE


def handler_solution_attempt(
                    update: Update, context: CallbackContext) -> DialogStatus:
    user_id = update.effective_user.id
    user_answer = update.message.text
    user_statistics = json.loads(context.bot_data['db'].get(user_id))

    question = user_statistics['question']
    correct_answer = context.bot_data['questions'][question]

    if check_answer(question, user_answer, correct_answer):
        message = 'Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос"'
        user_statistics['counter'] += 1
        context.bot_data['db'].set(user_id, json.dumps(user_statistics))
    else:
        message = 'Неправильно… Попробуешь ещё раз?'
    
    update.message.reply_text(message)
    return DialogStatus.USER_CHOICE


def handler_surrender_request(
                    update: Update, context: CallbackContext) -> DialogStatus:
    user_id = update.effective_user.id
    user_statistics = json.loads(context.bot_data['db'].get(user_id))
    answer = context.bot_data['questions'][user_statistics['question']]
    update.message.reply_text(answer)
    return DialogStatus.USER_CHOICE


def handler_counter_request(
                    update: Update, context: CallbackContext) -> DialogStatus:
    user_id = update.effective_user.id
    user_statistics = json.loads(context.bot_data['db'].get(user_id))
    update.message.reply_text(user_statistics['counter'])
    return DialogStatus.USER_CHOICE


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Чатбот для месенджера Telegram для проведения викторин.'
    )
    parser.add_argument(
        '-p', '--path',
        default='quiz-questions',
        help='Путь к директории с вопросами для викторины.'
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    config = dotenv_values('.env')

    redis_db = Redis(
        host=config['REDIS_URL'],
        port=config['REDIS_PORT'],
        password=config['REDIS_PASSW'],
    )

    updater = Updater(config['TELEGRAM_TOKEN'])
    dispatcher = updater.dispatcher
    dispatcher.bot_data['questions'] = get_questions(args.path)
    dispatcher.bot_data['db'] = redis_db

    conv_handler = ConversationHandler(
        entry_points = [CommandHandler('start', start),],
        states = {
            DialogStatus.USER_CHOICE: [
                MessageHandler(
                    Filters.regex(r'^Новый вопрос$'),
                    handler_new_question_request
                ),
                MessageHandler(
                    Filters.regex(r'^Сдаться$'), handler_surrender_request),
                MessageHandler(
                    Filters.regex(r'^Мой счет$'), handler_counter_request),
                MessageHandler(Filters.text, handler_solution_attempt),
            ]
        },
        fallbacks = [],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
