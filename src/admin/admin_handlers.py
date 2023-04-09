from .admin_routes import *
from .admin_module import *
from ..user.user_module import *

@admin_bp.route('/usercount', methods=['GET'])
def handle_admin_usercount():
    token = request.args.get('token')

    user = User.query(session, token=token)
    if not user:
        response_data = ErrorCode.error(-1, "Invalid token")
        return jsonify(response_data)

    count = User.count(session)
    response_data = ErrorCode.success({'count': count})

    return jsonify(response_data)

@admin_bp.route('/totalrevenue', methods=['GET'])
def handle_admin_totalrevenue():
    token = request.args.get('token')

    user = User.query(session, token=token)
    if not user:
        response_data = ErrorCode.error(-1, "Invalid token")
        return jsonify(response_data)

    total = 1000.0
    response_data = ErrorCode.success({'total': total})

    return jsonify(response_data)
