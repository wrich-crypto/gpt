from .admin_routes import *

@admin_bp.route('/usercount')
def handle_admin_usercount():
    # 处理用户统计操作
    # ...
    return 'User count: 100'

@admin_bp.route('/userpay')
def handle_admin_userpay():
    # 处理用户支付操作
    # ...
    return 'User pay successful!'
