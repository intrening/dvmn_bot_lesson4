import os
import random
import json
import redis

QUESTIONS_COUNT = 0
REDIS_DB = None


def get_redis_user_info(user_id):
    json_user_info = REDIS_DB.get(f'user_{user_id}')
    if json_user_info:
        user_info = json.loads(json_user_info)
    else:
        user_info = {
            'last_asked_question': '',
            'success_attempts': 0,
            'unsuccess_attempts': 0,
        }
    return user_info


def update_redis_user_info(user_id, user_info):
    REDIS_DB.set(f'user_{user_id}', json.dumps(user_info))


def get_attempts_count(user_id):
    user_info = get_redis_user_info(user_id)
    return user_info['success_attempts'], user_info['unsuccess_attempts']


def generate_new_question(user_id):
    question_num = f'question_{random.randint(0, QUESTIONS_COUNT)}'
    user_info = get_redis_user_info(user_id)
    user_info['last_asked_question'] = question_num
    update_redis_user_info(user_id, user_info)
    question_item = json.loads(REDIS_DB.get(question_num))
    return question_item['question']


def check_answer(user_id, answer):
    answer = answer.lower().strip()
    user_info = get_redis_user_info(user_id)
    question_num = user_info['last_asked_question']
    question_item = json.loads(REDIS_DB.get(question_num))
    right_answer = question_item['answer']
    short_right_answer = right_answer.split('.')[0].split('(')[0].lower().strip()
    if answer == short_right_answer:
        user_info['success_attempts'] += 1
    else:
        user_info['unsuccess_attempts'] += 1
    update_redis_user_info(user_id, user_info)
    return answer == short_right_answer


def get_right_answer(user_id):
    user_info = get_redis_user_info(user_id)
    question_num = user_info['last_asked_question']
    question_item = json.loads(REDIS_DB.get(question_num))
    return question_item['answer']


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
    global REDIS_DB
    global QUESTIONS_COUNT

    REDIS_DB = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=os.getenv('REDIS_PORT'),
        password=os.getenv('REDIS_PASSWORD'),
    )

    questions = parse_questions()
    QUESTIONS_COUNT = len(questions)
    for num, (question, answer) in enumerate(questions.items()):
        question_item = (
            {
                'question': question,
                'answer': answer,
            }
        )
        REDIS_DB.set(f'question_{num}', json.dumps(question_item))
