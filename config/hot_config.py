import json
from itertools import cycle
from pathlib import Path

CONFIG_FILE = "config_hot.json"
class TokenManager:
    def __init__(self, storage_file=CONFIG_FILE):
        self.storage_file = storage_file
        self.tokens = []

        if Path(self.storage_file).exists():
            self._load_tokens()
        else:
            self._save_tokens()

        self.token_cycle = cycle(self.tokens)

    def _load_tokens(self):
        with open(self.storage_file, 'r') as f:
            self.tokens = json.load(f)

    def _save_tokens(self):
        with open(self.storage_file, 'w') as f:
            json.dump(self.tokens, f)

    def add_token(self, token):
        self.tokens.append(token)
        self.token_cycle = cycle(self.tokens)
        self._save_tokens()

    def remove_token(self, token):
        if token in self.tokens:
            self.tokens.remove(token)
            self.token_cycle = cycle(self.tokens)
            self._save_tokens()

    def get_next_api_key(self):
        return next(self.token_cycle)

hot_config = TokenManager()