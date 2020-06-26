from dynaconf import settings
from pymongo import MongoClient
from bot import melty_bot

melty_bot.load_extension("cogs.autorole")
melty_bot.load_extension("cogs.welcome")

print([cmd.name for cmd in melty_bot.commands])

melty_bot.run(settings.TOKEN)
