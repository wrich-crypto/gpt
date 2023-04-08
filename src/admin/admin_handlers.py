from .admin_routes import *
from init import *

@admin_bp.route('/usercount', methods=['GET'])
def handle_admin_usercount():
    token = request.args.get('token')

    # validate the token
    # ...

    count = 1000
    response_data = ErrorCode.success({'count': count})

    return jsonify(response_data)

@admin_bp.route('/totalrevenue', methods=['GET'])
def handle_admin_totalrevenue():
    token = request.args.get('token')

    # validate the token
    # ...

    total = 1000.0
    response_data = ErrorCode.success({'total': total})

    return jsonify(response_data)
