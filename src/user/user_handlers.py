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
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'token invalid')

    response_data = ErrorCode.success({'token': token})
    return jsonify(response_data)

@user_bp.route('/register', methods=['POST'])
def handle_user_registration():
    username = request.form.get('username')
    password = request.form.get('password')

    verification_type = request.form.get('verification_type')
    verification_code = request.form.get('verification_code')

    phone = request.form.get('phone')
    email = request.form.get('email')
    referral_code = request.form.get('referral_code')
    hash_password = hash_token(password)
    token = generate_token(username, hash_password)

    logger.info(f'register email:{email}, phone:{phone}, '
                f'verification_code:{verification_code},password:{password},hash_password:{hash_password}')

    if register_verification(verification_type, verification_code, email, phone) is False:
        logger.error(f'handle_user_registration register_verification '
                     f'verification_type:{verification_type} '
                     f'email:{email}, phone:{phone}'
                     f'verification_code:{verification_code} error')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'verification error')

    if username == '' or password == '':
        return error_response(error_code=ErrorCode.ERROR_INVALID_PARAMETER)

    if User.exists(session, username=username):
        logger.info(f'account exist username:{username}, email:{email}, phone:{phone}')
        return error_response(error_code=ErrorCode.ERROR_INVALID_PARAMETER, message='account exist')

    self_referral_code = generate_referral_code()
    instance, _ = User.create(session, username=username, password=hash_password, email=email,
                phone=phone, referral_code=self_referral_code, token=token)

    if instance is None:
        logger.info(f'account exist username:{username}, email:{email}, phone:{phone}')
        return error_response(-1, "Invalid token")

    referral_user = User.query(session, referral_code=referral_code)

    if referral_user is not None and referral_user.id > 0:
        generate_invication(referral_user.id, instance.id)

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
    referral_code = request.form.get('referral_code')
    print(f'token:{token}, referral_code:{referral_code}')

    user = User.query(session, token=token)
    referral_user = User.query(session, referral_code=referral_code)

    if UserInvitation.exists(session, invitee_id=user.id):
        logger.error(f'account referral already:{user.id}, referral_code:{referral_code}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'account referral already')

    if referral_user is not None and referral_user.id > 0:
        generate_invication(referral_user.id, user.id)

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
        return error_response(-1, "Invalid token")

    if user.password != hash_password:
        return error_response(-1, "Invalid password")

    hashed_new_password = hash_token(new_password)
    success, error_message = User.update(session, {"id": user.id}, {"password": hashed_new_password})
    if success:
        response_data = ErrorCode.success()
    else:
        return error_response(-1, error_message)

    return jsonify(response_data)

@user_bp.route('/get_phone_verification_code', methods=['POST'])
def handle_get_phone_verification_code():
    username = request.form.get('username')
    phone = request.form.get('phone')

    if validate_phone_number(phone) is False:
        logger.error(f'handle_get_phone_verification_code, '
                     f'validate_phone_number, username:{username}, phone:{phone} error')
        error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'phone error')

    code = generate_code()

    # third part service
    # ...

    instance, e = VerificationCode.upsert(session, {"phone": phone},
                                          {"username": username, "code_type": code_type_phone,
                                           "code": code, "phone": phone})
    if instance is None:
        logger.error(f'func handle_get_phone_verification_code, VerificationCode.create, username:{username} error: {e}')

    response_data = ErrorCode.success({'code': str(code)})
    return jsonify(response_data)

@user_bp.route('/get_email_verification_code', methods=['POST'])
def handle_get_email_verification_code():
    username = request.form.get('username')
    email = request.form.get('email')

    code = generate_code()
    if validate_email(email) is False:
        logger.error(f'handle_get_email_verification_code, '
                     f'validate_email, username:{username}, email:{email} error')
        error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'email error')

    # third part service
    # ...

    instance, e = VerificationCode.upsert(session, {"email": email},
                                          {"username": username, "code_type": code_type_email,
                                           "code": code, "email": email})
    if instance is None:
        logger.error(f'func handle_get_phone_verification_code, VerificationCode.create, username:{username} error: {e}')

    response_data = ErrorCode.success({'code': str(code)})
    return jsonify(response_data)

@user_bp.route('/get_user_invitations', methods=['GET'])
def handle_get_user_invitations():
    token = request.args.get('token')

    user = User.query(session, token=token)
    if not user:
        return error_response(-1, "Invalid token")

    print(user.id)
    invitations, _ = UserInvitation.query_all(session, inviter_id=user.id)

    invitation_data = []
    for invitation in invitations:
        invitee = User.query(session, id=invitation.invitee_id)
        invitation_data.append({
            "invitee_username": invitee.username,
            "reward": invitation.inviter_reward
        })

    response_data = ErrorCode.success({"invitations": invitation_data})
    return jsonify(response_data)

@user_bp.route('/get_remaining_tokens', methods=['GET'])
def handle_get_remaining_tokens():
    token = request.args.get('token')

    user = User.query(session, token=token)
    if not user:
        return error_response(-1, "Invalid token")

    user_balance = UserBalance.query(session, user_id=user.id)
    if not user_balance:
        response_data = ErrorCode.success({"remaining_tokens": 0})
        return jsonify(response_data)

    remaining_tokens = user_balance.total_recharge - user_balance.consumed_amount

    response_data = ErrorCode.success({"remaining_tokens": remaining_tokens})
    return jsonify(response_data)

@user_bp.route('/pay', methods=['POST'])
def handle_payment():
    token = request.form.get('token')
    amount = request.form.get('amount')

    user = User.query(session, token=token)
    if not user:
        return error_response(-1, "Invalid token")

    # 在此处实现支付功能，可能需要与支付服务集成
    # ...

    token_amount = amount * 10000
    instance, e = UserRecharge.create(session, user_id=user.id, amount=token_amount,
                                      recharge_method=recharge_method_pay, status=status_success)
    if instance is None:
        logger.error(f'UserRecharge.create inviter_id:{user.id} error:{e}')

    print('update_user_balance')
    update_user_balance(user.id, token_amount)

    response_data = ErrorCode.success()
    return jsonify(response_data)

