from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from questions import get_questions, check_answer
from dotenv import dotenv_values
from redis import Redis
import vk_api as vk
import json


def start(event, vk_api, keyboard, db):
    user_id=event.user_id
    user_statistics =  {'question': None, 'answer': None, 'counter': 0}
    db.set(user_id, json.dumps(user_statistics))
    vk_api.messages.send(
        user_id=user_id,
        message='Привет! Я бот для викторины.',
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard()
    )


def handle_new_question_request(event, vk_api, keyboard, questions, db):
    user_id = event.user_id
    user_statistics = json.loads(db.get(user_id))
    try:
        question, answer = questions.popitem()
    except KeyError:
        question = 'Конец викторины. Вы ответили на все вопросы.'
    else:
        user_statistics['question'], user_statistics['answer'] = question, answer
        db.set(user_id, json.dumps(user_statistics))

    vk_api.messages.send(
        user_id=user_id,
        message=question,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
    )



def handle_solution_attempt(event, vk_api, keyboard, questions, db):
    user_id = event.user_id
    user_answer = event.text
    user_statistics = json.loads(db.get(user_id))
    question = user_statistics['question']
    correct_answer = user_statistics['answer']

    if check_answer(question, user_answer, correct_answer):
        message = 'Правильно! Поздравляю! Для следующего вопроса нажми "Новый вопрос"'
        user_statistics['counter'] += 1
        db.set(user_id, json.dumps(user_statistics))
    else:
        message='Неправильно… Попробуешь ещё раз?'

    vk_api.messages.send(
        user_id=user_id,
        message=message,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
    )


def handle_surrender_request(event, vk_api, keyboard, questions, db):
    user_id = event.user_id
    user_statistics = json.loads(db.get(user_id))
    answer = user_statistics['answer']
    vk_api.messages.send(
        user_id=user_id,
        message=answer,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
    )


def handle_counter_request(event, vk_api, keyboard, db):
    user_id = event.user_id
    user_statistics = json.loads(db.get(user_id))
    counter = user_statistics['counter']
    vk_api.messages.send(
        user_id=user_id,
        message=counter,
        random_id=get_random_id(),
        keyboard=keyboard.get_keyboard(),
    )


def main(questions_dir):
    config = dotenv_values('.env')

    vk_session = vk.VkApi(token=config['VK_TOKEN'])
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    keyboard = VkKeyboard(one_time=True)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button('Мой счет', color=VkKeyboardColor.SECONDARY)

    redis_db = Redis(
        host=config['REDIS_URL'],
        port=config['REDIS_PORT'],
        password=config['REDIS_PASSW'],
    )

    questions = get_questions(questions_dir)

    try:
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text == 'start':
                    start(event, vk_api, keyboard, redis_db)
                elif event.text == 'Новый вопрос':
                    handle_new_question_request(
                        event, vk_api, keyboard, questions, redis_db)
                elif event.text == 'Сдаться':
                    handle_surrender_request(
                        event, vk_api, keyboard, questions, redis_db)
                elif event.text == 'Мой счет':
                    handle_counter_request(event, vk_api, keyboard, redis_db)
                else:
                    handle_solution_attempt(
                        event, vk_api, keyboard, questions, redis_db)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Чатбот для соц.сети Вконтакте для проведения викторин.'
    )
    parser.add_argument(
        '-p', '--path',
        default='quiz-questions',
        help='Путь к директории с вопросами для викторины.'
    )
    args = parser.parse_args()
    main(args.path)

