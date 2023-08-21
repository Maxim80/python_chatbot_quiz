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
from functools import partial
from dotenv import dotenv_values
import json
import logging
import enum
import argparse



logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class DialogStatus(enum.Enum):
    USER_CHOICE = 0


def start(update: Update, context: CallbackContext, db: Redis) -> DialogStatus:
    reply_keyboard = [['Новый вопрос', 'Сдаться'], ['Мой счет']]
    markup = ReplyKeyboardMarkup(reply_keyboard)

    user_id = update.effective_user.id
    user_statistics = {'question': None, 'answer': None, 'counter': 0}
    db.set(user_id, json.dumps(user_statistics))

    update.message.reply_text(
        'Привет! Я бот для викторины.',
        reply_markup=markup
    )
    return DialogStatus.USER_CHOICE


def handler_new_question_request(
            update: Update,
            context: CallbackContext,
            questions: dict,
            db: Redis) -> DialogStatus:
    user_id = update.effective_user.id
    user_statistics = json.loads(db.get(user_id))
    try:
        question, answer = questions.popitem()
    except KeyError:
        question = 'Конец викторины. Вы ответили на все вопросы.'
    else:
        user_statistics['question'], user_statistics['answer'] = question, answer
        db.set(user_id, json.dumps(user_statistics))
    
    update.message.reply_text(question)
    return DialogStatus.USER_CHOICE


def handler_solution_attempt(
        update: Update, context: CallbackContext, db: Redis) -> DialogStatus:
    user_id = update.effective_user.id
    user_answer = update.message.text
    user_statistics = json.loads(db.get(user_id))

    question, correct_answer = user_statistics['question'], user_statistics['answer']

    if check_answer(question, user_answer, correct_answer):
        message = 'Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос"'
        user_statistics['counter'] += 1
        db.set(user_id, json.dumps(user_statistics))
    else:
        message = 'Неправильно… Попробуешь ещё раз?'
    
    update.message.reply_text(message)
    return DialogStatus.USER_CHOICE


def handler_surrender_request(
            update: Update,
            context: CallbackContext,
            db: Redis) -> DialogStatus:
    user_id = update.effective_user.id
    user_statistics = json.loads(db.get(user_id))
    question, answer = user_statistics['question'], user_statistics['answer']
    update.message.reply_text(answer)
    return DialogStatus.USER_CHOICE


def handler_counter_request(
            update: Update,
            context: CallbackContext,
            db: Redis) -> DialogStatus:
    user_id = update.effective_user.id
    user_statistics = json.loads(db.get(user_id))
    update.message.reply_text(user_statistics['counter'])
    return DialogStatus.USER_CHOICE


def main(questions_dir: str) -> None:
    config = dotenv_values('.env')
    print(config)

    updater = Updater(config['TELEGRAM_TOKEN'])
    dispatcher = updater.dispatcher

    redis_db = Redis(
        host=config['REDIS_URL'],
        port=config['REDIS_PORT'],
        password=config['REDIS_PASSW'],
    )

    questions = get_questions(questions_dir)

    start_quiz = partial(start, db=redis_db)
    new_question = partial(handler_new_question_request,
        questions=questions, db=redis_db)
    solution_attempt = partial(handler_solution_attempt, db=redis_db)
    sorrender = partial(handler_surrender_request, db=redis_db)
    counter = partial(handler_counter_request, db=redis_db)

    conv_handler = ConversationHandler(
        entry_points = [CommandHandler('start', start_quiz),],
        states = {
            DialogStatus.USER_CHOICE: [
                MessageHandler(Filters.regex(r'^Новый вопрос$'), new_question),
                MessageHandler(Filters.regex(r'^Сдаться$'), sorrender),
                MessageHandler(Filters.regex(r'^Мой счет$'), counter),
                MessageHandler(Filters.text, solution_attempt),
            ]
        },
        fallbacks = [],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Чатбот для месенджера Telegram для проведения викторин.'
    )
    parser.add_argument(
        '-p', '--path',
        default='quiz-questions',
        help='Путь к директории с вопросами для викторины.'
    )
    args = parser.parse_args()
    main(args.path)
