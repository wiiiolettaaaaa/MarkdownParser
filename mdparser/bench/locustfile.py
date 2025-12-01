# bench/locustfile.py
from locust import HttpUser, task, between
import random
import os

SAMPLES_DIR = os.path.join(os.path.dirname(__file__), '..', 'samples')
FILES = [os.path.join(SAMPLES_DIR, f) for f in os.listdir(SAMPLES_DIR) if f.endswith('.md')]

class ParserUser(HttpUser):
    wait_time = between(0.1, 0.5)
    @task
    def parse_random(self):
        path = random.choice(FILES)
        with open(path, 'r', encoding='utf-8') as fh:
            txt = fh.read()
        # would call an HTTP endpoint if parser deployed as service
        # here we simulate local call
        from markdown_parser import Parser
        p = Parser(txt)
        doc = p.parse()
        # no HTTP - just parse and return