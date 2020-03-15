import requests
from config import api_key


def create_endpoint():
    return "http://newsapi.org/v2/top-headlines?country=ng&apiKey={0}".format(api_key)


def call_endpoint():
    endpoint = create_endpoint()
    response = requests.get(endpoint)
    return response.json()['articles']
