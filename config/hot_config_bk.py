import json
from itertools import cycle

CONFIG_FILE = "config_hot.json"
class TokenManager:
    def __init__(self, storage_file=CONFIG_FILE):
        self.storage_file = storage_file
        self.tokens = []
        self.config_updated()

    @staticmethod
    def load_config():
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return config

    def remove_api_key(self, api_key):
        if api_key in self.config["API_KEYS"]:
            self.config["API_KEYS"].remove(api_key)
            self.save_config()
            self.config_updated()


    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

    def config_updated(self):
        self.config = self.load_config()
        self.token_cycle = cycle(self.config["API_KEYS"])
        self.ip_proxy_cycle = cycle(self.config["IP_PROXIES"])

    def get_next_api_key(self):
        return next(self.token_cycle)

hot_config = TokenManager()