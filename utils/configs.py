import os

config_var = {
    "token": os.environ.get("token"),
    "mongo_pass": os.environ.get("mongo_pass"),
    "statcord": os.environ.get("statcord"),
    "weather": os.environ.get("weather")
}