from .user_routes import *
from .user_module import *

@user_bp.route('/login', methods=['POST'])
def handle_user_login():
    print('login')
    username = request.form.get('username')
    password = request.form.get('password')
    hash_password = hash_token(password)

    user = User.query(session, username=username)

    print(user.password)
    print(hash_password)
    if str(user.password) != str(hash_password):
        response_data = ErrorCode.error(-1)
        return jsonify(response_data)

    # validate the username and password

    token = generate_token(username, password)
    response_data = ErrorCode.success({'token': token})

    return jsonify(response_data)

@user_bp.route('/register', methods=['POST'])
def handle_user_registration():
    username = request.form.get('username')
    email = request.form.get('email')
    verification_code = request.form.get('verification_code')
    phone = request.form.get('phone')
    password = request.form.get('password')
    hash_password = hash_token(password)

    print(f'email:{email},verification_code:{verification_code},password:{password},hash_password:{hash_password}')

    if User.exists(session, username=username) or User.exists(session, email=email) or User.exists(session, phone=phone):
        logger.info(f'account exist username:{username}, email:{email}, phone:{phone}')
        response_data = ErrorCode.error(-1)
        return jsonify(response_data)

    User.create(session, username=username, password=hash_password, email=email,
                phone=phone, invitation_code=verification_code)

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
