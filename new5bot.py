import sqlite3
from datetime import datetime
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import pandas as pd
from io import BytesIO

# Connect to SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('users.db', check_same_thread=False)
cursor = conn.cursor()

admin_ids = [679030634, 987654321]
user_classes = {}
# Create table to store user data
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    class TEXT,
    phone_number TEXT,
    registration_time TEXT,
    referrer_id TEXT,
    user_name TEXT DEFAULT "unknown"
)
''')


conn.commit()
# Создаем таблицы в базе данных
cursor.execute('''
CREATE TABLE IF NOT EXISTS sozvon (
    user_id INTEGER PRIMARY KEY
);
''')
conn.commit()

cursor.execute('''
CREATE TABLE IF NOT EXISTS kurs (
    user_id INTEGER PRIMARY KEY
);
''')
conn.commit()

cursor.execute('''
CREATE TABLE IF NOT EXISTS pobediteli (
    user_id INTEGER PRIMARY KEY
);
''')
conn.commit()




# Initialize the bot with your token
bot = telebot.TeleBot('6708762418:AAFEgHko1kjBUrbO77Xd_nUjVC9SuTi1x6A')

# Command to start the bot interaction
@bot.message_handler(commands=['start'])
def send_welcome(message):
    referral_id = None
    if len(message.text.split()) > 1:  # Проверяем наличие реферального ID
        referral_id = message.text.split()[1]
        try:
            # Проверяем, не является ли реферальный ID нашим существующим пользователем (дополнительная валидация)
            referrer_id = int(referral_id)  # Преобразуем в int, чтобы избежать SQL инъекций
            with sqlite3.connect('users.db', check_same_thread=False) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT user_name FROM users WHERE user_id = ?', (referrer_id,))
                referrer = cursor.fetchone()
                if referrer:
                    # Регистрируем нового пользователя с реферальным ID
                    registration_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    user_name = message.from_user.first_name + ' ' + (
                        message.from_user.last_name if message.from_user.last_name else '')
                    cursor.execute(
                        'INSERT OR IGNORE INTO users (user_id, class, phone_number, registration_time, user_name, referrer_id) VALUES (?, ?, ?, ?, ?, ?)',
                        (message.from_user.id, 'unknown', 'unknown', registration_time, user_name, referrer_id))
                    conn.commit()

                    # Награда для пригласившего пользователя: добавляем его еще раз в таблицу
                    cursor.execute(
                        'INSERT OR IGNORE INTO users (user_id, class, phone_number, registration_time, user_name, referrer_id) VALUES (?, ?, ?, ?, ?, ?)',
                        (referrer_id, 'unknown', 'unknown', registration_time, referrer[0], None))
                    conn.commit()

                    # Сообщение пользователю о регистрации
                    bot.send_message(message.chat.id,
                                     "Вы успешно зарегистрированы! Спасибо за приглашение от вашего друга!")
        except ValueError:
            # Если referral_id не является числом, игнорируем его
            pass # Здесь вы можете добавить логику для награждения пользователя, который поделился реферальной ссылкой

    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("11 класс (ЕГЭ 2024)", callback_data="11"),
               InlineKeyboardButton("10 класс (ЕГЭ 2025)", callback_data="10"),
               InlineKeyboardButton("9 класс (ОГЭ 2024)", callback_data="9"),
               InlineKeyboardButton("8 класс и ниже (ОГЭ 2025)", callback_data="8"))

    # Путь к файлу фото
    photo_path = 'priv.png'
    with open(photo_path, 'rb') as photo:
        bot.send_photo(message.chat.id, photo,
                       caption="Привет! 👋\n\nЭто бот поможет нам зарегистрировать тебя на розыгрыш!")

    # Отправляем сообщение с инлайн-клавиатурой
    bot.send_message(message.chat.id, "Для начала, выбери в каком ты классе 👇", reply_markup=markup)
# Handler for class selection
@bot.callback_query_handler(func=lambda call: call.data in ["11", "10", "9", "8"])
def query_handler(call):
    bot.answer_callback_query(callback_query_id=call.id)
    # Получаем данные из callback_data, чтобы узнать, какую кнопку нажал пользователь
    class_selected = call.data
    # Обновляем информацию о пользователе в базе данных, записывая его класс
    user_id = call.from_user.id
    cursor.execute('UPDATE users SET class = ? WHERE user_id = ?', (class_selected, user_id))
    conn.commit()
    # Удаляем кнопки, отправляя пустую разметку
    bot.delete_message(call.message.chat.id, call.message.message_id)
     # Продолжаем с запросом номера телефона
    bot.send_message(call.message.chat.id, 'Супер! Также нам нужен номер телефона, чтобы мы могли связаться с тобой, если ты выиграешь 🥳\n\nНажми, пожалуйста, кнопку «Оставить номер телефоан»📱', reply_markup=phone_number_request())


# Request for user's phone number

def phone_number_request():
    markup = ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    button_phone = KeyboardButton(text="Отправить номер телефона", request_contact=True)
    markup.add(button_phone)
    return markup

# Функция для создания реферальной ссылки
def generate_referral_link(user_id):
    return f"https://t.me/testoviy56_bot?start={user_id}"

def send_invite_message(chat_id):
    markup = InlineKeyboardMarkup()
    invite_button = InlineKeyboardButton("Пригласить друга", callback_data="send_invite_message")
    markup.add(invite_button)
    bot.send_message(chat_id, "Регистрация прошла успешно!\n\nТеперь ты есть в списке участников, среди которых мы будем разыгрывать призы в прямом эфире 27 апреля в 14:00 по мск 🔥\n\nЧто ты сможешь выиграть?\n— Созвон с преподавателем (10 победителей). \n— Место на интенсиве «Мясорубка» (33 победителя).\n\nПриходи на эфир «Как подготовиться к ОГЭ за неделю?», чтобы узнать, кто заберёт призы от «100балльного», а ещё:\n— какова статистика сдающих ОГЭ и что на неё влияет;\n— как побороть ВСЕ страхи перед ОГЭ; \n— правда ли, что можно взять ответы на ОГЭ, и где; \n— что такое «Мясорубка», и как она поможет затащить экзамены на 5.\n\nНо если хочешь увеличить свои шансы на победу, то приглашай на трансляцию друзей!\n\nКак это работает: сколько друзей пригласишь на трансляцию, столько раз твоё имя попадёт в список участников, увеличивая шансы на победу!\n\nЧтобы мы могли понять, что друг пришёл именно от тебя, жми на кнопку ниже.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "send_invite_message")
def handle_invite_callback(call):
    bot.answer_callback_query(call.id)
    # Ссылка для приглашения
    referral_link = generate_referral_link(call.from_user.id)  # Генерация реферальной ссылки
    text = f"Лови! Это уникальная ссылка, по которой ты можешь пригласить друга на трансляцию:\n\n{referral_link}\n\nПросто отправь ему ссылку, чтобы он зарегистрировался на эфир, и твоё имя автоматически добавится в список участников ещё раз 💜"
    photo_path = 'ref.png'
    with open(photo_path, 'rb') as photo:
        bot.send_photo(call.message.chat.id, photo=photo, caption=text)
# Handler for receiving contact information
@bot.message_handler(content_types=['contact'])
def contact_handler(message):
    user_id = message.from_user.id
    phone_number = message.contact.phone_number
    user_name = message.from_user.first_name
    if message.from_user.last_name:
        user_name += ' ' + message.from_user.last_name
    # Получаем информацию о классе из сохраненных данных
    class_info = user_classes.get(user_id, 'unknown')  # Если класс не найден, используем 'unknown'
    registration_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Далее идет код для сохранения информации в базу данных
    with sqlite3.connect('users.db', check_same_thread=False) as conn:
        cursor = conn.cursor()
        # Проверяем, существует ли пользователь
        cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
        if cursor.fetchone() is None:
            # Если пользователя нет, добавляем его
            cursor.execute(
                'INSERT INTO users (user_id, class, phone_number, registration_time, user_name, referrer_id) VALUES (?, ?, ?, ?, ?, ?)',
                (user_id, class_info, phone_number, registration_time, user_name, None))
        else:
            # Если пользователь существует, обновляем его данные
            cursor.execute(
                'UPDATE users SET class = ?, phone_number = ?, user_name = ? WHERE user_id = ?',
                (class_info, phone_number, user_name, user_id))
        conn.commit()




    # Удаляем предыдущее сообщение пользователя с номером телефона и сообщение бота с запросом номера
    bot.delete_message(message.chat.id, message.message_id - 1)
    bot.delete_message(message.chat.id, message.message_id)

    # Отправляем пригласительное сообщение
    send_invite_message(message.chat.id)



    # Отправляем сообщение с реферальной ссылкой
   # referral_link = generate_referral_link(user_id)
   # bot.send_message(message.chat.id, f"Регистрация прошла успешно!\n\nТеперь ты есть в списке участников, среди которых мы будем разыгрывать призы в прямом эфире 27 апреля в 14:00 по мск 🔥\n\nЧто ты сможешь выиграть?\n— Созвон с преподавателем (10 победителей). \n— Место на интенсиве «Мясорубка» (33 победителя).\n\nПриходи на эфир «Как подготовиться к ОГЭ за неделю?», чтобы узнать, кто заберёт призы от «100балльного», а ещё:\n— какова статистика сдающих ОГЭ и что на неё влияет;\n— как побороть ВСЕ страхи перед ОГЭ; \n— правда ли, что можно взять ответы на ОГЭ, и где; \n— что такое «Мясорубка», и как она поможет затащить экзамены на 5.\n\nНо если хочешь увеличить свои шансы на победу, то приглашай на трансляцию друзей!\n\nКак это работает: сколько друзей пригласишь на трансляцию, столько раз твоё имя попадёт в список участников, увеличивая шансы на победу!\n\nЧтобы мы могли понять, что друг пришёл именно от тебя, жми на кнопку ниже. \n\nТвоя реферальная ссылка: {referral_link}")

def generate_referral_link(user_id):
    # Замените на логику вашей реферальной ссылки
    return f"https://t.me/testoviy56_bot?start={user_id}"

# Admin command to dump all users' data
@bot.message_handler(commands=['dump_users'])
def dump_users(message):
    user_id = message.from_user.id
    if user_id in admin_ids:
        # Получаем данные из базы данных
        with sqlite3.connect('users.db', check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users')
            users_data = cursor.fetchall()

        # Создаем DataFrame
        df = pd.DataFrame(users_data, columns=['ID', 'Class', 'Phone', 'Registered', 'Name', 'Referrer ID'])  # Добавлен Referrer ID

        # Сохраняем DataFrame в файл Excel
        excel_file = BytesIO()
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Users')

        # Перематываем на начало файла перед отправкой
        excel_file.seek(0)

        # Отправляем файл
        bot.send_document(message.chat.id, (
        'users_data.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
    else:
        bot.send_message(message.chat.id, "У вас нет прав для использования этой команды.")
# Comment out the following line before deploying the code to avoid running the bot during development
# bot.polling()

@bot.message_handler(commands=['broadcast'])
def handle_broadcast(message):
    user_id = message.from_user.id
    if user_id in admin_ids:
        # Сохраняем ID админа, который начал рассылку
        admin_chat_id = message.chat.id
        msg = bot.send_message(admin_chat_id, "Введите текст сообщения для рассылки:")
        bot.register_next_step_handler(msg, send_broadcast)
    else:
        bot.send_message(message.chat.id, "У вас нет прав для использования этой команды.")

def send_broadcast(message):
    text = message.text
    with sqlite3.connect('users.db', check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM users')
        user_ids = cursor.fetchall()
        for user_id in user_ids:
            try:
                bot.send_message(user_id[0], text)
            except Exception as e:
                print(f"Не удалось отправить сообщение пользователю {user_id[0]}: {e}")

    bot.send_message(message.chat.id, "Сообщения отправлены.")

@bot.message_handler(commands=['custom_broadcast'])
def custom_broadcast_init(message):
    user_id = message.from_user.id
    if user_id in admin_ids:
        msg = bot.send_message(message.chat.id, "Введите ID пользователей через запятую:")
        bot.register_next_step_handler(msg, custom_broadcast_get_text)
    else:
        bot.send_message(message.chat.id, "У вас нет прав для использования этой команды.")

def custom_broadcast_get_text(message):
    # Сохраняем введенные ID в временную переменную
    global temp_user_ids
    temp_user_ids = message.text.split(',')
    msg = bot.send_message(message.chat.id, "Введите текст сообщения для рассылки:")
    bot.register_next_step_handler(msg, send_custom_broadcast)

def send_custom_broadcast(message):
    text = message.text
    failed_users = []
    for user_id in temp_user_ids:
        try:
            bot.send_message(int(user_id.strip()), text)
        except Exception as e:
            failed_users.append(user_id)
            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

    if failed_users:
        bot.send_message(message.chat.id, f"Сообщения отправлены, но не удалось доставить следующим пользователям: {', '.join(failed_users)}")
    else:
        bot.send_message(message.chat.id, "Все сообщения успешно отправлены.")

@bot.message_handler(commands=['add_to_sozvon'])
def add_to_sozvon(message):
    if message.from_user.id in admin_ids:
        msg = bot.send_message(message.chat.id, "Введите ID пользователя для добавления в 'Созвон':")
        bot.register_next_step_handler(msg, process_adding_to_sozvon)
    else:
        bot.send_message(message.chat.id, "У вас нет прав для использования этой команды.")

def process_adding_to_sozvon(message):
    user_id = int(message.text.strip())
    with sqlite3.connect('users.db', check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO sozvon (user_id) VALUES (?)", (user_id,))
        conn.commit()
    bot.send_message(message.chat.id, "Пользователь добавлен в 'Созвон'.")

@bot.message_handler(commands=['add_to_kurs'])
def add_to_kurs(message):
    if message.from_user.id in admin_ids:
        msg = bot.send_message(message.chat.id, "Введите ID пользователя для добавления в 'Курс':")
        bot.register_next_step_handler(msg, process_adding_to_kurs)
    else:
        bot.send_message(message.chat.id, "У вас нет прав для использования этой команды.")

def process_adding_to_kurs(message):
    user_id = int(message.text.strip())
    with sqlite3.connect('users.db', check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO kurs (user_id) VALUES (?)", (user_id,))
        conn.commit()
    bot.send_message(message.chat.id, "Пользователь добавлен в 'Курс'.")

@bot.message_handler(func=lambda message: message.text.lower() == "слон")
def add_to_pobediteli(message):
    with sqlite3.connect('users.db', check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM sozvon WHERE user_id = ? UNION SELECT 1 FROM kurs WHERE user_id = ?", (message.from_user.id, message.from_user.id))
        if cursor.fetchone():
            cursor.execute("INSERT OR IGNORE INTO pobediteli (user_id) VALUES (?)", (message.from_user.id,))
            conn.commit()
            bot.send_message(message.chat.id, "Вы добавлены в список 'Победители'.")
        else:
            bot.send_message(message.chat.id, "Вы не зарегистрированы в 'Созвон' или 'Курс'.")

@bot.message_handler(commands=['dump_pobediteli'])
def dump_pobediteli(message):
    if message.from_user.id in admin_ids:
        with sqlite3.connect('users.db', check_same_thread=False) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM pobediteli")
            pobediteli_data = cursor.fetchall()
            df = pd.DataFrame(pobediteli_data, columns=['User ID'])
            excel_file = BytesIO()
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Pobediteli')
            excel_file.seek(0)
            bot.send_document(message.chat.id, ('pobediteli.xlsx', excel_file, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'))
    else:
        bot.send_message(message.chat.id, "У вас нет прав для использования этой команды.")


bot.polling(none_stop=True)
