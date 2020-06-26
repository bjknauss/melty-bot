from dynaconf import settings
from pymongo import MongoClient

client = MongoClient(settings.DB_URI)

db = client[settings.DB_NAME]