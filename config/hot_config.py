import json
from itertools import cycle
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

CONFIG_FILE = "config_hot.json"


class ConfigHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback

    def on_modified(self, event):
        if event.src_path == CONFIG_FILE:
            self.callback()


class HotConfig:
    def __init__(self, config_file="config_hot.json"):
        global CONFIG_FILE
        CONFIG_FILE = config_file
        self.config = self.load_config()
        self.default_key = self.config['default_key']

        self.config_updated()

        event_handler = ConfigHandler(callback=self.config_updated)
        self.observer = Observer()
        self.observer.schedule(event_handler, path=".", recursive=False)
        self.observer.start()

    def config_updated(self):
        global api_key_cycle, ip_proxy_cycle, openai_api_key_cycle
        self.config = self.load_config()
        api_key_cycle = cycle(self.config["API_KEYS"])
        ip_proxy_cycle = cycle(self.config["IP_PROXIES"])
        openai_api_key_cycle = cycle(self.config['OPENAI_API_KEYS'])

    @staticmethod
    def load_config():
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return config

    def get_next_api_key(self):
        return next(api_key_cycle)

    def get_next_proxy(self):
        return next(ip_proxy_cycle)

    def get_next_openai_api_key(self):
        return next(openai_api_key_cycle)

    def stop(self):
        self.observer.stop()
        self.observer.join()

    def remove_api_key(self, api_key):
        if api_key in self.config["API_KEYS"]:
            self.config["API_KEYS"].remove(api_key)
            self.save_config()
            self.config_updated()

    def remove_openai_api_key(self, openai_api_key):
        if openai_api_key in self.config["OPENAI_API_KEYS"]:
            self.config["OPENAI_API_KEYS"].remove(openai_api_key)
            self.save_config()
            self.config_updated()

    def remove_proxy(self, proxy):
        if proxy in self.config["IP_PROXIES"]:
            self.config["IP_PROXIES"].remove(proxy)
            self.save_config()
            self.config_updated()

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

hot_config = HotConfig()