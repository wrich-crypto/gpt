import json

class Config:
    def __init__(self, filepath):
        if filepath == '':
            return

        with open(filepath) as f:
            config = json.load(f)

        self.server = config['server']
        self.port = config['port']
        self.db_server = config['database']['server']
        self.db_port = config['database']['port']
        self.db_username = config['database']['username']
        self.db_password = config['database']['password']
        self.db_name = config['database']['name']