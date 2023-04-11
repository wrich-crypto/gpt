from .admin_routes import *
from .admin_module import *
from ..user.user_module import *

@admin_bp.route('/usercount', methods=['GET'])
def handle_admin_usercount():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

    token = auth_header[7:]

    user = User.query(session, token=token)
    if not user:
        return error_response(-1, "Invalid token")

    count = User.count(session)
    response_data = ErrorCode.success({'count': count})

    return jsonify(response_data)

@admin_bp.route('/totalrevenue', methods=['GET'])
def handle_admin_totalrevenue():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

    token = auth_header[7:]

    user = User.query(session, token=token)
    if not user:
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, "Invalid token")

    total_revenue, e = UserRecharge.total_pay_amount(session)

    if total_revenue is None:
        logger.error(f'handle_admin_totalrevenue UserBalance.sum error:{e}')
        total_revenue = 0

    response_data = ErrorCode.success({'total': total_revenue})

    return jsonify(response_data)

@admin_bp.route('/userbalance', methods=['GET'])
def handle_admin_userbalance():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

    token = auth_header[7:]
    user_id = request.args.get('user_id')

    user = User.query(session, token=token)
    if not user:
        return error_response(-1, "Invalid token")

    user_balance = UserBalance.query(session, user_id=user_id)
    remaining_balance = (user_balance.total_recharge - user_balance.consumed_amount) if user_balance else 0
    remaining_balance = remaining_balance if remaining_balance >= 0 else 0

    response_data = ErrorCode.success({'remaining_balance': remaining_balance})
    return jsonify(response_data)