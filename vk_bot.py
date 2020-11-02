import os
from vk_api import VkApi
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from questions import (
    generate_new_question, check_answer, get_right_answer,
    load_questions, check_account,
)
from telegram_logger import TelegramLogsHandler
import logging

logger = logging.getLogger("dvmn_bot_telegram")


def get_reply_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)

    keyboard.add_line()
    keyboard.add_button('Счет', color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()


def send_text(event, vk_api, text):
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        message=text,
        keyboard=get_reply_keyboard(),
    )


def send_new_question_request(event, vk_api):
    question = generate_new_question(user_id=f'vk_{event.user_id}')
    send_text(
        event, vk_api,
        text=question,
    )


def send_refuse_question(event, vk_api):
    right_answer = get_right_answer(user_id=f'vk_{event.user_id}')
    send_text(
        event, vk_api,
        text=f'Правильный ответ:\n{right_answer}',
    )


def send_my_account(event, vk_api):
    success_attempts, unsuccess_attempts = check_account(
        user_id=f'vk_{event.user_id}'
    )
    send_text(
        event, vk_api,
        text=f'''
        Успешных попыток угадывания: {success_attempts}\nНедачных попыток угадывания: {unsuccess_attempts}
        ''',
    )


def send_solution_attempt(event, vk_api):
    is_right_answer = check_answer(
        user_id=f'vk_{event.user_id}',
        answer=event.text,
    )
    if is_right_answer:
        send_text(
            event, vk_api,
            'Правильно! Поздравляю! Для следующего вопроса нажмите «Новый вопрос»',
        )
        return None
    send_text(
        event, vk_api,
        'Неправильно... Попробуете ещё раз?',
    )


def main():
    vk_token = os.environ['VK_TOKEN']
    debug_bot_token = os.environ['DEBUG_BOT_TOKEN']
    debug_chat_id = os.environ['DEBUG_TELEGRAM_BOT_TOKEN']

    logger.setLevel(logging.INFO)
    logger.addHandler(TelegramLogsHandler(
        debug_bot_token=debug_bot_token,
        chat_id=debug_chat_id,
    ))

    load_questions()
    vk_session = VkApi(token=vk_token)
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)

    logger.info('Бот Викторина в VK запущен')

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == 'Новый вопрос':
                send_new_question_request(event, vk_api)
            elif event.text == 'Сдаться':
                send_refuse_question(event, vk_api)
            elif event.text == 'Счет':
                send_my_account(event, vk_api)
            else:
                send_solution_attempt(event, vk_api)


if __name__ == "__main__":
    main()
