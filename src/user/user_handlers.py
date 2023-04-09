from .user_routes import *
from user_module import *

@user_bp.route('/login', methods=['POST'])
def handle_user_login():
    print('login')
    username = request.form.get('username')
    password = request.form.get('password')
    hash_password = hash(password)

    # validate the username and password

    token = generate_token(username, password)
    response_data = ErrorCode.success({'token': token})

    return jsonify(response_data)

@user_bp.route('/register', methods=['POST'])
def handle_user_registration():
    username = request.form.get('username')
    email = request.form.get('email')
    verification_code = request.form.get('verification_code')
    password = request.form.get('password')
    hash_password = hash(password)

    print(f'email:{email},verification_code:{verification_code},password:{password}')
    # validate the email and verification code
    # ...

    new_user = User(username=username, password=hash(password), email=email, phone="", invitation_code="")
    session.add(new_user)  # 添加新用户到 session
    session.commit()  # 提交更改

    token = generate_token(username, password)
    response_data = {'code': 0, 'msg': 'success'}
    return jsonify(response_data)


@user_bp.route('/logout')
def handle_user_logout():
    print('logout')

    response_data = ErrorCode.success()
    return jsonify(response_data)

@user_bp.route('/invite', methods=['POST'])
def handle_user_invite():
    token = request.form.get('token')
    email = request.form.get('email')
    print(f'token:{token}, email:{email}')

    # validate the token and email
    # ...

    response_data = ErrorCode.success()
    return jsonify(response_data)
