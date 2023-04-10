import re

def validate_email(email):
    pattern = re.compile(r'^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$')
    return True if pattern.match(email) else False

def validate_phone_number(phone_number):
    pattern = re.compile(r'^1[3-9]\d{9}$')
    return True if pattern.match(phone_number) else False