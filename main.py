import time
import datetime
from urllib.request import urlopen
import pytz
import locale
import json
import socket
import telepot
from telepot.namedtuple import InlineKeyboardMarkup, InlineQueryResultPhoto
from mcstatus import MinecraftServer

from secret import API_KEY

BOTNAME = '@stickyutrechtbot'
utc = pytz.timezone('CET')
agenda_time_stamp = {}


try:
    locale.setlocale(locale.LC_TIME, "nl_NL.utf8")
except locale.Error:
    locale.setlocale(locale.LC_TIME, "nl_NL")


def chat(msg):
    """on chat message"""
    time.sleep(0.5)
    content_type, chat_type, chat_id = telepot.glance(msg)
    if content_type == 'text':
        print(msg['chat']['id'], msg['text'])
        if msg['text'][0] == '/':
            command = command_parser(msg['text'])
            if command:
                switch_case[command[0]](msg, command[1])


def start(msg, add):
    """Welke opdrachten zijn er?"""
    chat_id = msg['chat']['id']
    unique_values = []
    commands = []
    for value in switch_case:
        if switch_case[value] not in unique_values:
            if value is not 'start':
                unique_values.append(switch_case[value])
                commands.append("/{0} - {1}".format(value, switch_case[value].__doc__))
    bot.sendMessage(chat_id, 'Mogelijke opdrachten:\n{}'.format('\n'.join(sorted(commands))))

def agenda(msg, add):
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
    start = date_to_string(event)

    if event.get('poster') == None:
        bot.sendMessage(chat_id, '{0}\n{1}'.format(name, start))
    else:
        bot.sendPhoto(chat_id, event.get('poster'), '{0}\n{1}'.format(name, start))


def bier(msg, add):
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
            response = "Het is {0} minuten over bier".format((((now - biertijd).seconds // 60)))
    else:
        response = "Het is {0} minuten voor bier".format((((biertijd - now).seconds // 60) + 1))
    bot.sendMessage(chat_id, response)


def minecraft(msg, add):
    """Wie zitten er op minecraft?"""
    chat_id = msg['chat']['id']
    server = MinecraftServer.lookup("mc.stickyplay.nl")
    try:
        status = server.status()
    except socket.timeout:
        bot.sendMessage(chat_id, "Kan mc.stickyplay.nl niet bereiken :(")
        return
    if status.players.online == 0:
        bot.sendMessage(chat_id, "Er is niemand online op de Sticky Minecraft server")
    elif status.players.online == 1:
        bot.sendMessage(chat_id, "Er is 1 player online op de Sticky Minecraft server")
    else:
        bot.sendMessage(chat_id,
                        "Er zijn {0} players online op de Sticky Minecraft server".format(status.players.online))

    try:
        query = server.query()  # 'query' has to be enabled in a servers' server.properties file.
        bot.sendMessage(chat_id, "De volgende players zijn online {0}".format(", ".join(query.players.names)))
    except:
        if status.players.online > 0:
            bot.sendMessage(chat_id,
                            "Als Robin nou eens 'query' enabled in server.properties, dan zou je nu ook kunnen zien wie er online zijn")


def stickers(msg, add):
    """Mag ik een sticker?"""
    chat_id = msg['chat']['id']
    text = 'Sticker packs:'
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [dict(text='Sticky Stickers', url='https://telegram.me/addstickers/Sticky_stickers')],
        [dict(text='Meer Sticky Stickers', url='https://telegram.me/addstickers/SuperSticky')],
    ])
    bot.sendMessage(chat_id, text, reply_markup=reply_markup)


def command_parser(input):
    """static, parses commands"""
    add_input = None
    command_input = None
    if input[0] == '/':  # remove the '/'
        command_input = input[1:]
        if ' ' in command_input:  # separate the additive
            add_input = command_input[command_input.index(' ') + 1:500]
            command_input = command_input[:command_input.index(' ')]
        command_input = command_input.lower()  # make lowercase
        if '@' in command_input:  # check for recipient
            if command_input[command_input.index('@'):command_input.index('@') + len(BOTNAME)] == BOTNAME:  # remove the recipient
                command_input = command_input[:command_input.index('@')]
            else:  # ignore command
                command_input = None
                add_input = None
    return command_input, add_input


def date_to_string(event):
    """Pakt de datetime van een event en maakt er een mooie zin van"""
    if len(event.get('start_date')) == 25:
        start = datetime.datetime.strptime(event.get('start_date')[:-6], "%Y-%m-%dT%H:%M:%S")
    elif len(event.get('start_date')) == 10:
        start = datetime.datetime.strptime(event.get('start_date')[:10], "%Y-%m-%d")
    else:
        start = ''
    if start != '':
        start = utc.localize(start)
        start = start.strftime('%A %-d %B %H:%M uur')
        start = start[0].upper() + start[1:]
    return start


switch_case = {'start': start,
               'minecraft': minecraft,
               'mc': minecraft,
               'agenda': agenda,
               'activiteit': agenda,
               'activiteiten': agenda,
               'stickers': stickers,
               'bier': bier,
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
                                                caption='{0}\n{1}'.format(name, start))
                query = msg['query']
                if query.lower() in event.get('name').lower() or query is '':
                    inline_result.append(result)
        return inline_result

    answerer.answer(msg, compute)


if __name__ == '__main__':
    print('Listening...')
    bot = telepot.Bot(API_KEY)
    answerer = telepot.helper.Answerer(bot)
    bot.message_loop({'chat': chat,
                      'inline_query': inline_query,
                      })
    while 1:
        time.sleep(10)
