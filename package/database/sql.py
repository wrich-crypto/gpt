import mysql.connector
import logging


class MySQLDatabase:
    def __init__(self, host, port, user, password, database):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
        except mysql.connector.Error as error:
            logging.error(f"Failed to connect to MySQL: {error}")
            raise error

    def close(self):
        if self.connection is not None:
            self.connection.close()

    def add(self, table_name, data):
        try:
            columns = ', '.join(data.keys())
            values = ', '.join(['%s'] * len(data))
            query = f"INSERT INTO {table_name} ({columns}) VALUES ({values})"
            cursor = self.connection.cursor()
            cursor.execute(query, tuple(data.values()))
            self.connection.commit()
        except mysql.connector.Error as error:
            logging.error(f"Failed to add data to MySQL: {error}")
            raise error

    def delete(self, table_name, condition):
        try:
            query = f"DELETE FROM {table_name} WHERE {condition}"
            cursor = self.connection.cursor()
            cursor.execute(query)
            self.connection.commit()
        except mysql.connector.Error as error:
            logging.error(f"Failed to delete data from MySQL: {error}")
            raise error

    def query(self, query, params=None):
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()
        except mysql.connector.Error as error:
            logging.error(f"Failed to execute query on MySQL: {error}")
            raise error

    def authenticate_user(self, username, password):
        try:
            query = "SELECT * FROM users WHERE username=%s AND password=%s"
            params = (username, password)
            results = self.query(query, params)
            if len(results) > 0:
                return True
            else:
                return False
        except mysql.connector.Error as error:
            logging.error(f"Failed to authenticate user with MySQL: {error}")
            raise error