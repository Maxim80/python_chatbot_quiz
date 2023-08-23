import os
import pprint


def get_file_content(file): 
    with open(file, mode='r', encoding='KOI8-R') as file:
        file_content = file.read()
    
    return file_content


def get_questions(questions_dir):
    questions = {}

    for file in os.listdir(questions_dir):
        file_content = get_file_content(os.path.join(questions_dir, file))
        ques = [text.split(':')[1].strip() for text in file_content.split('\n\n') if 'Вопрос' in text]
        answ = [text.split(':')[1].strip() for text in file_content.split('\n\n') if 'Ответ:' in text]
        
        if len(ques) == len(answ):
            questions.update(list(zip(ques, answ)))

    return questions


def get_normalize_answer(answer):
    answer = answer.strip(' .').lower()
    index = 0
    for symbol in answer:
        if symbol == '(' and symbol == '.':
            break
        index +=1
    return answer[:index]


def check_answer(question, user_answer, correct_answer):
    user_answer = get_normalize_answer(user_answer)
    correct_answer = get_normalize_answer(correct_answer)
    return user_answer in correct_answer
