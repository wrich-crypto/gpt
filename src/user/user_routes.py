from flask import Blueprint, request, url_forhandle_user_invite

user_bp = Blueprint('user', __name__, url_prefix='/user')