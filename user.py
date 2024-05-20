import json
import threading
from datetime import date
import requests
from bs4 import BeautifulSoup
import secrets

STATE_NONE, STATE_LOGIN, STATE_PASSWORD, STATE_REGISTERED = range(4)


def get_token(cookie):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Referer': 'https://student.letovo.ru/student/academic/progress',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not-A.Brand";v="99", "Chromium";v="124"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"'
    }

    # Define the cookies
    cookies = {
        'PHPSESSID': cookie
    }

    # Send the GET request
    response = requests.get('https://student.letovo.ru/home', headers=headers, cookies=cookies)

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find the _token value
    token_input = soup.find('input', {'name': '_token'})
    if token_input:
        token_value = token_input.get('value')
        print(f"_token value: {token_value}")
        return token_value
    else:
        print("_token value not found")


def logout(cookie):
    url = 'https://student.letovo.ru/logout'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Referer': 'https://student.letovo.ru/home',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not-A.Brand";v="99", "Chromium";v="124"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"'
    }

    cookies = {
        'PHPSESSID': cookie
    }

    response = requests.get(url, headers=headers, cookies=cookies)

    print(f"Status code: {response.status_code}")
    # print(response.text)


# Создаем объект блокировки
database_lock = threading.Lock()


def get_users():
    with database_lock:
        with open("database.json", 'r+', encoding="UTF-8") as file:
            return json.loads(file.read())


def set_users(users):
    with database_lock:
        with open("database.json", 'w+', encoding="UTF-8") as file:
            json.dump(users, file, ensure_ascii=False, indent=4)


def get_messages():
    with database_lock:
        with open("messages.json", 'r+', encoding="UTF-8") as file:
            return json.loads(file.read())


def set_messages(messages):
    with database_lock:
        with open("messages.json", 'w+', encoding="UTF-8") as file:
            json.dump(messages, file, ensure_ascii=False, indent=4)


def get_user(id: str):
    users = get_users()  # Получаем словарь пользователей
    return users.get(str(id), False)  # Возвращаем пользователя по ID или None, если такого пользователя нет


def create_user(id, name, grade, login, nastavnik, pansion, commanda, house, dorm, schedule):
    users = get_users()
    users[str(id)] = users.get(str(id), {}) | {
        "creation_date": date.today().strftime("%d-%m-%Y"),
        "language": "ru",
        "name": name,
        "grade": grade,
        "login": login,
        "nastavnik": nastavnik,
        "pansion": pansion,
        "commanda": commanda,
        "house": house,
        "dorm": dorm,
        "schedule": schedule
    }
    # print(users[str(id)])
    set_users(users)


def login(login_username, login_password, cookie, token):
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Cookie': f'PHPSESSID={cookie}',
        'DNT': '1',
        'Origin': 'https://student.letovo.ru',
        'Referer': 'https://student.letovo.ru/student/1137071/studyplan',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'X-CSRF-TOKEN': f'{token}',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Not-A.Brand";v="99", "Chromium";v="124"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"'
    }
    data = {
        '_token': f'{token}',
        'login': login_username,
        'password': login_password
    }
    response = requests.post('https://student.letovo.ru/login', headers=headers, data=data)
    return response.status_code


def change_password(current_password, new_password, confirm_new_password, cookie, token):
    url = 'https://student.letovo.ru/profile/setpassword'
    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Cookie': f'PHPSESSID={cookie}',
        'DNT': '1',
        'Origin': 'https://student.letovo.ru',
        'Referer': 'https://student.letovo.ru/profile/password',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'X-CSRF-TOKEN': f'{token}',
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': '"Not-A.Brand";v="99", "Chromium";v="124"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"'
    }

    data = {
        'password_current': current_password,
        'password_new_1': new_password,
        'password_new_2': confirm_new_password
    }

    response = requests.post(url, headers=headers, data=data)
    response_json = response.json()

    if 'message' in response_json:
        return response_json['message']
    else:
        return 'Неизвестная ошибка'


def parse_inf(cookie):
    try:
        response = requests.get("https://student.letovo.ru/student/123123/schedule", headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9", "Cookie": f"PHPSESSID={cookie}"})
        main_student_info = BeautifulSoup(requests.get("https://student.letovo.ru/student/123123/", headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9", "Cookie": f"PHPSESSID={cookie}"}).text, "html.parser").find_all(
            'div',
            class_='col-sm-12 col-md-8')
        name = main_student_info[0].get_text(strip=True)
        grade = main_student_info[1].get_text(strip=True)
        login = main_student_info[2].get_text(strip=True)
        nastavnik = main_student_info[7].get_text(strip=True).split("\n")[0]
        house, dorm = main_student_info[8].get_text(strip=True).replace("НедельныйДом:House ", '').replace(
            "ПолныйДом:House ",
            '').replace(
            "ДневнойДом:House", '').split("Комната:Dorm ")
        commanda = BeautifulSoup(requests.get("https://student.letovo.ru/student/123123/", headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9", "Cookie": f"PHPSESSID={cookie}"}).text, "html.parser").find(
            'h5').get_text(
            strip=True).replace("Профиль ученика", '')
        pansion = BeautifulSoup(requests.get("https://student.letovo.ru/student/123123/", headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9", "Cookie": f"PHPSESSID={cookie}"}).text, "html.parser").find('span',
                                                                                                             class_='badge badge-info').get_text(
            strip=True)
        print(name)
        print(grade)
        print(login)
        print(nastavnik)
        print(pansion)
        print(commanda)
        print(house, dorm)

        soup = BeautifulSoup(response.text, "html.parser")
        timetable = {}
        text_timetable = ""
        all_rows = soup.findAll('tr')[1:]
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        for lesson_row in all_rows:
            for lesson in range(0, len(lesson_row.find_all('td'))):
                i = lesson
                lesson = lesson_row.find_all('td')[lesson]
                time_range = lesson.find('div', class_='lesson-time-range').get_text(strip=True)
                subject_name = lesson.find('div', class_='lesson-subject-name').get_text(strip=True)
                group_name = lesson.find('div', class_='lesson-group-name').get_text(strip=True)
                if 'ID' in group_name or "ОБЖ" in group_name:
                    continue
                room = lesson.find('div', class_='lesson-room').get_text(strip=True)
                day = days[lesson_row.find_all('td').index(lesson)]
                if time_range and subject_name and group_name and room:
                    text_timetable += f"{day}:\n{time_range} {subject_name} {group_name} {room}\n"
                    if day not in timetable:
                        timetable[day] = []
                    timetable[day].append({
                        "name": subject_name,
                        "group": group_name,
                        "start": time_range.split(' ─ ')[0],
                        "end": time_range.split(' ─ ')[1],
                        "where": room
                    })

        return name, grade, login, nastavnik, pansion, commanda, house, dorm, timetable
    except IndexError:
        return 401


def gen_unique_cookie():
    users = get_users()
    cookie_value = None
    while True:
        cookie_value = secrets.token_hex(16)
        unique = True
        for key in users:
            if users[key].get('cookie', False) == cookie_value:
                unique = False
                break
        if unique:
            break
    return cookie_value


def get_user_state(user_id: str) -> int:
    try:
        user_id = str(user_id)
        users = get_users()
        return users.get(user_id, {}).get('state', STATE_NONE)
    except TypeError:
        print('TypeError')


def is_choosing_person(login_: str) -> int:
    user_id = str(login_)
    messages = get_messages()
    if login_ not in messages:
        return 401


def update_user_state(user_id, state, data: map = None):
    try:
        if data is None:
            data = {}
        users = get_users()
        users[str(user_id)] = users.get(str(user_id), {}) | {'state': state, **data}
        set_users(users)
    except TypeError:
        print('TypeError')


def update_user_info(user_id, data: map = None):
    try:
        if data is None:
            data = {}
        users = get_users()
        users[str(user_id)] = users.get(str(user_id), {}) | data
        set_users(users)
    except TypeError:
        print('TypeError')


def get_all_groups(user_id):
    try:
        user_id = str(user_id)
        users = get_users()
        user_data = users.get(user_id, False)
        if not user_data:
            return 401
        cookie = user_data['cookie']
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Cookie': f'PHPSESSID={cookie}',
            'DNT': '1',
            'Referer': 'https://student.letovo.ru/student/academic/progress',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Not-A.Brand";v="99", "Chromium";v="124"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"'
        }

        response = requests.get('https://student.letovo.ru/student/1488/studyplan', headers=headers)

        soup = BeautifulSoup(response.content, 'html.parser')

        all_groups = {}
        table = soup.find('table', {'class': 'table table-hover'})

        for row in table.find('tbody').find_all('tr'):
            columns = row.find_all('td')
            group = columns[0].text.strip()
            subject = columns[1].text.strip()
            teacher = columns[2].text.strip()
            all_groups[group] = [teacher, subject]

        sorted_all_groups = sorted([key for key in all_groups])
        new_all_groups = {}
        for group in sorted_all_groups:
            new_all_groups[group] = all_groups[group]

        return new_all_groups
    except TypeError:
        print('TypeError')


def fill_teachers(user_id):
    try:
        user_id = str(user_id)
        users = get_users()
        user_data = users[user_id]
        all_groups = user_data['all_groups']
        for day in user_data['schedule']:
            for ind in range(len(user_data['schedule'][day])):
                lesson = user_data['schedule'][day][ind]
                users[user_id]['schedule'][day][ind]['teacher'] = all_groups[lesson['group']][0].split(', ')
        set_users(users)
        return 0
    except:
        return 1


def refresh_user_data(user_id):
    user_id = str(user_id)
    users = get_users()
    cookie = users[user_id]['cookie']
    logout(cookie)
    cookie = gen_unique_cookie()
    logout(cookie)
    token = get_token(cookie)
    user_data = users[user_id]
    login_ = user_data['login']
    password = user_data['password']
    response_code = login(login_, password, cookie, token)

    # delete previous user data from database
    del users[user_id]
    set_users(users)

    if response_code == 200:
        user_info = parse_inf(cookie)
        if user_info == 401:
            print("Неверный логин или пароль")
        else:
            create_user(user_id, *user_info)
            update_user_state(user_id, STATE_REGISTERED,
                              {'login': login_, 'cookie': cookie, 'token': token, 'password': password})
            all_groups = get_all_groups(user_id)
            # print(all_groups)
            print({'login': login_, 'cookie': cookie, 'token': token, 'password': password})
            if all_groups != 401 and all_groups != 1:
                update_user_info(user_id, {'all_groups': all_groups})
                fill_teachers(user_id)
    else:
        print('Неизвестная ошибка', end=' ~~~ ')
        print(response_code)


# refresh_user_data(896996640)
# refresh_user_data(1215863434)
