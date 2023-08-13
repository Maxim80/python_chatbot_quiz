import os


QUESTIONS_DIR = 'quiz-questions'


def get_files(path_to_files):
    return os.listdir(path_to_files)


def get_file_content(file):
    with open(f'quiz-questions/{file}', mode='r', encoding='KOI8-R') as file:
        file_content = file.read()
    
    return file_content


def get_questions_or_answers(file_content, keyword):
    return [text.split(':')[1].strip() for text in file_content.split('\n\n') if keyword in text]


if __name__ == '__main__':
    questions_and_answers = {}

    for file in get_files(QUESTIONS_DIR):
        file_content = get_file_content(file)
        questions = get_questions_or_answers(file_content, 'Вопрос')
        answers = get_questions_or_answers(file_content, 'Ответ:')

        if len(questions) == len(answers):
            questions_and_answers.update(list(zip(questions, answers)))
