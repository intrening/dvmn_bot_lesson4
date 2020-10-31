import os
import random
import redis

QUESTIONS_DICT = {}
REDIS_DB = None


def generate_new_question(user_id):
    question, _ = random.choice(list(QUESTIONS_DICT.items()))
    REDIS_DB.set(user_id, question)
    return question


def check_answer(user_id, answer):
    answer = answer.lower().strip()
    question = REDIS_DB.get(user_id).decode()
    right_answer = QUESTIONS_DICT[question]
    short_right_answer = right_answer.split('.')[0].split('(')[0].lower().strip()
    return answer == short_right_answer


def get_right_answer(user_id):
    question = REDIS_DB.get(user_id).decode()
    return QUESTIONS_DICT[question]


def parse_questions():
    question_dict = {}
    question_dir = os.getenv('QUESTIONS_DIR')
    for file in os.listdir(question_dir):
        if file.endswith(".txt"):
            with open(os.path.join(question_dir, file), 'r', encoding='KOI8-R') as f:
                file_lines = f.read().split('\n\n')
            question = answer = ''
            for line in file_lines:
                if 'Вопрос ' in line:
                    question = ''.join(line.replace('\n', ' ').split(': ')[1:])
                if 'Ответ:' in line:
                    answer = ''.join(line.replace('\n', ' ').split(': ')[1:])
                if question and answer:
                    question_dict[question] = answer
                    question = answer = ''
    return question_dict


def load_questions():
    global QUESTIONS_DICT
    global REDIS_DB
    QUESTIONS_DICT = parse_questions()
    REDIS_DB = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=os.getenv('REDIS_PORT'),
        password=os.getenv('REDIS_PASSWORD'),
    )
