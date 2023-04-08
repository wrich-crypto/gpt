from .admin_routes import *
from init import *

@admin_bp.route('/usercount')
def handle_admin_usercount():

    response_data = ErrorCode.success()
    return jsonify(response_data)

@admin_bp.route('/userpay')
def handle_admin_userpay():

    response_data = ErrorCode.success()
    return jsonify(response_data)
