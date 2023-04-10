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
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, "Invalid token")

    total_revenue = UserBalance.sum(session, column='pay_amount')
    response_data = ErrorCode.success({'total': total_revenue})

    return jsonify(response_data)

@admin_bp.route('/userbalance', methods=['GET'])
def handle_admin_userbalance():
    token = request.args.get('token')
    user_id = request.args.get('user_id')

    user = User.query(session, token=token)
    if not user:
        response_data = ErrorCode.error(-1, "Invalid token")
        return jsonify(response_data)

    user_balance = UserBalance.query(session, user_id=user_id)
    remaining_balance = (user_balance.total_recharge - user_balance.consumed_amount) if user_balance else 0
    remaining_balance = remaining_balance if remaining_balance >= 0 else 0

    response_data = ErrorCode.success({'remaining_balance': remaining_balance})
    return jsonify(response_data)