from .user_routes import *
from init import *

@user_bp.route('/login', methods=['POST'])
def handle_user_login():
    username = request.form['username']
    password = request.form['password']
    # 验证用户名和密码
    # ...
    return f'User login successful!\nusername:{username}\npassword:{password}'

@user_bp.route('/logout')
def handle_user_logout():
    # 处理注销操作
    # ...
    print('logout')
    return 'User logged out!'