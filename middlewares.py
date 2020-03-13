import functools, json
import os.path as path
import config

def subscribed_middleware(handler_function):
	functools.wraps(handler_function)
	def middleware(update, context):
		chat_id = str(update.effective_chat.id)
		with open(path.join(config.base_directory, 'subscribers.json')) as reader:
			data = json.load(reader)

		if chat_id not in data['subscribers']:
			return context.bot.send_message(chat_id=chat_id, text='You are not subscribed!')

		return handler_function(update, context)

	return middleware
