import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
BRIXHUB_API_KEY = os.getenv("BRIXHUB_API_KEY")
BRIXHUB_API_URL = os.getenv("BRIXHUB_API_URL", "https://api.brixhub.com/v1/search")
PANEL_SECRET = os.getenv("PANEL_SECRET", "changeme123")
FREE_SEARCHES_PER_DAY = 3
