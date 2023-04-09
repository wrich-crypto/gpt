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
        response_data = ErrorCode.error(error_code=ErrorCode.ERROR_INVALID_PARAMETER, message='account exist')
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

@user_bp.route('/change_password', methods=['POST'])
def handle_change_password():
    token = request.form.get('token')
    password = request.form.get('password')
    hash_password = hash_token(password)
    new_password = request.form.get('new_password')

    user = User.query(session, token=token)
    if not user:
        response_data = ErrorCode.error(-1, "Invalid token")
        return jsonify(response_data)

    if user.password != hash_password:
        response_data = ErrorCode.error(-1, "Invalid password")
        return jsonify(response_data)

    hashed_new_password = hash_token(new_password)
    success, error_message = User.update(session, {"id": user.id}, {"password": hashed_new_password})
    if success:
        response_data = ErrorCode.success()
    else:
        response_data = ErrorCode.error(-1, error_message)

    return jsonify(response_data)

@user_bp.route('/get_phone_verification_code', methods=['POST'])
def handle_get_phone_verification_code():
    phone = request.form.get('phone')

    # third part service
    # ...

    response_data = ErrorCode.success({'code': '111111'})
    return jsonify(response_data)

@user_bp.route('/get_email_verification_code', methods=['POST'])
def handle_get_email_verification_code():
    email = request.form.get('email')

    # third part service
    # ...

    response_data = ErrorCode.success({'code': '111111'})
    return jsonify(response_data)

@user_bp.route('/get_user_invitations', methods=['GET'])
def handle_get_user_invitations():
    token = request.args.get('token')

    user = User.query(session, token=token)
    if not user:
        response_data = ErrorCode.error(-1, "Invalid token")
        return jsonify(response_data)

    # 查询用户邀请列表
    invitations = UserInvitation.query_all(session, inviter_id=user.id)

    # 获取邀请人和奖励信息（根据实际情况修改）
    invitation_data = []
    for invitation in invitations:
        invitee = User.query(session, id=invitation.invitee_id)
        reward = 0  # 计算奖励
        invitation_data.append({
            "invitee_username": invitee.username,
            "reward": reward
        })

    response_data = ErrorCode.success({"invitations": invitation_data})
    return jsonify(response_data)

@user_bp.route('/bind_invitation_reward', methods=['POST'])
def handle_bind_invitation_reward():
    token = request.form.get('token')
    invitee_id = request.form.get('invitee_id')

    user = User.query(session, token=token)
    if not user:
        response_data = ErrorCode.error(-1, "Invalid token")
        return jsonify(response_data)

    # 在此处实现邀请奖励的绑定关系，可能需要更新用户奖励数据等
    # ...

    response_data = ErrorCode.success()
    return jsonify(response_data)

@user_bp.route('/get_remaining_tokens', methods=['GET'])
def handle_get_remaining_tokens():
    token = request.args.get('token')

    user = User.query(session, token=token)
    if not user:
        response_data = ErrorCode.error(-1, "Invalid token")
        return jsonify(response_data)

    user_balance = UserBalance.query(session, user_id=user.id)
    remaining_tokens = user_balance.remaining_balance

    response_data = ErrorCode.success({"remaining_tokens": remaining_tokens})
    return jsonify(response_data)

@user_bp.route('/pay', methods=['POST'])
def handle_payment():
    token = request.form.get('token')
    amount = request.form.get('amount')

    user = User.query(session, token=token)
    if not user:
        response_data = ErrorCode.error(-1, "Invalid token")
        return jsonify(response_data)

    # 在此处实现支付功能，可能需要与支付服务集成
    # ...

    response_data = ErrorCode.success()
    return jsonify(response_data)

