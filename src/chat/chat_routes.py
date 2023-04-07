from flask import Blueprint, request

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')