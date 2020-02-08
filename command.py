import logging
import datetime
import json
import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultPhoto


logger = logging.getLogger(__name__)


def start(update, context):
    """Welke opdrachten zijn er?"""
    text = "\n".join([f"/{value} - {key.__doc__}" for value, key in commands.items()])
    update.message.reply_text(text)


def agenda(update, context):
    """Wanneer is de volgende activiteit?"""
    req = requests.request('get', 'https://koala.svsticky.nl/api/activities/')
    if req.status_code == 200:
        api = json.loads(req.text)
    else:
        update.message.reply_text("Ik kan Koala niet bereiken :(")
        return

    n = 0
    event = api[n]
    while datetime.datetime.strptime(event.get('start_date')[:-6], "%Y-%m-%dT%H:%M:%S") < datetime.datetime.now():
        event = api[n + 1]

    name = event.get('name')
    location = event.get('location')
    participants = event.get('participant_counter') if event.get('participant_counter') else 0
    start = datetime.datetime.strftime(datetime.datetime.strptime(event.get('start_date')[:-6], "%Y-%m-%dT%H:%M:%S"),
                                       "%c")

    poster = event.get('poster')
    if not poster:
        update.message.reply_text(f'{name} ({participants})\n{start}\nLocatie: {location}')
    else:

        event_id = event.get('id')
        keyboard = [[InlineKeyboardButton("Meer info", callback_data=f"/activiteit {event_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        context.bot.send_photo(chat_id=update.message.chat_id, photo=poster)
        update.message.reply_text(name, reply_markup=reply_markup)


def bier(update, context):
    """Kan ik al bier kopen?"""
    nu = datetime.datetime.now()
    biertijd = nu.replace(hour=17, minute=0, second=0, microsecond=0)
    dag = nu.strftime('%A')
    if dag in ['zaterdag', 'zondag']:
        response = 'Het is weekend, je zult je bier ergens anders moeten halen'
    elif (nu - biertijd) > datetime.timedelta(hours=0):
        if nu.replace(second=0, microsecond=0) == biertijd:
            response = "TIJD VOOR BIER!"
        else:
            response = f"Het is {(nu - biertijd).seconds // 60} minuten over bier"
    else:
        response = f"Het is {((biertijd - nu).seconds // 60) + 1} minuten voor bier"
    update.message.reply_text(response)


def stickers(update, context):
    """Mag ik een sticker?"""
    reply_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Sticky stickers", url="https://telegram.me/addstickers/Sticky_stickers")],
        [InlineKeyboardButton(text="Meer Sticky stickers", url="https://telegram.me/addstickers/SuperSticky")]
    ])
    update.message.reply_text("Sticker packs:", reply_markup=reply_markup)


commands = {"start": start,
            "agenda": agenda,
            "bier": bier,
            "stickers": stickers}


def inlinequery(update, context):
    """Handle the inline query."""
    req = requests.request('get', 'https://koala.svsticky.nl/api/activities/')
    if req.status_code == 200:
        api = json.loads(req.text)
    else:
        logger.warning("Couldn't connect to Koala")
        return

    query = update.inline_query.query
    inline_results = []
    for i, event in enumerate(api):
        if event.get('poster') is not None:
            result = InlineQueryResultPhoto(
                id=i,
                title=event.get('name'),
                photo_url=event['poster'],
                thumb_url=event.get('thumbnail'),
                description=event.get('name'),
            )
            if query.lower() in event.get('name').lower() or query is '':
                inline_results.append(result)

    update.inline_query.answer(inline_results)