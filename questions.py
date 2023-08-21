import os
import pprint


QUESTIONS_DIR = 'quiz-questions'


def get_file_content(file): 
    with open(f'quiz-questions/{file}', mode='r', encoding='KOI8-R') as file:
        file_content = file.read()
    
    return file_content


def get_questions():
    questions = {}

    for file in os.listdir(QUESTIONS_DIR):
        file_content = get_file_content(file)
        ques = [text.split(':')[1].strip() for text in file_content.split('\n\n') if 'Вопрос' in text]
        answ = [text.split(':')[1].strip() for text in file_content.split('\n\n') if 'Ответ:' in text]
        
        if len(ques) == len(answ):
            questions.update(list(zip(ques, answ)))

    return questions


def _answer_normalize(answer):
    answer = answer.strip(' .').lower()
    index = 0
    for symbol in answer:
        if symbol == '(' and symbol == '.':
            break
        index +=1
    return answer[:index]


def check_answer(question, user_answer, correct_answer):
    user_answer = _answer_normalize(user_answer)
    correct_answer = _answer_normalize(correct_answer)
    return user_answer in correct_answer
