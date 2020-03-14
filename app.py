from telegram import ParseMode
from telegram.ext import Updater, CommandHandler
from middlewares import subscribed_middleware
from endpoints import call_endpoint
import config
import json
import os.path as path
import logging
import time


# Enable logging of errors
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)


# Initializing relevant variables
updater = Updater(token=config.bot_token, use_context=True)
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

    next_alert_time = get_next_alert_information()
    minutes = next_alert_time['minutes']
    seconds = next_alert_time['seconds']
    text = 'Subscribed successfully. My next alert is in {0} minutes and {1} seconds.\nType /unsubscribe to stop getting my alerts'.format(
        minutes, seconds)

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


def get_next_alert_information():
    current_time = time.localtime()
    minutes = time.strftime('%M', current_time)
    seconds = time.strftime('%S', current_time)

    if seconds == 0:
        rem_minutes = 60 - int(minutes)
        rem_seconds = seconds
    else:
        rem_minutes = 60 - (int(minutes) + 1)
        rem_seconds = 60 - int(seconds)

    return {'minutes': rem_minutes, 'seconds': rem_seconds}


# Job Functions
def alert(context):
    with open(path.join(config.base_directory, 'alerts.json')) as reader:
        data = json.load(reader)

    with open(path.join(config.base_directory, 'subscribers.json')) as reader:
        subscribers = json.load(reader)

    if len(data['articles']) == 0:
        data['articles'] = call_endpoint()
        with open(path.join(config.base_directory, 'alerts.json'), 'w') as writer:
            json.dump(data, writer)

    print(len(data['articles']))
    for chat_id in subscribers['subscribers']:
        send_article(context, chat_id, data['articles'][11])


def send_article(context, chat_id, article):
    url = article['url']
    source_text = "<a href='{0}'>Read more</a>".format(url)
    context.bot.send_message(chat_id=chat_id, text=article['title'])
    context.bot.send_message(chat_id=chat_id, text=article['content'])
    context.bot.send_message(
        chat_id=chat_id, text=source_text, parse_mode=ParseMode.HTML)


job.run_once(alert, 2)

# Creating the Handlers
start_handler = CommandHandler('start', start)
subscribe_handler = CommandHandler('subscribe', subscribe)
unsubscribe_handler = CommandHandler('unsubscribe', unsubscribe)


# Adding the handlers to the dispatcher
dispatcher.add_handler(start_handler)
dispatcher.add_handler(subscribe_handler)
dispatcher.add_handler(unsubscribe_handler)


# Running the bot
updater.start_polling()
updater.idle()
