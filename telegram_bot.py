import os
from telegram import ReplyKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
    ConversationHandler,
)
from questions import (
    generate_new_question, check_answer, get_right_answer,
    load_questions,
)

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


def start(bot, update):
    update.message.reply_text(
        'Добро пожаловать в викторину!',
        reply_markup=markup,
    )
    return CHOOSING


def handle_new_question_request(bot, update, user_data):
    question = generate_new_question(user_id=update.effective_chat.id)
    update.message.reply_text(question, reply_markup=markup)
    return TRYING_ANSWER


def handle_refuse_question(bot, update, user_data):
    right_answer = get_right_answer(user_id=update.effective_chat.id)
    update.message.reply_text(
        f'Правильный ответ:\n{right_answer}',
        reply_markup=markup,
    )
    return CHOOSING


def handle_solution_attempt(bot, update, user_data):
    is_right_answer = check_answer(
        user_id=update.effective_chat.id,
        answer=update.message.text,
    )
    if is_right_answer:
        update.message.reply_text(
            'Правильно! Поздравляю! Для следующего вопроса нажмите «Новый вопрос»',
            reply_markup=markup,
        )
        return CHOOSING
    update.message.reply_text(
        'Неправильно... Попробуете ещё раз?',
        reply_markup=markup,
    )
    return TRYING_ANSWER


def done(bot, update, user_data):
    return ConversationHandler.END


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    load_questions()
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
