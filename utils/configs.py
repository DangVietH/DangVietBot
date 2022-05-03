import os

config_var = {
    "token": os.environ.get("token"),
    "mongo_pass": os.environ.get("mongo_pass"),
    "reddit_pass": os.environ.get("reddit_pass"),
    "reddit_secret": os.environ.get("reddit_secret"),
    "reddit_id": os.environ.get("reddit_id"),
    "statcord": os.environ.get("statcord")
}