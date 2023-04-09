import hashlib


def generate_token(username, password):
    salt = '12345678'
    token = hashlib.sha256((username + password + salt).encode('utf-8')).hexdigest()
    return token

def hash_token(context):
    # Hash the password
    hashed_password = hashlib.sha256(context.encode()).hexdigest()
    return hashed_password