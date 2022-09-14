import os

from django.conf import settings
from dotenv import load_dotenv


class Environment:

    @staticmethod
    def get(key=''):
        path = os.path.join(settings.BASE_DIR, '.env')
        load_dotenv(path)
        return os.getenv(key, None)
