from flask import Blueprint, request

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')