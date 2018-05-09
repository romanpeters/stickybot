import time
import datetime
from urllib.request import urlopen, Request
from urllib.error import HTTPError
import pytz
import locale
import json
import socket
import telepot
from pprint import pprint
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultPhoto

from redacted import API_KEY, KOALA_COOKIE

BOTNAME = '@stickyutrechtbot'
utc = pytz.timezone('CET')
agenda_time_stamp = {}


try:
    locale.setlocale(locale.LC_TIME, "nl_NL.utf8")
except locale.Error:
    locale.setlocale(locale.LC_TIME, "nl_NL")


def chat(msg):
    """on chat message"""
    time.sleep(0.1)  # only necessary if reply from bot appears before command
    content_type, chat_type, chat_id = telepot.glance(msg)
    pprint(msg)
    if content_type == 'text':
        print(msg['chat']['id'], msg['text'])
        if msg['text'][0] == '/':
            command = command_parser(msg['text'])
            if command:
                switch_case[command](msg)


def start(msg):
    """Welke opdrachten zijn er?"""
    chat_id = msg['chat']['id']
    unique_values = []
    commands = []
    for value in switch_case:
        if switch_case[value] not in unique_values:
            if value is not 'start':
                unique_values.append(switch_case[value])
                commands.append(f"/{value} - {switch_case[value].__doc__}")
    bot.sendMessage(chat_id, "Mogelijke opdrachten:\n{0}".format('\n'.join(sorted(commands))))


def agenda(msg):
    """Wanneer is de volgende activiteit?"""
    chat_id = msg['chat']['id']
    req = urlopen('https://koala.svsticky.nl/api/activities/')
    data = req.read().decode('utf-8')
    api = json.loads(data)
    n = 0
    event = api[n]
    while datetime.datetime.strptime(event.get('start_date')[:-6], "%Y-%m-%dT%H:%M:%S") < datetime.datetime.now():
        event = api[n + 1]

    name = event.get('name')
    location = event.get('location')
    participants = event.get('participant_counter')
    start = date_to_string(event)

    if event.get('poster') is None:
        bot.sendMessage(chat_id, f'{name} ({participants})\n{start}\nLocatie: {location}')
    else:
        event_id = get_event_id_from_poster_url(event.get('poster'))
        button = InlineKeyboardMarkup(inline_keyboard = [[InlineKeyboardButton(text='Meer info', callback_data=f'/activiteit {event_id}')]])
        bot.sendPhoto(chat_id, event.get('poster'), f'{name} ({participants})\n{start}\nLocatie: {location}', reply_markup=button)


def activiteit(msg):
    """Vertel meer over deze activiteit"""
    chat_id = msg['chat']['id']
    numbers = [int(i) for i in msg['text'].split() if i.isdigit()]
    for possible_id in numbers:
        try:
            build = Request(f'https://koala.svsticky.nl/api/activities/{possible_id}')
            build.add_header('Cookie', f'remember_user_token={KOALA_COOKIE}')
            req = urlopen(build)
        except HTTPError:
            req = None

        if req:
            data = req.read().decode('utf-8')
            event = json.loads(data)
            event_url = f'https://koala.svsticky.nl/activities/{possible_id}'

            bot.sendMessage(chat_id,
                            f"{event.get('description')}\n"
                            f"{event_url}\n"
                            f"{'_Je kunt je niet meer inschrijven voor deze activiteit._' if event.get('enrollable') == False else ''}",
                            parse_mode='Markdown',
                            )



def get_event_id_from_poster_url(poster_url: str) -> int:
    """Include the id in the API already"""
    this_is_dumb = poster_url[poster_url.index('/activities/')+12:]
    yes_it_is = this_is_dumb[this_is_dumb.index('/'):]
    return int(this_is_dumb.replace(yes_it_is, ""))




def bier(msg):
    """Kan ik al bier kopen?"""
    chat_id = msg['chat']['id']
    now = datetime.datetime.now()
    biertijd = now.replace(hour=16, minute=0, second=0, microsecond=0)
    dag = utc.localize(now).strftime('%A')
    if dag is 'zaterdag' or dag is 'zondag':
        response = 'Het is weekend, je zult je bier ergens anders moeten halen'
    elif (now - biertijd) > datetime.timedelta(hours=0):
        if now.replace(second=0, microsecond=0) == biertijd:
            response = "TIJD VOOR BIER!"
        else:
            response = f"Het is {(now - biertijd).seconds // 60} minuten over bier"
    else:
        response = f"Het is {((biertijd - now).seconds // 60) + 1} minuten voor bier"
    bot.sendMessage(chat_id, response)

def stickers(msg):
    """Mag ik een sticker?"""
    chat_id = msg['chat']['id']
    text = 'Sticker packs:'
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [dict(text='Sticky Stickers', url='https://telegram.me/addstickers/Sticky_stickers')],
        [dict(text='Meer Sticky Stickers', url='https://telegram.me/addstickers/SuperSticky')],
    ])
    bot.sendMessage(chat_id, text, reply_markup=reply_markup)

def foodtruck(msg):
    """Welke foodtruck staat er vandaag?"""
    chat_id = msg['chat']['id']
    dag = utc.localize(datetime.datetime.now()).strftime('%A')
    message_list = msg['text'].split()
    with open('.foodtruck.json', 'r') as f:
        ft_data = json.load(f)

    if not ft_data[dag]:
        bot.sendMessage(chat_id, "Vandaag staat er geen foodtruck")
    else:
        bot.sendVenue(chat_id, 52.087285, 5.168533, ft_data[dag], dag.title())

def command_parser(command_input: str) -> str:
    """Parses commands"""
    command = command_input.split()[0][1:500].lower()  # limit + make lowercase
    if '@' in command:
        i = command.index('@')
        if command[i:i+len(BOTNAME)] == BOTNAME:
            command = command[:i]
        else:  # ignore command
            command = None
    return command


def date_to_string(event: dict) -> str:
    """Pakt de datetime van een event en maakt er een mooie zin van"""
    if len(event.get('start_date')) == 25:
        start_time = datetime.datetime.strptime(event.get('start_date')[:-6], "%Y-%m-%dT%H:%M:%S")
    elif len(event.get('start_date')) == 10:
        start_time = datetime.datetime.strptime(event.get('start_date')[:10], "%Y-%m-%d")
    else:
        start_time = ''
    if start_time != '':
        start_time = utc.localize(start_time)
        start_time = start_time.strftime('%A %d %B %H:%M uur')
        start_time = start_time[0].upper() + start_time[1:]
    return start_time


switch_case = {'start': start,
               'agenda': agenda,
               'activiteiten': agenda,
               'stickers': stickers,
               'bier': bier,
               'activiteit': activiteit,
               'foodtruck': foodtruck,
               }


def inline_query(msg):
    """Posters sturen via inline query"""
    def compute():
        """Processing"""
        req = urlopen('https://koala.svsticky.nl/api/activities/')
        data = req.read().decode('utf-8')
        api = json.loads(data)
        inline_result = []
        for event in api:
            if event.get('poster') is not None:
                name = event.get('name')
                start = date_to_string(event)

                result = InlineQueryResultPhoto(id=event.get('name'),
                                                title=event.get('name'),
                                                photo_url=event.get('poster'),
                                                thumb_url=event.get('poster'),
                                                caption=f'{name} ({event.get("participant_counter")})\n'
                                                        f'{start}',
                                                )
                query = msg['query']
                if query.lower() in event.get('name').lower() or query is '':
                    inline_result.append(result)
        return inline_result

    answerer.answer(msg, compute)


def callback_query(callback):
    """Creates a msg from the callback query data as if it was sent by the user"""
    query_id, from_id, query_data = telepot.glance(callback, flavor='callback_query')
    msg = {'chat': {}}
    msg['chat']['id'] = callback['message']['chat']['id']
    msg['chat']['type'] = 'text'
    msg['text'] = query_data
    chat(msg)


if __name__ == '__main__':
    print('Listening...')
    bot = telepot.Bot(API_KEY)
    answerer = telepot.helper.Answerer(bot)
    bot.message_loop({'chat': chat,
                      'inline_query': inline_query,
                      'callback_query': callback_query,
                      })
    while 1:
        time.sleep(10)

