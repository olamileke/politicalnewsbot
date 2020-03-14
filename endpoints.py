import requests
from config import api_key
from datetime import date


def create_endpoint():
    today = date.today().strftime("%Y-%m-%d")
    return "http://newsapi.org/v2/top-headlines?country=ng&apiKey={0}".format(api_key)


def call_endpoint():
    endpoint = create_endpoint()
    response = requests.get(endpoint)
    return response.json()['articles']
