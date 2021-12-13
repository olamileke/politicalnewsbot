import os
import requests


def create_endpoint():
    return "http://newsapi.org/v2/top-headlines?country=ng&apiKey={0}".format(os.environ.get("NEWS_API_KEY"))


def call_endpoint():
    endpoint = create_endpoint()
    response = requests.get(endpoint)
    return response.json()['articles']
