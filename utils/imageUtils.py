from io import BytesIO
import requests


def get_image_from_url(link):
    return BytesIO(requests.get(link).content)