import os
from vk_api import VkApi
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id


def get_reply_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('Новый вопрос', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('Сдаться', color=VkKeyboardColor.NEGATIVE)

    keyboard.add_line()
    keyboard.add_button('Счет', color=VkKeyboardColor.PRIMARY)
    return keyboard.get_keyboard()


def echo(event, vk_api):
    vk_api.messages.send(
        user_id=event.user_id,
        random_id=get_random_id(),
        message=event.text,
        keyboard=get_reply_keyboard(),
    )


def main():
    vk_session = VkApi(token=os.getenv('VK_TOKEN'))
    vk_api = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            if event.text == 'Новый вопрос':
                echo(event, vk_api)


if __name__ == "__main__":
    main()
