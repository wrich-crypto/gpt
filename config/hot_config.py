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
        self.config_updated()

        event_handler = ConfigHandler(callback=self.config_updated)
        self.observer = Observer()
        self.observer.schedule(event_handler, path=".", recursive=False)
        self.observer.start()

    def config_updated(self):
        global api_key_cycle, ip_proxy_cycle
        self.config = self.load_config()
        api_key_cycle = cycle(self.config["API_KEYS"])
        ip_proxy_cycle = cycle(self.config["IP_PROXIES"])

    @staticmethod
    def load_config():
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        return config

    def get_next_api_key(self):
        return next(api_key_cycle)

    def get_next_proxy(self):
        return next(ip_proxy_cycle)

    def stop(self):
        self.observer.stop()
        self.observer.join()
