import os
import random
from telegram import ReplyKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
    ConversationHandler,
)
import redis

import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

CHOOSING, TRYING_ANSWER = range(2)

reply_keyboard = [
    ['Новый вопрос', 'Сдаться'],
    ['Мой счет'],
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def generate_random_question():
    global QUESTIONS_DICT
    question, answer = random.choice(list(QUESTIONS_DICT.items()))
    return question, answer


def start(bot, update):
    update.message.reply_text(
        'Добро пожаловать в викторину!',
        reply_markup=markup,
    )
    return CHOOSING


def handle_new_question_request(bot, update, user_data):
    question, _ = generate_random_question()
    update.message.reply_text(question, reply_markup=markup)
    REDIS_DB.set(update.effective_chat.id, question)
    return TRYING_ANSWER


def handle_refuse_question(bot, update, user_data):
    question = REDIS_DB.get(update.effective_chat.id).decode()
    right_answer = QUESTIONS_DICT[question]
    update.message.reply_text(
        f'Правильный ответ:\n{right_answer}',
        reply_markup=markup,
    )
    return CHOOSING


def handle_solution_attempt(bot, update, user_data):
    answer = update.message.text.lower().strip()
    question = REDIS_DB.get(update.effective_chat.id).decode()
    right_answer = QUESTIONS_DICT[question]
    short_right_answer = right_answer.split('.')[0].split('(')[0].lower().strip()
    if answer == short_right_answer:
        update.message.reply_text(
            'Правильно! Поздравляю! Для следующего вопроса нажми «Новый вопрос»',
            reply_markup=markup,
        )
        return CHOOSING
    update.message.reply_text(
        'Неправильно... Попробуете ещё раз?',
        reply_markup=markup,
    )
    update.message.reply_text(right_answer)
    return TRYING_ANSWER


def done(bot, update, user_data):
    return ConversationHandler.END


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def parse_questions():
    with open('1vs1200.txt', 'r', encoding='KOI8-R') as f:
        file_lines = f.read().split('\n\n')
    question_dict = {}
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


def main():
    global QUESTIONS_DICT
    global REDIS_DB

    QUESTIONS_DICT = parse_questions()
    REDIS_DB = redis.Redis(
        host=os.getenv('REDIS_HOST'),
        port=os.getenv('REDIS_PORT'),
        password=os.getenv('REDIS_PASSWORD'),
    )

    updater = Updater(os.environ['TELEGRAM_TOKEN'])
    dp = updater.dispatcher
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            CHOOSING: [
                RegexHandler(
                    '^Новый вопрос$',
                    handle_new_question_request,
                    pass_user_data=True
                ),
            ],
            TRYING_ANSWER: [
                RegexHandler(
                    '^Новый вопрос$',
                    handle_new_question_request,
                    pass_user_data=True
                ),
                RegexHandler(
                    '^Сдаться$',
                    handle_refuse_question,
                    pass_user_data=True
                ),
                MessageHandler(
                    Filters.text,
                    handle_solution_attempt,
                    pass_user_data=True,
                ),
            ],
        },

        fallbacks=[RegexHandler('^Сдаться$', done, pass_user_data=True)]
    )

    dp.add_handler(conv_handler)
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
