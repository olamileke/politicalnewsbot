from telegram import ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from os import path, environ
from middlewares import subscribed_middleware
from endpoints import call_endpoint
import config
import json
import logging
import time


# Enable logging of errors
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Setting the relevant environment variables
config.set()

# Initializing relevant variables
token = os.environ.get("BOT_TOKEN")
updater = Updater(token=token, use_context=True)
dispatcher = updater.dispatcher
job = updater.job_queue


# Handler functions
def start(update, context):
    with open(path.join(config.base_directory, 'start_message.txt')) as reader:
        text = reader.read()

    context.bot.send_message(chat_id=update.effective_chat.id, text=text)


def subscribe(update, context):
    chat_id = str(update.effective_chat.id)
    with open(path.join(config.base_directory, 'subscribers.json')) as reader:
        data = json.load(reader)

    if chat_id in data['subscribers']:
        return context.bot.send_message(
            chat_id=chat_id, text='You are already subscribed!')

    data['subscribers'].append(chat_id)

    with open(path.join(config.base_directory, 'subscribers.json'), 'w') as writer:
        json.dump(data, writer)

    next_alert_time = get_next_alert_time()
    minutes = next_alert_time['minutes']
    seconds = next_alert_time['seconds']
    hours = next_alert_time.get('hours')

    if hours is None:
        text = 'Subscribed successfully. My next alert is in {0} minutes and {1} seconds.\nType /unsubscribe to stop getting my alerts'.format(
        minutes, seconds)
    else:
        text = 'Subscribed successfully. My next alert is in {0} hours {1} minutes and {2} seconds.\nType /unsubscribe to stop getting my alerts'.format(
        hours, minutes, seconds)

    context.bot.send_message(chat_id=chat_id, text=text)


@subscribed_middleware
def unsubscribe(update, context):
    chat_id = str(update.effective_chat.id)
    with open(path.join(config.base_directory, 'subscribers.json')) as reader:
        data = json.load(reader)

    data['subscribers'].remove(chat_id)

    with open(path.join(config.base_directory, 'subscribers.json'), 'w') as writer:
        json.dump(data, writer)

    context.bot.send_message(
        chat_id=chat_id, text='Unsubscribed successfully!')


def get_next_alert_time():
    current_time = time.localtime()
    hours = int(time.strftime('%H'))
    minutes = time.strftime('%M', current_time)
    seconds = time.strftime('%S', current_time)
    has_hours = False

    if hours > 20 or hours < 5:
        if hours > 20:
            hours = 30 - (hours + 1)
        else:
            hours = 6 - (hours + 1)

        has_hours = True


    if seconds == 0:
        rem_minutes = 60 - int(minutes)
        rem_seconds = seconds
    else:
        rem_minutes = 60 - (int(minutes) + 1)
        rem_seconds = 60 - int(seconds)

    if has_hours:
        return {'hours':hours, 'minutes': rem_minutes, 'seconds': rem_seconds}

    return {'minutes': rem_minutes, 'seconds': rem_seconds}


def unknown(update, context):
    context.bot.send_message(
        chat_id=update.effective_chat.id, text="I'm sorry. I do not understand that.")


# Job Functions
def alert(context):
    current_hour = int(time.strftime('%H'))

    if current_hour > 5 and current_hour < 22:
        with open(path.join(config.base_directory, 'alerts.json')) as reader:
            data = json.load(reader)

        with open(path.join(config.base_directory, 'subscribers.json')) as reader:
            subscribers = json.load(reader)

        if len(data['articles']) == 0:
            data['articles'] = call_endpoint()
            with open(path.join(config.base_directory, 'alerts.json'), 'w') as writer:
                json.dump(data, writer)

        for chat_id in subscribers['subscribers']:
            send_article(context, chat_id, data['articles'][current_hour - 6])

        if current_hour == 21:
            data['articles'] = []
            with open(path.join(config.base_directory, 'alerts.json'), 'w') as writer:
                json.dump(data, writer)


def send_article(context, chat_id, article):
    url = article['url']
    source_text = "<a href='{0}'>Read more</a>".format(url)
    context.bot.send_message(chat_id=chat_id, text=article['title'])
    if article['content'] is not None:
        context.bot.send_message(chat_id=chat_id, text=article['content'])
    context.bot.send_message(
        chat_id=chat_id, text=source_text, parse_mode=ParseMode.HTML)


def seconds_from_start():
    current_time = time.localtime()
    mins_till_next_hour = 60 - (int(time.strftime('%M', current_time)) + 1)
    secs_till_next_hour = (mins_till_next_hour * 60) + (60 - int(time.strftime('%S', current_time)))
    return secs_till_next_hour


# Job to alert subscribers with news
job.run_repeating(alert, interval=3600, first=seconds_from_start())


# Creating the Handlers
start_handler = CommandHandler('start', start)
subscribe_handler = CommandHandler('subscribe', subscribe)
unsubscribe_handler = CommandHandler('unsubscribe', unsubscribe)
unknown_handler = MessageHandler(Filters.all, unknown)

# Adding the handlers to the dispatcher
dispatcher.add_handler(start_handler)
dispatcher.add_handler(subscribe_handler)
dispatcher.add_handler(unsubscribe_handler)
dispatcher.add_handler(unknown_handler)


# Starting the bot
updater.start_webhook(listen=os.environ.get("BOT_HOST"), port=os.environ.get("BOT_PORT"), url_path=token)
updater.bot.set_webhook(url="{0}{1}".format(os.environ.get("BOT_URL"), token))

updater.idle()
