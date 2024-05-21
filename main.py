import telebot
from telebot import types
import user as api
import threading

database_lock = threading.Lock()

bot = telebot.TeleBot('BOT_TOKEN')

STATE_NONE, STATE_LOGIN, STATE_PASSWORD, STATE_REGISTERED = range(4)
CHOOSING_PERSON, NOT_CHOOSING_PERSON = 1, 0


@bot.message_handler(commands=['start'])
def start(message):
    try:
        user_id = str(message.from_user.id)
        if api.get_user_state(user_id) == STATE_REGISTERED:
            main_menu_call(message)
        else:
            bot.send_message(user_id, "Введите ваш логин:")
            api.update_user_state(user_id, STATE_LOGIN)
    except TypeError:
        print('TypeError')


@bot.message_handler(func=lambda message: api.get_user_state(message.from_user.id) == STATE_LOGIN)
def handle_login(message):
    try:
        user_id = str(message.from_user.id)
        cookie = api.gen_unique_cookie()
        api.logout(cookie)
        token = api.get_token(cookie)
        api.update_user_state(user_id, STATE_PASSWORD, {'login': message.text, 'cookie': cookie, 'token': token})
        bot.send_message(user_id, "Теперь введите ваш пароль:")
    except TypeError:
        print('TypeError')


@bot.message_handler(func=lambda message: api.get_user_state(message.from_user.id) == STATE_PASSWORD)
def handle_password(message):
    try:
        users = api.get_users()
        user_id = str(message.from_user.id)
        user_data = users[user_id]
        login = user_data['login']
        password = message.text
        cookie = user_data['cookie']
        token = user_data['token']
        response_code = api.login(login, password, cookie, token)
        if response_code == 200:
            user_info = api.parse_inf(cookie)
            if user_info == 401:
                bot.send_message(user_id, "Неверный логин или пароль. Попробуйте еще раз.\nВведите ваш логин:")
                api.update_user_state(user_id, STATE_LOGIN)
            else:
                api.create_user(user_id, *user_info)
                api.update_user_state(user_id, STATE_REGISTERED, {'password': password})
                all_groups = api.get_all_groups(user_id)

                print(all_groups)

                if all_groups != 1 and all_groups != 401:
                    api.update_user_info(user_id, {'all_groups': all_groups})
                    api.fill_teachers(user_id)
                else:
                    print('ОШИБКА С ПОЛУЧЕНИЕМ ГРУПП ---', all_groups)

                # Пробуем добавить логин в messages.json
                messages = api.get_messages()
                if not messages.get(login, False):
                    messages[login] = {}
                api.set_messages(messages)
                main_menu_call(message)
        else:
            bot.send_message(user_id, "Неверный логин или пароль. Попробуйте еще раз.\nВведите ваш логин:")
            api.update_user_state(user_id, STATE_LOGIN)
    except TypeError:
        print('TypeError')



def lang_get(ui):
    try:
        return api.get_user(ui)['language'] == 'en'
    except TypeError:
        print('TypeError')


def main_menu(message):
    try:
        markup = types.InlineKeyboardMarkup(row_width=8)
        user_id = str(message.from_user.id)

        compose_ = types.InlineKeyboardButton(text=('Отправка', 'Composing')[lang_get(user_id)],
                                              callback_data='compose')
        inbox_ = types.InlineKeyboardButton(text=('Входящие', 'Inbox')[lang_get(user_id)],
                                            callback_data='inbox')
        settings_ = types.InlineKeyboardButton(text=('Настройки', 'Settings')[lang_get(user_id)],
                                               callback_data='settings')
        markup.add(compose_)
        markup.add(inbox_)
        markup.add(settings_)
        return markup
    except TypeError:
        print('TypeError')


def main_menu_call(message):
    try:
        user_id = str(message.from_user.id)
        markup = main_menu(message)
        bot.send_photo(chat_id=message.chat.id, photo=open('main_menu.png', 'rb'),
                       caption=("👋 *Привет, *" '*' + api.get_users()[user_id]['name'] + '!*' '*\n\nГлавное меню:*',
                                "👋 *Hello, *" '*' + api.get_users()[user_id]['name'] + '!*' '*\n\nMain menu*')[
                           lang_get(user_id)],
                       reply_markup=markup, parse_mode='Markdown')
    except TypeError:
        print('TypeError')


def settings(call):
    try:
        markup = types.InlineKeyboardMarkup(row_width=8)
        user_id = str(call.from_user.id)
        support_ = types.InlineKeyboardButton(
            text=('Задать вопрос в поддержку', 'Ask a question to the support')[lang_get(user_id)],
            callback_data='support', url='https://t.me/iskochergin')
        feedback_ = types.InlineKeyboardButton(
            text=('Оставить фидбек', 'Leave feedback')[lang_get(user_id)],
            callback_data='feedback', url='https://t.me/iskochergin')
        language_ = types.InlineKeyboardButton(
            text=('Поменять язык', 'Change the language')[lang_get(user_id)],
            callback_data='language')
        privacy_ = types.InlineKeyboardButton(
            text=('Посмотреть настройки приватности', 'View privacy settings')[lang_get(user_id)],
            callback_data='privacy', url='https://example.com')
        logout_ = types.InlineKeyboardButton(
            text=('Выйти из аккаунта', 'Log out of your account')[lang_get(user_id)],
            callback_data='logout')
        back = types.InlineKeyboardButton(text=('Назад в меню', 'Back to menu')[lang_get(user_id)],
                                          callback_data='back_to_main')

        markup.add(support_)
        markup.add(feedback_)
        markup.add(privacy_)
        markup.add(language_)
        markup.add(logout_)
        markup.add(back)

        new_photo = open('Settings.png', 'rb')
        new_media = types.InputMediaPhoto(new_photo)
        bot.edit_message_media(media=new_media, chat_id=call.message.chat.id, message_id=call.message.message_id)
        new_photo.close()
        bot.edit_message_caption(('*Меню настроек*', "*Settings menu:*")[lang_get(user_id)],
                                 call.message.chat.id,
                                 call.message.message_id, parse_mode='Markdown')
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=markup)
    except TypeError:
        print('TypeError')


def change_language(call, lan):
    try:
        user_id = str(call.from_user.id)
        users = api.get_users()
        users[user_id]['language'] = lan
        api.set_users(users)
    except TypeError:
        print('TypeError')


def language(call):
    try:
        user_id = str(call.from_user.id)
        bot.edit_message_caption(
            ("*Выберите ваш язык:*", "*Choose the language you prefer:*")[lang_get(user_id)],
            call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        markup = types.InlineKeyboardMarkup(row_width=8)
        russian = types.InlineKeyboardButton(
            text=('Установить русский', 'Set Russian')[lang_get(user_id)],
            callback_data='ru_lan')
        english = types.InlineKeyboardButton(
            text=('Установить английский', 'Set English')[lang_get(user_id)],
            callback_data='en_lan')
        back = types.InlineKeyboardButton(text=('Назад в настройки', 'Back to settings ')[lang_get(user_id)],
                                          callback_data='back_to_settings')
        markup.add(english)
        markup.add(russian)
        markup.add(back)
        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=markup)
    except TypeError:
        print('TypeError')


def logout(call):
    try:
        user_id = str(call.from_user.id)
        users = api.get_users()
        del users[user_id]
        api.set_users(users)
        bot.send_message(int(user_id),
                         "Вы успешно вышли из аккаунта. Нажмите /start, для того, чтобы зарегистрироваться.")
    except TypeError:
        print('TypeError')


def compose(call):
    try:
        with database_lock:
            user_id = str(call.from_user.id)
            bot.edit_message_caption(
                ("*Выберите каким образом вы хотите отправить сообщение:*",
                 "*Choose how you want to compose the message:*")[lang_get(user_id)], call.message.chat.id,
                call.message.message_id, parse_mode='Markdown')
            markup = types.InlineKeyboardMarkup(row_width=8)

            by_name = types.InlineKeyboardButton(text=('Искать по имени', 'Search by name')[lang_get(user_id)],
                                                 callback_data='search_by_name')
            by_group = types.InlineKeyboardButton(text=('Искать по группе', 'Search by group')[lang_get(user_id)],
                                                  callback_data='search_by_group')

            back = types.InlineKeyboardButton(text=('Назад в меню', 'Back to menu')[lang_get(user_id)],
                                              callback_data='back_to_main')

            markup.add(by_name)
            markup.add(by_group)
            markup.add(back)

            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          reply_markup=markup)
    except TypeError:
        print('TypeError')


def update_markup_groups(user_id, page, max_page):
    try:
        markup = types.InlineKeyboardMarkup(row_width=8)
        start_index = page * 8
        end_index = start_index + 8
        users = api.get_users()
        all_groups = [group for group in users[user_id]['all_groups']]

        # Добавляем кнопки групп
        for group in all_groups[start_index:end_index]:
            markup.add(types.InlineKeyboardButton(text=group + ' (' + users[user_id]['all_groups'][group][1] + ')',
                                                  callback_data='group_' + group))

        # Добавляем кнопки навигации
        nav_buttons = [
            types.InlineKeyboardButton(text="<<", callback_data='nav_0'),  # Перейти на первую страницу
            types.InlineKeyboardButton(text="<", callback_data=f'nav_{page - 1}'),
            types.InlineKeyboardButton(text=">", callback_data=f'nav_{page + 1}'),
            types.InlineKeyboardButton(text=">>", callback_data=f'nav_{max_page}')  # Перейти на последнюю страницу
        ]
        if page == 0:
            nav_buttons[0].callback_data = nav_buttons[1].callback_data = 'under_zero_page'
        if page >= max_page:
            nav_buttons[2].callback_data = nav_buttons[3].callback_data = 'under_zero_page'

        markup.row(*nav_buttons)

        back = types.InlineKeyboardButton(text=('Назад в отправку', 'Back to composing')[lang_get(user_id)],
                                          callback_data='back_to_compose')
        markup.add(back)

        return markup
    except TypeError:
        print('TypeError')


def search_by_group(call):
    try:
        with database_lock:
            user_id = str(call.from_user.id)
            bot.edit_message_caption(
                ("*Найдите человека по группе*", "*Find the person by group*")[lang_get(user_id)], call.message.chat.id,
                call.message.message_id, parse_mode='Markdown')

            users = api.get_users()
            all_groups = users[user_id]['all_groups']
            max_page = len(all_groups) // 8

            markup = update_markup_groups(user_id, 0, max_page)
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          reply_markup=markup)
    except TypeError:
        print('TypeError')


def change_page_group(call):
    try:
        if call.data.startswith('nav_'):
            page = int(call.data.split('_')[1])
            if page < 0 or call.data == 'under_zero_page':
                return  # Игнорируем невалидную страницу или заблокированные кнопки
            user_id = str(call.from_user.id)
            users = api.get_users()
            all_groups = users[user_id]['all_groups']
            max_page = len(all_groups) // 8

            markup = update_markup_groups(user_id, page, max_page)
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          reply_markup=markup)
    except TypeError:
        print('TypeError')


def inbox(call):
    try:
        user_id = str(call.from_user.id)
        bot.edit_message_caption(
            ("*Входящие сообщения*\nВыберите раздел:", "*Incoming messages*\nSelect the section:")[lang_get(user_id)],
            call.message.chat.id, call.message.message_id, parse_mode='Markdown')
        markup = types.InlineKeyboardMarkup(row_width=8)

        academ = types.InlineKeyboardButton(text=('Академ', 'Academic')[lang_get(user_id)],
                                            callback_data='academ')
        vneacadem = types.InlineKeyboardButton(text=('Внекадем', 'Out of academic')[lang_get(user_id)],
                                               callback_data='vneacadem')
        diploma = types.InlineKeyboardButton(
            text=('Сортировка по диплому Летово', 'Sorting by Letovo diploma')[lang_get(user_id)],
            callback_data='vneacadem')
        back = types.InlineKeyboardButton(text=('Назад в меню', 'Back to menu')[lang_get(user_id)],
                                          callback_data='back_to_main')

        markup.add(academ)
        markup.add(vneacadem)
        markup.add(diploma)
        markup.add(back)

        bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      reply_markup=markup)
    except TypeError:
        print('TypeError')


@bot.callback_query_handler(func=lambda call: call.data.startswith('nav_') or call.data == 'under_zero_page')
def callback_query(call):
    change_page_group(call)


def update_people_markup(people_in_group, page, max_page, user_id):
    markup = types.InlineKeyboardMarkup(row_width=1)  # Устанавливаем row_width по количеству кнопок в строке
    start_index = page * 8
    end_index = start_index + 8

    # Добавляем кнопки людей
    for person, login in people_in_group[start_index:end_index]:
        markup.add(types.InlineKeyboardButton(text=person, callback_data='person_' + login))

    # Добавляем кнопки навигации
    nav_buttons = [
        types.InlineKeyboardButton(text="<<", callback_data='nav_people_0'),  # Перейти на первую страницу
        types.InlineKeyboardButton(text="<", callback_data=f'nav_people_{page - 1}'),
        types.InlineKeyboardButton(text=">", callback_data=f'nav_people_{page + 1}'),
        types.InlineKeyboardButton(text=">>", callback_data=f'nav_people_{max_page}')  # Перейти на последнюю страницу
    ]
    if page == 0:
        nav_buttons[0].callback_data = nav_buttons[1].callback_data = 'inactive'
    if page >= max_page:
        nav_buttons[2].callback_data = nav_buttons[3].callback_data = 'inactive'

    markup.row(*nav_buttons)
    # Добавляем кнопку "Назад"
    back_button = types.InlineKeyboardButton(
        text=('Назад в поиск по группе', 'Back to search by group')[lang_get(user_id)],
        callback_data='back_to_search_by_group')
    markup.add(back_button)

    return markup


def find_people_in_group(call, group):
    user_id = str(call.from_user.id)
    users = api.get_users()

    bot.edit_message_caption(
        ("*Найдите человека в группе* " + group + ' (' + users[user_id]['all_groups'][group][1] + ')',
         "*Find a person in the group* " + group + ' (' + users[user_id]['all_groups'][group][1] + ')')[
            lang_get(user_id)],
        call.message.chat.id, call.message.message_id, parse_mode='Markdown')

    people_in_group = []
    if users[user_id]['all_groups'][group][0] != '':
        people_in_group.append((users[user_id]['all_groups'][group][0], ''))
        # Надо добавить логины учителей
    for user in users:
        if not users[user].get('schedule', False) or user == user_id:
            continue
        for day in users[user]['schedule']:
            need_to_break = False
            for lesson in users[user]['schedule'][day]:
                if lesson['group'] == group:
                    people_in_group.append((users[user]['name'], users[user]['login']))
                    need_to_break = True
                    break
            if need_to_break:
                break

    # Рассчитываем количество страниц
    max_page = len(people_in_group) // 8
    if len(people_in_group) % 8 != 0:
        max_page += 1

    # Создаем и отправляем начальную разметку
    markup = update_people_markup(people_in_group, 0, max_page - 1, user_id)
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                  reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith('group_'))
def callback_query(call):
    find_people_in_group(call, call.data.lstrip('group_'))


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    try:
        user_id = str(call.from_user.id)

        if call.data == 'compose' or call.data == 'back_to_compose':
            compose(call)
        elif call.data == 'inbox' or call.data == 'back_to_inbox':
            inbox(call)
        elif call.data == 'settings' or call.data == 'back_to_settings':
            settings(call)
        elif call.data == 'back_to_main':
            markup = main_menu(call)
            new_photo = open('main_menu.png', 'rb')
            new_media = types.InputMediaPhoto(new_photo)
            bot.edit_message_media(media=new_media, chat_id=call.message.chat.id, message_id=call.message.message_id)
            new_photo.close()
            bot.edit_message_caption(
                ("👋 *Привет, *" '*' + api.get_users()[user_id]['name'] + '!*' '*\n\nГлавное меню:*',
                 "👋 *Hello, *" '*' + api.get_users()[user_id]['name'] + '!*' '*\n\nMain menu*')[
                    lang_get(user_id)],
                call.message.chat.id, call.message.message_id, parse_mode='Markdown')
            bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                          reply_markup=markup)
        elif call.data == 'language':
            language(call)
        elif call.data == 'ru_lan':
            change_language(call, 'ru')
            language(call)
        elif call.data == 'en_lan':
            change_language(call, 'en')
            language(call)
        elif call.data == 'logout':
            logout(call)
        elif call.data == 'search_by_group' or call.data == 'back_to_search_by_group':
            search_by_group(call)
    except TypeError:
        print('TypeError')


bot.polling()
