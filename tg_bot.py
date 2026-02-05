import telebot, psycopg2

conn = psycopg2.connect('postgresql://postgres:@:5433/database') # здесь указать БД
curs = conn.cursor()
curs.execute("""CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY, 
                user_id BIGINT NOT NULL, 
                task_id INT NOT NULL, 
                name TEXT NOT NULL, 
                is_completed BOOLEAN DEFAULT FALSE)""")
bot = telebot.TeleBot('MY_BOT_TOKEN') # здесь указать токен для бота

@bot.message_handler(commands=['start', 'help'])
def starting(message):
    bot.send_message(message.from_user.id, 'Telegram-бот для управления ту-ду-листом.\n'
                                           'Список команд:\n'
                                           '/list - вывести список текущих задач\n'
                                           '/add <название> - добавить новую задачу\n'
                                           '/complete <номер> - отметить задачу как выполненную\n'
                                           '/delete <номер> - удалить задачу по номеру\n'
                                           '/help - вывести это сообщение')
@bot.message_handler(commands=['list'])
def list_tasks(message):
    curs.execute(f"""SELECT task_id, name, is_completed FROM tasks WHERE user_id = '{message.from_user.id}' ORDER BY task_id""")
    result = curs.fetchall()
    if not result: bot.send_message(message.from_user.id, 'Список пуст.')
    else:
        text = 'Список задач:'
        for row in result:
            text += f'\nЗадача №{row[0]}: {row[1]} {"✅" if row[2] else "❌"}'
        bot.send_message(message.from_user.id, text)
@bot.message_handler(commands=['add'])
def add_task(message):
    name = message.text[4:].strip()
    if not name: bot.send_message(message.from_user.id, 'Нужно указать название.')
    else:
        curs.execute(f"""INSERT INTO tasks (user_id, task_id, name) 
                        VALUES ('{message.from_user.id}',
                        COALESCE((SELECT task_id FROM tasks WHERE user_id = {message.from_user.id} ORDER BY task_id DESC LIMIT 1), 0) + 1,
                        '{name}')""")
        conn.commit()
        bot.send_message(message.from_user.id, f'Задача "{name}" добавлена.')
@bot.message_handler(commands=['complete'])
def compete_task(message):
    index = message.text[9:].strip()
    if not index.isdigit(): bot.send_message(message.from_user.id, 'Нужно указать номер задачи.')
    else:
        try:
            curs.execute(f"""UPDATE tasks SET is_completed = TRUE WHERE user_id = '{message.from_user.id}' AND task_id = {index} RETURNING name""")
            conn.commit()
            bot.send_message(message.from_user.id, f'Задача "{curs.fetchone()[0]}" завершена.')
        except TypeError: bot.send_message(message.from_user.id, 'Такой задачи не существует.')
@bot.message_handler(commands=['delete'])
def delete_task(message):
    index = message.text[7:].strip()
    if not index.isdigit(): bot.send_message(message.from_user.id, 'Нужно указать номер задачи.')
    else:
        try:
            curs.execute(f"""DELETE FROM tasks WHERE user_id = '{message.from_user.id}' AND task_id = {index} RETURNING name""")
            conn.commit()
            bot.send_message(message.from_user.id, f'Задача "{curs.fetchone()[0]}" удалена.')
        except TypeError: bot.send_message(message.from_user.id, 'Такой задачи не существует.')
@bot.message_handler(func=None)
def others(message):
    bot.send_message(message.from_user.id, 'Неверный формат команды.')

bot.polling(none_stop=True)
curs.close()
conn.close()