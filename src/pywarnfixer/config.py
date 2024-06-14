import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_ACCESS_TOKEN = os.getenv('GITHUB_ACCESS_TOKEN')
ORGANIZATION = os.getenv('ORGANIZATION')
ENGAGEMENTS = ["stars", "forks"]
STRATA_RANGES = [(11, 100), (101, 1000), (1001, 10000), (10001, 100000), (100001, 1000000)]
PYLINT_MESSAGE_TYPES = ["F", "E", "W", "C", "R", "I", "ALL"]

MAX_PROJECTS_PER_STRATUM = 25
MAX_WARNINGS_PER_GRAPH = 15

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
ANTHROPIC_API_URL = "https://api-inference.huggingface.co/models/openai-community/gpt2"
