from .user_routes import *
from .user_module import *

@user_bp.route('/login', methods=['POST'])
def handle_user_login():
    username = request.form.get('username')
    password = request.form.get('password')
    hash_password = hash_token(password)
    token = generate_token(username, hash_password)
    logger.info(f'login username:{username}')

    user = User.query(session, username=username)

    # validate the username and password
    if str(user.token) != str(token):
        response_data = ErrorCode.error(-1)
        return jsonify(response_data)

    response_data = ErrorCode.success({'token': token})
    return jsonify(response_data)

@user_bp.route('/register', methods=['POST'])
def handle_user_registration():
    username = request.form.get('username')
    email = request.form.get('email')
    verification_code = request.form.get('verification_code')
    referral_code = request.form.get('referral_code')
    phone = request.form.get('phone')
    password = request.form.get('password')
    hash_password = hash_token(password)
    token = generate_token(username, hash_password)

    logger.info(f'register email:{email},verification_code:{verification_code},password:{password},hash_password:{hash_password}')

    if User.exists(session, username=username) or User.exists(session, email=email) or User.exists(session, phone=phone):
        logger.info(f'account exist username:{username}, email:{email}, phone:{phone}')
        response_data = ErrorCode.error(-1)
        return jsonify(response_data)

    self_referral_code = generate_referral_code()
    instance, _ = User.create(session, username=username, password=hash_password, email=email,
                phone=phone, referral_code=self_referral_code, token=token)

    if instance is None:
        logger.info(f'account exist username:{username}, email:{email}, phone:{phone}')
        response_data = ErrorCode.error(-1)
        return jsonify(response_data)

    referral_user = User.query(session, referral_code=referral_code)

    if referral_user is not None and referral_user.id > 0:
        inviter_id = referral_user.id
        invitee_id = instance.id
        UserInvitation.create(session, inviter_id=inviter_id, invitee_id=invitee_id)

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
    referral_code = request.form.get('referral code')
    print(f'token:{token}, email:{referral_code}')

    user = User.query(session, token=token)
    referral_user = User.query(session, referral_code=referral_code)

    if referral_user is not None and referral_user.id > 0:
        inviter_id = referral_user.id
        invitee_id = user.id
        UserInvitation.create(session, inviter_id=inviter_id, invitee_id=invitee_id)

    response_data = ErrorCode.success()
    return jsonify(response_data)
