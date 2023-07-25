import os
import time
from datetime import datetime, timedelta

import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType

import pickle
import config

vk_session = vk_api.VkApi(token=config.token)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, config.group_id)

# ID беседы, в которую нужно отправить сообщение
peer_id = config.peer_id

# ID группы
group_id = config.group_id

# ID пользователя, от которого бот будет принимать команды
admin_ids = config.admin_ids

# Словарь для хранения информации о пользователях
users = {}
muted_users = []
banned_users = []
scores = {}
date = ''

# Создание словаря для хранения ролей пользователей
roles = {}

# Подкачка данных из старой сессии
try:
    if not users and not date:
        if os.path.exists('data.pickle'):
            with open('data.pickle', 'rb') as f:
                data = pickle.load(f)
                date = data.get('date', '')
                admin_ids = data.get('admin_ids', [])
                users = data.get('users', {})
                scores = data.get('scores', {})
                banned_users = data.get('banned_users', [])
                muted_users = data.get('muted_users', [])
        else:
            date = ''
            users = {}
    print('Данные из старой сессии успешно загружены.')
except Exception as e:
    print(f'Ошибка при загрузке данных из старой сессии: {e}')

# Загрузка информации о работягах из словаря users
for user_id in users:
    roles[user_id] = 'Работяга'

# Добавление администраторов в словарь roles
for admin_id in admin_ids:
    roles[admin_id] = 'Администратор'
print('Бот начал слушать сообщения')
while True:
    try:
        for event in longpoll.listen():
            try:
                # проверка на события
                if 'action' in event.raw['object']['message']:
                    try:
                        # Обработка события приглашения забаненого в беседу
                        if event.raw['object']['message']['action']['type'] == 'chat_invite_user':
                            try:
                                user_id = event.raw['object']['message']['action']['member_id']
                                if user_id in banned_users:
                                    vk.messages.removeChatUser(
                                        chat_id=peer_id - 2000000000,
                                        user_id=user_id
                                    )
                                    continue
                            except Exception as e:
                                print(f'Произошла ошибка при приглашении забаненого в беседу: {e}')
                        # Обработка события входа по ссылке забаненого в беседу
                        elif event.raw['object']['message']['action']['type'] == 'chat_invite_user_by_invitelink':
                            try:
                                user_id = event.raw['object']['message']['action']['member_id']
                                if user_id in banned_users:
                                    vk.messages.removeChatUser(
                                        chat_id=peer_id - 2000000000,
                                        user_id=user_id
                                    )
                                    continue
                            except Exception as e:
                                print(f'Произошла ошибка при входа по ссылке забаненого в беседу: {e}')
                    except Exception as e:
                        print(f'Произошла ошибка при проверке события: {e}')

                if event.type == VkBotEventType.MESSAGE_NEW:
                    message = event.obj.message['text']
                    peer_id = event.obj.message['peer_id']
                    from_id = event.obj.message['from_id']

                    # Удаление сообщений от замьюченных пользователей
                    if from_id in muted_users:
                        vk.messages.delete(
                            delete_for_all=1,
                            peer_id=peer_id,
                            group_id=group_id,
                            conversation_message_ids=event.obj.message['conversation_message_id']
                        )
                        continue

                    # Сохранение данных в файл
                    try:
                        with open('data.pickle', 'wb') as f:
                            pickle.dump({'date': date, 'users': users, 'admin_ids': admin_ids, 'scores': scores,
                                         'banned_users': banned_users, 'muted_users': muted_users}, f)
                        print('Данные успешно сохранены в файл.')
                    except Exception as e:
                        print(f'Ошибка при сохранении данных в файл: {e}')

                    # Проверка текущей даты
                    try:
                        if date and datetime.now().strftime('%d.%m.%Y') == date:
                            for tag in users:
                                debt = users[tag]
                                score = scores.get(tag, 0) - debt * 2
                                scores[tag] = score
                                users[tag] += 5
                            response = f'До {date} каждый работяга должен сделать еще по 5 мемов.\n'
                            for tag, debt in users.items():
                                score = scores[tag]
                                response += f'{tag}, твой долг: {debt}. \nТекущий рейтинг: {score}\n'
                            vk.messages.send(
                                peer_id=peer_id,
                                message=response,
                                random_id=0
                            )
                            print('Авто-пинок был выполнен, все нормы обновлены.')

                            # Установка даты на следующий месяц
                            date_obj = datetime.strptime(date, '%d.%m.%Y')
                            next_month = date_obj + timedelta(days=31)
                            date = next_month.strftime('%d.%m.%Y')
                            print('Перевёл дату на следующий месяц')
                    except Exception as e:
                        print(f'Ошибка при работе с датой и авто-пинком: {e}')

                    # Распознавание, что сообщение адресовано боту
                    if message.startswith('!'):

                        # Обработка команды !рейтинг
                        if message == '!рейтинг':
                            try:
                                response = 'Рейтинг:\n\n'
                                sorted_users = sorted(users, key=lambda tag: scores.get(tag, 0), reverse=True)
                                for tag in sorted_users:
                                    user_id = tag.split('|')[0][3:]
                                    user = vk.users.get(user_ids=user_id)[0]
                                    name = user['first_name']
                                    surname = user['last_name']
                                    score = scores.get(tag, 0)
                                    response += f'{name} {surname}. Очки: {score}\n\n'
                                vk.messages.send(
                                    peer_id=peer_id,
                                    message=response,
                                    random_id=0
                                )
                            except Exception as e:
                                print(f'Ошибка при выполнении команды !рейтинг: {e}')

                        # Обработка команды !почет
                        elif message == '!почет':
                            try:
                                top_users = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
                                response = 'Побольше бы таких людей:\n\n'
                                for tag, score in top_users:
                                    user_id = tag.split('|')[0][3:]
                                    user = vk.users.get(user_ids=user_id)[0]
                                    name = user['first_name']
                                    surname = user['last_name']
                                    response += f'{name} {surname}. \nОчки: {score}\n\n'
                                vk.messages.send(
                                    peer_id=peer_id,
                                    message=response,
                                    random_id=0
                                )
                            except Exception as e:
                                print(f'Ошибка при выполнении команды !почет: {e}')

                        # Обработка команды !позор
                        elif message == '!позор':
                            try:
                                bottom_users = sorted([(tag, scores.get(tag, 0)) for tag in users], key=lambda x: x[1])[
                                               :3]
                                response = 'Поменьше бы таких людей:\n\n'
                                for tag, score in bottom_users:
                                    user_id = tag.split('|')[0][3:]
                                    user = vk.users.get(user_ids=user_id)[0]
                                    name = user['first_name']
                                    surname = user['last_name']
                                    response += f'{name} {surname}. \nОчки: {score}\n\n'
                                vk.messages.send(
                                    peer_id=peer_id,
                                    message=response,
                                    random_id=0
                                )
                            except Exception as e:
                                print(f'Ошибка при выполнении команды !позор: {e}')

                        # Обработка команды !я
                        elif message == '!я':
                            try:
                                user_key = None
                                for key in users:
                                    if f'id{from_id}' in key:
                                        user_key = key
                                        break

                                if user_key:
                                    user = vk.users.get(user_ids=from_id)[0]
                                    name = user['first_name']
                                    surname = user['last_name']
                                    debt = users.get(user_key, 0)
                                    score = scores.get(user_key, 0)
                                    response = f'{name} {surname}. Твой долг: {debt}. \nТекущий рейтинг: {score}'
                                else:
                                    response = 'Ты не являешься работягой...'

                                vk.messages.send(
                                    peer_id=peer_id,
                                    message=response,
                                    random_id=0
                                )
                            except Exception as e:
                                print(f'Ошибка при выполнении команды !долг: {e}')

                        # Обработка команды !бот
                        elif message == '!бот':
                            try:
                                response = 'На месте ✅'
                                vk.messages.send(
                                    peer_id=peer_id,
                                    message=response,
                                    random_id=0
                                )
                            except Exception as e:
                                print(f'Ошибка при выполнении команды !бот: {e}')

                        # Обработка команды !команды
                        elif message == '!команды':
                            try:
                                role = roles.get(from_id)
                                if role == 'Администратор':
                                    response = 'Доступные команды для администраторов:\n\n'
                                    response += '!+работяга @тег - добавить работягу\n'
                                    response += '!-работяга @тег - удалить работягу\n'
                                    response += '!+админ @тег - добавить администратора\n'
                                    response += '!-админ @тег - удалить администратора\n'
                                    response += '!бан @тег - забанить или разбанить человека\n'
                                    response += '!мут @тег - замьютить или размьютить\n'
                                    response += '!долги - показать долги всех работяг без их оповещения\n'
                                    response += '!пинок - "пнуть" всех работяг с ненулевым долгом\n'
                                    response += '!пинок @тег - "пнуть" конкретного работягу\n'
                                    response += '!+s число @тег - увеличить рейтинг на определенное число очков\n'
                                    response += '!-s число @тег - уменьшить рейтинг на определенное число очков\n'
                                    response += '!+ число @тег - увеличить долг на определенное число очков\n'
                                    response += '!- число @тег - уменьшить долг на определенное число очков\n'
                                    response += '!срок ХХ.ХХ.XXXX - установить срок выполнения долгов\n'
                                    response += '!рейтинг - показать рейтинг всех работяг\n'
                                    response += '!позор - показать плохих ребят\n'
                                    response += '!почет - показать отличных работяг\n'
                                    response += '!бот - пропинговать бота\n'
                                elif role == 'Работяга':
                                    response = 'Доступные команды для работяг:\n\n'
                                    response += '!рейтинг - показать рейтинг всех работяг\n'
                                    response += '!позор - показать плохих ребят\n'
                                    response += '!почет - показать отличных работяг\n'
                                    response += '!я - показать свой долг и рейтинг\n'
                                    response += '!бот - пропинговать бота\n'
                                else:
                                    response = 'Вы не являетесь администратором или работягой. Для тебя нет доступных команд.'
                                vk.messages.send(
                                    peer_id=peer_id,
                                    message=response,
                                    random_id=0
                                )
                            except Exception as e:
                                print(f'Ошибка при выполнении команды !команды: {e}')


                        # Проверка, что сообщение от админа
                        elif roles.get(from_id) == 'Администратор':
                            try:

                                # Обработка команды !+админ @тег
                                if message.startswith('!+админ'):
                                    try:
                                        parts = message.split()
                                        if len(parts) == 2:
                                            user_tag = parts[1]
                                            if user_tag.startswith('[') and '|' in user_tag and ']' in user_tag:
                                                user_id = int(user_tag.split('|')[0][3:])
                                                if user_id not in admin_ids:
                                                    admin_ids.append(user_id)
                                                    roles[user_id] = 'Администратор'
                                                    vk.messages.send(
                                                        peer_id=peer_id,
                                                        message=f'Пользователь с ID {user_id} был добавлен в список администраторов.',
                                                        random_id=0
                                                    )
                                                else:
                                                    vk.messages.send(
                                                        peer_id=peer_id,
                                                        message=f'Пользователь с ID {user_id} уже является администратором.',
                                                        random_id=0
                                                    )
                                    except Exception as e:
                                        print(f'Ошибка при выполнении команды !+админ: {e}')

                                # Обработка команды !-админ @тег
                                if message.startswith('!-админ'):
                                    try:
                                        parts = message.split()
                                        if len(parts) == 2:
                                            user_tag = parts[1]
                                            if user_tag.startswith('[') and '|' in user_tag and ']' in user_tag:
                                                user_id = int(user_tag.split('|')[0][3:])
                                                if user_id in admin_ids:
                                                    admin_ids.remove(user_id)
                                                    vk.messages.send(
                                                        peer_id=peer_id,
                                                        message=f'Пользователь с ID {user_id} был удален из списка администраторов.',
                                                        random_id=0
                                                    )
                                                else:
                                                    vk.messages.send(
                                                        peer_id=peer_id,
                                                        message=f'Пользователь с ID {user_id} не является администратором.',
                                                        random_id=0
                                                    )
                                    except Exception as e:
                                        print(f'Ошибка при выполнении команды !-админ: {e}')

                                # Обработка команды !+работяга @тег
                                if message.startswith('!+работяга'):
                                    try:
                                        tag = message.split()[1]
                                        if tag not in users:
                                            users[tag] = 0
                                        users[tag] += 5  # Долг
                                        vk.messages.send(
                                            peer_id=peer_id,
                                            message=f'{tag} работяга был добавлен! Он должен сделать {users[tag]} мемов.',
                                            random_id=0
                                        )
                                        print(f'Работяга добавлен. Словарь users: {users}')
                                    except Exception as e:
                                        print(f'Ошибка при выполнении команды !+работяга: {e}')

                                # Обработка команды !-работяга @тег
                                if message.startswith('!-работяга'):
                                    try:
                                        tag = message.split()[1]
                                        if tag in users:
                                            del users[tag]
                                            del scores[tag]
                                        vk.messages.send(
                                            peer_id=peer_id,
                                            message=f'{tag} работяга был удалён!',
                                            random_id=0
                                        )
                                        print(f'Работяга удален. Словарь users: {users}')
                                    except Exception as e:
                                        print(f'Ошибка при выполнении команды !-работяга: {e}')

                                # Обработка команды !+число @тег
                                if message.startswith('!+') and '@' in message:
                                    try:
                                        parts = message.split()
                                        num_str = parts[0][2:]
                                        if num_str.isdigit():
                                            num = int(num_str)
                                            tag = parts[1]
                                            if tag in users:
                                                users[tag] += num
                                                vk.messages.send(
                                                    peer_id=peer_id,
                                                    message=f'{tag} должен сделать {users[tag]} мемов.',
                                                    random_id=0
                                                )
                                                print(f'Долг работяги увеличен. Словарь users: {users}')
                                            if tag not in users:
                                                vk.messages.send(
                                                    peer_id=peer_id,
                                                    message='Это не работяга...',
                                                    random_id=0
                                                )
                                    except Exception as e:
                                        print(f'Ошибка при выполнении команды !+число @тег: {e}')

                                # Обработка команды !-число @тег
                                if message.startswith('!-') and '@' in message:
                                    try:
                                        parts = message.split()
                                        num_str = parts[0][2:]
                                        if num_str.isdigit():
                                            num = int(num_str)
                                            tag = parts[1]
                                            if tag in users:
                                                if users[tag] - num >= 0:
                                                    users[tag] -= num
                                                    if users[tag] != 0:
                                                        vk.messages.send(
                                                            peer_id=peer_id,
                                                            message=f'{tag} должен сделать ещё {users[tag]} мемов.',
                                                            random_id=0
                                                        )
                                                        print(f'Долг работяги уменьшен. Словарь users: {users}')
                                                    else:
                                                        score = scores.get(tag, 0) + 5
                                                        scores[tag] = score
                                                        vk.messages.send(
                                                            peer_id=peer_id,
                                                            message=f'{tag} выполнил всю норму и получил 5 очков рейтинга, поздравляю! '
                                                                    f'Текущий рейтинг: {score}',
                                                            random_id=0
                                                        )
                                                        print(
                                                            f'Долг работяги уменьшен, а рейтинг начислен. Словарь users: {users}')
                                                else:
                                                    vk.messages.send(
                                                        peer_id=peer_id,
                                                        message=f'Долг не должен быть отрицательным...',
                                                        random_id=0
                                                    )

                                            if tag not in users:
                                                vk.messages.send(
                                                    peer_id=peer_id,
                                                    message='Это не работяга...',
                                                    random_id=0
                                                )
                                    except Exception as e:
                                        print(f'Ошибка при выполнении команды !-число @тег: {e}')

                                # Обработка команды !пинок
                                if message.startswith('!пинок'):
                                    try:
                                        parts = message.split()
                                        if len(parts) == 2:
                                            user_tag = parts[1]
                                            if user_tag in users:
                                                debt = users[user_tag]
                                                date_obj = datetime.strptime(date, '%d.%m.%Y')
                                                days_left = (date_obj - datetime.now()).days
                                                response = f'{user_tag}, твой долг: {debt}.\n Выполни его за {days_left} дней.'
                                                vk.messages.send(
                                                    peer_id=peer_id,
                                                    message=response,
                                                    random_id=0
                                                )
                                            else:
                                                vk.messages.send(
                                                    peer_id=peer_id,
                                                    message=f'Пользователь с тегом {user_tag} не является работягой.',
                                                    random_id=0
                                                )
                                        else:
                                            # Обработка команды !пинок без аргументов
                                            response = ''
                                            for user_tag, debt in users.items():
                                                if debt != 0:
                                                    date_obj = datetime.strptime(date, '%d.%m.%Y')
                                                    days_left = (date_obj - datetime.now()).days
                                                    response += f'{user_tag}, твой долг: {debt}.\n Выполни его за {days_left} дней.\n\n'
                                            vk.messages.send(
                                                peer_id=peer_id,
                                                message=response,
                                                random_id=0
                                            )
                                    except Exception as e:
                                        print(f'Ошибка при выполнении команды !пинок: {e}')

                                # Обработка команды !срок ХХ.ХХ.XX
                                if message.startswith('!срок'):
                                    try:
                                        date = message.split()[1]

                                        response = f'До {date} каждый работяга должен выполнить норму.\n'
                                        for tag, debt in users.items():
                                            response += f'{tag}, твой долг: {debt}\n'
                                        vk.messages.send(
                                            peer_id=peer_id,
                                            message=response,
                                            random_id=0
                                        )
                                    except Exception as e:
                                        print(f'Ошибка при выполнении команды !срок XX.XX.XX: {e}')

                                # Обработка команды !-s число @тег
                                if message.startswith('!-s') and '@' in message:
                                    try:
                                        parts = message.split()
                                        num_str = parts[1]
                                        if num_str.isdigit():
                                            num = int(num_str)
                                            tag = parts[2]
                                            if tag in users:
                                                score = scores.get(tag, 0) - num
                                                scores[tag] = score
                                                vk.messages.send(
                                                    peer_id=peer_id,
                                                    message=f'У {tag} снято {num} очков рейтинга.\n Текущий рейтинг: {score}',
                                                    random_id=0
                                                )
                                            else:
                                                vk.messages.send(
                                                    peer_id=peer_id,
                                                    message='Это не работяга...',
                                                    random_id=0
                                                )
                                    except Exception as e:
                                        print(f'Ошибка при выполнении команды !-s число @тег: {e}')

                                # Обработка команды !+s число @тег
                                if message.startswith('!+s') and '@' in message:
                                    try:
                                        parts = message.split()
                                        num_str = parts[1]
                                        if num_str.isdigit():
                                            num = int(num_str)
                                            tag = parts[2]
                                            if tag in users:
                                                score = scores.get(tag, 0) + num
                                                scores[tag] = score
                                                vk.messages.send(
                                                    peer_id=peer_id,
                                                    message=f'{tag} получил {num} очков рейтинга.\n Текущий рейтинг: {score}',
                                                    random_id=0
                                                )
                                            else:
                                                vk.messages.send(
                                                    peer_id=peer_id,
                                                    message='Это не работяга...',
                                                    random_id=0
                                                )
                                    except Exception as e:
                                        print(f'Ошибка при выполнении команды !+s число @тег: {e}')

                                # Обработка команды !долги
                                if message == '!долги':
                                    try:
                                        response = ''
                                        sorted_users = sorted(users.items(), key=lambda x: x[1],
                                                              reverse=True)  # Сортировка по величине долга
                                        for user_tag, debt in sorted_users:
                                            if debt != 0:
                                                user_id = int(user_tag.split('|')[0][3:])
                                                users_list = vk.users.get(user_ids=user_id)
                                                if users_list:
                                                    user = users_list[0]
                                                    name = user['first_name']
                                                    surname = user['last_name']
                                                    date_obj = datetime.strptime(date, '%d.%m.%Y')
                                                    days_left = (date_obj - datetime.now()).days
                                                    response += f'{name} {surname}. Долг: {debt}.\n Должен выполнить его за {days_left} дней.\n\n'
                                                else:
                                                    response += f'Не удалось получить информацию о пользователе с тегом {user_tag}.\n'
                                        if response:
                                            vk.messages.send(
                                                peer_id=peer_id,
                                                message=response,
                                                random_id=0
                                            )
                                    except Exception as e:
                                        print(f'Ошибка при выполнении команды !долги: {e}')

                                # Обработка команды !мут @тег
                                if message.startswith('!мут'):
                                    try:
                                        tag = message.split()[1]
                                        user_id = int(tag.split('|')[0][3:])
                                        if user_id not in muted_users:
                                            if user_id not in admin_ids:
                                                # Добавьте user_id в список замьюченных пользователей
                                                muted_users.append(user_id)
                                                vk.messages.send(
                                                    peer_id=peer_id,
                                                    message=f'{tag} имей совесть, помолчи и подумай над своим поведением!',
                                                    random_id=0
                                                )
                                            else:
                                                vk.messages.send(
                                                    peer_id=peer_id,
                                                    message=f'Администратора нельзя заставить молчать',
                                                    random_id=0
                                                )
                                        else:
                                            muted_users.remove(user_id)
                                            vk.messages.send(
                                                peer_id=peer_id,
                                                message=f'{tag} твоя совесть очищена, можешь снова говорить.',
                                                random_id=0
                                            )
                                    except Exception as e:
                                        print(f'Ошибка при обработке команды !мут @тег: {e}')

                                    banned_users = []

                                # Обработка команды !бан @тег
                                if message.startswith('!бан'):
                                    try:
                                        tag = message.split()[1]
                                        user_id = int(tag.split('|')[0][3:])
                                        if user_id not in banned_users:
                                            if user_id not in admin_ids:
                                                vk.messages.removeChatUser(
                                                    chat_id=peer_id - 2000000000,
                                                    user_id=user_id
                                                )
                                                banned_users.append(user_id)
                                                vk.messages.send(
                                                    peer_id=peer_id,
                                                    message=f'{tag} был забанен.',
                                                    random_id=0
                                                )
                                            else:
                                                vk.messages.send(
                                                    peer_id=peer_id,
                                                    message=f'Администратора нельзя забанить',
                                                    random_id=0
                                                )
                                        else:
                                            banned_users.remove(user_id)
                                            vk.messages.send(
                                                peer_id=peer_id,
                                                message=f'{tag} был разбанен!',
                                                random_id=0
                                            )
                                    except Exception as e:
                                        print(f'Ошибка при обработке команды !бан @тег: {e}')

                            except Exception as e:
                                print(f'Ошибка при обработке админ команды: {e}')

                        else:
                            vk.messages.send(
                                peer_id=peer_id,
                                message='А ну руки убери гаденыш, не дорос еще',
                                random_id=0
                            )

            except Exception as e:
                print(f'[WARNING] Произошла ошибка: {e}')
    except Exception as e:
        print(f'Не был получен ответ от сервера. Повторное подключение через 15 секунд. Ошибка: {e}')
        time.sleep(15)
        continue
