import telebot
from API import get_weather, get_daily_forecasts
from dotenv import load_dotenv
import os, json
load_dotenv()
token = os.getenv('token')
bot = telebot.TeleBot(token)
FORECASTS = {}

with open('f.json', 'r', encoding='utf-8') as file:
    users = json.load(file)
with open('f2.json', 'r', encoding='utf-8') as file:
    cities = json.load(file)


@bot.message_handler(commands=['start'])
def start(message):
    hello = 'Добрый день, я ваш персональный метеоролог.'
    bot.send_message(message.chat.id, text=hello, reply_markup=keyboard_lobby())
    str_id = str(message.chat.id)
    if str(str_id) not in users:
        change_city(message)
    else:
        print(users[str_id])
    

def change_city(message):
    bot.send_message(message.chat.id, text='Укажите название города')
    bot.register_next_step_handler(message, save_city)

def save_city(message):
    users[str(message.chat.id)] = message.text
    with open('f.json', 'w', encoding='utf-8') as file:
        json.dump(users, file, ensure_ascii=False)
    with open('f2.json', 'w', encoding='utf-8') as file:
        if str(message.chat.id) in cities:
            if message.text not in cities[str(message.chat.id)]:
                cities[str(message.chat.id)].append(message.text)
        else:
            cities[str(message.chat.id)] = [message.text]
        json.dump(cities, file, ensure_ascii=False)
    bot.send_message(message.chat.id, text=f'Город {message.text} успешно сохранен!', reply_markup=keyboard_lobby())
    

def keyboard_lobby():
    keyboard = telebot.types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=False)
    button1 = telebot.types.KeyboardButton('Текущая погода')
    button2 = telebot.types.KeyboardButton('Подробный прогноз на дату')
    button3 = telebot.types.KeyboardButton('Сменить город')
    button4 = telebot.types.KeyboardButton('Мои города')
    keyboard.add(button1, button2)
    keyboard.add(button3, button4)
    return keyboard

def cities_history(message):
    history_of_cities = cities[str(message.chat.id)]
    my_cities = telebot.types.InlineKeyboardMarkup()
    for city in history_of_cities:
        button = telebot.types.InlineKeyboardButton(text=city, callback_data='Город:' + city)
        my_cities.add(button)
    bot.send_message(message.chat.id, text='Выберите нужный город: ', reply_markup=my_cities)

@bot.callback_query_handler(func=lambda call: 'Город:' in call.data)
def show_cities(call):
    city_name = call.data.split(':')[1]
    bot.send_message(call.message.chat.id, text='\n'.join(get_weather(city_name)))
    print(city_name)


def current_message(message):
    try:
        weather = get_weather(users[str(message.chat.id)])
        answer = '\n'.join(weather)
    except:
        answer = 'Погода по данному городу не найдена'
    bot.send_message(message.chat.id, text=answer)

def days_buttons(message):
    FORECASTS.update(get_daily_forecasts(users[str(message.chat.id)]))
    days_keyboard = telebot.types.InlineKeyboardMarkup()
    for date in FORECASTS.keys():
        button = telebot.types.InlineKeyboardButton(text=date, callback_data=date)
        days_keyboard.add(button)
    bot.send_message(message.chat.id, text='Выберите нужный день: ', reply_markup=days_keyboard)

@bot.callback_query_handler(func=lambda call: ':' not in call.data)
def hours_button(call):
    date = call.data
    hours_keyboard = telebot.types.InlineKeyboardMarkup()
    for hour in FORECASTS[date].keys():
        button = telebot.types.InlineKeyboardButton(text=hour, callback_data=f'{date} {hour}')
        hours_keyboard.add(button)
    bot.send_message(call.message.chat.id, text='Выберите нужное время: ', reply_markup=hours_keyboard)

@bot.callback_query_handler(func=lambda call: ":" in call.data)
def show_forecast(call):
    data = call.data.split()
    date, hour = data[0], data[1]
    forecast = FORECASTS[date][hour]
    answer = f"Прогноз на {date}, {hour}:\n" + '\n'.join(forecast)
    bot.send_message(call.message.chat.id, text=answer)

@bot.message_handler(content_types=['text'])
def check_message(message):
    if message.text == 'Текущая погода':
        current_message(message)
    elif message.text == 'Сменить город':
        change_city(message)
    elif message.text == 'Подробный прогноз на дату':
        days_buttons(message)
    elif message.text == 'Мои города':
        cities_history(message)
    else:
        bot.send_message(message.chat.id, text='Я вас не понимаю')

bot.polling()

