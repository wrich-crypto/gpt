from .user_routes import *
from .user_module import *
from ..chat.chat_module import ChatMessage

@user_bp.route('/login', methods=['POST'])
def handle_user_login():
    session = g.session
    username = g.data.get('username')
    password = g.data.get('password')
    hash_password = hash_token(password)
    token = generate_token(username, hash_password)
    logger.info(f'login username:{username}')

    if username is None or username == '' or password is None or password == '':
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'invalid parameter')

    user = User.query(session, username=username)

    if user is None:
        logger.error(f'handle_user_login User.query, username:{username} account no exist')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'account no exist')

    # validate the username and password
    if str(user.token) != str(token):
        logger.error(f'handle_user_login User.query, username:{username} password error, token invalid')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'password error')

    response_data = ErrorCode.success({'token': token})
    return jsonify(response_data)

@user_bp.route('/register', methods=['POST'])
def handle_user_registration():
    session = g.session
    username = g.data.get('username')
    password = g.data.get('password')

    verification_type = g.data.get('verification_type')
    verification_code = g.data.get('verification_code')

    phone = g.data.get('phone')
    email = g.data.get('email')
    referral_code = g.data.get('referral_code')
    hash_password = hash_token(password)
    token = generate_token(username, hash_password)

    logger.info(f'register email:{email}, phone:{phone}, '
                f'verification_code:{verification_code},password:{password},hash_password:{hash_password}')

    if username is None or username == '' or password is None or password == '':
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'invalid parameter')

    success, err = register_verification(session, verification_type, verification_code, email, phone)
    if success is False:
        logger.error(f'handle_user_registration register_verification '
                     f'verification_type:{verification_type} '
                     f'email:{email}, phone:{phone}'
                     f'verification_code:{verification_code} error,'
                     f'error: {err}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, err)

    if username == '' or password == '':
        logger.error(f'handle_user_registration register_verification '
                     f'verification_type:{verification_type} '
                     f'email:{email}, phone:{phone}'
                     f'verification_code:{verification_code} error')
        return error_response(error_code=ErrorCode.ERROR_INVALID_PARAMETER)

    if User.exists(session, username=username):
        logger.error(f'account exist username:{username}, email:{email}, phone:{phone}')
        return error_response(error_code=ErrorCode.ERROR_INVALID_PARAMETER, message='account exist')

    bind_phone = status_success
    if phone is None or phone == '':
        bind_phone = status_failed

    self_referral_code = generate_referral_code()
    source = request.host
    referral_code = init_referral_code(session, source) if referral_code is None or referral_code == "" else referral_code
    referral_user = User.query(session, referral_code=referral_code)

    if referral_user.is_role_present(user_role_agent):
        invitation_user_id = referral_user.id
        invitation_user_name = referral_user.username
    else:
        invitation_user_id = referral_user.invitation_user_id
        invitation_user_name = referral_user.invitation_user_name

    instance, e = User.create(session, username=username, password=hash_password, email=email,
                phone=phone, referral_code=self_referral_code, token=token, bind_phone=bind_phone,
                source=source, invitation_code=referral_code, invitation_user_id=invitation_user_id,
                invitation_user_name=invitation_user_name)

    if instance is None:
        logger.error(f'account exist username:{username}, email:{email}, phone:{phone}, error:{e}')
        return error_response(ErrorCode.ERROR_INTERNAL_SERVER, "server error")

    if referral_user is not None and referral_user.id > 0:
        generate_invication(session, referral_user.id, instance.id)

    token_amount = DevConfig.get_free_token_count(session)
    user_id = instance.id
    instance, e = UserRecharge.create(session, user_id=user_id, amount=token_amount, pay_amount=0,
                                      recharge_method=recharge_method_register, status=status_success)
    if instance is None:
        logger.error(f'UserRecharge.create inviter_id:{user_id} error:{e}')

    update_user_balance(session, user_id, token_amount)

    response_data = {'code': 0, 'msg': 'success'}
    return jsonify(response_data)

@user_bp.route('/logout')
def handle_user_logout():
    session = g.session
    logger.info('logout')

    response_data = ErrorCode.success()
    return jsonify(response_data)

@user_bp.route('/invite', methods=['POST'])
def handle_user_invite():
    session = g.session
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.error(f'Invalid token, auth_header:{auth_header}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

    token = auth_header[7:]

    referral_code = g.data.get('referral_code')
    logger.info(f'token:{token}, referral_code:{referral_code}')

    if referral_code is None or referral_code == '':
        logger.error(f'referral_code:{referral_code}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'referral code empty')

    user = User.query(session, token=token)

    if not user:
        logger.error(f'Invalid token, auth_header:{auth_header}')
        return error_response(ErrorCode.ERROR_TOKEN, "Invalid token")

    referral_user = User.query(session, referral_code=referral_code)

    if UserInvitation.exists(session, invitee_id=user.id):
        logger.error(f'account referral already:{user.id}, referral_code:{referral_code}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'account referral already')

    if referral_user is not None and referral_user.id > 0:
        generate_invication(session, referral_user.id, user.id)

    response_data = ErrorCode.success()
    return jsonify(response_data)

@user_bp.route('/change_password', methods=['POST'])
def handle_change_password():
    session = g.session
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.error(f'Invalid token, auth_header:{auth_header}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

    token = auth_header[7:]

    password = g.data.get('password')
    hash_password = hash_token(password)
    new_password = g.data.get('new_password')

    if password is None or password == '' or new_password is None or new_password == '':
        logger.error(f'user not exist, token:{token}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, "Invalid parameter")

    user = User.query(session, token=token)
    if not user:
        logger.error(f'user not exist, token:{token}')
        return error_response(ErrorCode.ERROR_TOKEN, "Invalid token")

    if user.password != hash_password:
        logger.error(f'password error, token:{token}, password:{password}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, "Invalid password")

    hashed_new_password = hash_token(new_password)
    new_token = generate_token(user.username, hashed_new_password)

    success, error_message = User.update(session, {"id": user.id}, {"password": hashed_new_password, "token": new_token})
    if success:
        response_data = ErrorCode.success()
    else:
        logger.error(f'user not exist, token:{token}')
        return error_response(ErrorCode.ERROR_INTERNAL_SERVER, error_message)

    return jsonify(response_data)

@user_bp.route('/get_phone_verification_code', methods=['POST'])
def handle_get_phone_verification_code():
    session = g.session
    username = g.data.get('username')
    phone = g.data.get('phone')

    if phone is None or phone == '':
        logger.error(f'handle_get_phone_verification_code, '
                     f'sms_client.send_message, username:{username}, phone:{phone}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'phone error')

    if validate_phone_number(phone) is False:
        logger.error(f'handle_get_phone_verification_code, '
                     f'validate_phone_number, username:{username}, phone:{phone} error')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'phone error')

    code = generate_code()

    sign_name = main_config.sign_name
    template_code = main_config.template_code
    template_param = '{"code":"' + str(code) + '"}'
    err = sms_client.send_message(phone, sign_name, template_code, template_param)

    if err is not None:
        logger.error(f'handle_get_phone_verification_code, '
                     f'sms_client.send_message, username:{username}, phone:{phone} error:{err}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'phone error')

    instance, e = VerificationCode.upsert(session, {"phone": phone},
                                          {"username": username, "code_type": code_type_phone,
                                           "code": code, "phone": phone})
    if instance is None:
        logger.error(f'func handle_get_phone_verification_code, VerificationCode.create, username:{username} error: {e}')
        return error_response(ErrorCode.ERROR_INTERNAL_SERVER, 'server error')

    response_data = ErrorCode.success()
    return jsonify(response_data)

@user_bp.route('/get_email_verification_code', methods=['POST'])
def handle_get_email_verification_code():
    session = g.session
    username = g.data.get('username')
    email = g.data.get('email')

    if email is None or email == '':
        logger.error(f'handle_get_phone_verification_code, '
                     f'sms_client.send_message, username:{username}, email:{email}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'email error')

    code = generate_code()
    if validate_email(email) is False:
        logger.error(f'handle_get_email_verification_code, '
                     f'validate_email, username:{username}, email:{email} error')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'email error')

    single_send_mail_request = dm_20151123_models.SingleSendMailRequest()
    single_send_mail_request.account_name = 'services@aigcchina.ai'
    single_send_mail_request.to_address = email
    single_send_mail_request.subject = "验证码信息"
    single_send_mail_request.html_body = f'<p>验证码为"{str(code)}".</p>'
    single_send_mail_request.from_alias = "gpt"
    single_send_mail_request.address_type = 1
    single_send_mail_request.reply_to_address = False
    err = email_client.send_email(single_send_mail_request)

    if err is not None:
        logger.error(f'handle_get_email_verification_code, email_client.send_email, email:{email} error:{err}')

    instance, err = VerificationCode.upsert(session, {"email": email},
                                          {"username": username, "code_type": code_type_email,
                                           "code": code, "email": email})

    if err is not None:
        logger.error(f'handle_get_email_verification_code, VerificationCode.upsert, email:{email} error:{err}')

    logger.info(f'code:{code}')
    if instance is None:
        logger.error(f'func handle_get_phone_verification_code, VerificationCode.create, username:{username} error: {err}')

    response_data = ErrorCode.success()
    return jsonify(response_data)

@user_bp.route('/get_user_invitations', methods=['GET'])
def handle_get_user_invitations():
    session = g.session
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.error(f'Invalid token, auth_header:{auth_header}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

    token = auth_header[7:]

    page = request.args.get('page')
    page_size = request.args.get('pageSize')

    if page is None or int(page) <= 0:
        page = 1

    if page_size is None or int(page_size) <= 0:
        page_size = 50

    user = User.query(session, token=token)
    if not user:
        logger.error(f'Invalid token, auth_header:{auth_header}')
        return error_response(ErrorCode.ERROR_TOKEN, "Invalid token")

    offset = (int(page) - 1) * int(page_size)
    invitations, _ = UserInvitation.query_all(session, limit=int(page_size), offset=offset, inviter_id=user.id)

    invitation_data = []
    for invitation in invitations:
        invitee = User.query(session, id=invitation.invitee_id)
        invitation_data.append({
            "invitee_username": invitee.username,
            "reward": invitation.inviter_reward
        })

    total_num = UserInvitation.count(session, inviter_id=user.id)


    response_data = ErrorCode.success({"referral_code": user.referral_code, "invitations": invitation_data,
                                       "total": total_num})
    return jsonify(response_data)

@user_bp.route('/get_remaining_tokens', methods=['GET'])
def handle_get_remaining_tokens():
    session = g.session
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.error(f'Invalid token, auth_header:{auth_header}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

    token = auth_header[7:]

    user = User.query(session, token=token)
    if not user:
        logger.error(f'Invalid token, auth_header:{auth_header}')
        return error_response(ErrorCode.ERROR_TOKEN, "Invalid token")

    user_balance = UserBalance.query(session, user_id=user.id)
    if not user_balance:
        response_data = ErrorCode.success({"remaining_tokens": 0})
        return jsonify(response_data)

    remaining_tokens = user_balance.total_recharge - user_balance.consumed_amount

    response_data = ErrorCode.success({"remaining_tokens": remaining_tokens})
    return jsonify(response_data)

@user_bp.route('/pay', methods=['POST'])
def handle_payment():
    session = g.session
    logger.info('update_user_balance')
    amount = int(g.data.get('amount'))
    open_id = g.data.get('open_id')
    order_type = int(g.data.get('order_type'))

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.error(f'Invalid auth_header, amount:{auth_header}')
        return error_response(ErrorCode.ERROR_TOKEN, 'Invalid auth_header')

    token = auth_header[7:]

    if amount is None or amount == '' or int(amount) < 5000:
        logger.error(f'Invalid amount, amount:{amount}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid amount')


    user = User.query(session, token=token)
    if not user:
        logger.error(f'Invalid token, auth_header:{auth_header}')
        return error_response(ErrorCode.ERROR_TOKEN, "Invalid token")

    response_data = request_pay_by_type(session, order_type, amount, user.id, open_id)
    return jsonify(response_data)

@user_bp.route('/order_status', methods=['GET'])
def get_order_status():
    session = g.session
    logger.info('get_order_status')

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.error(f'Invalid token, auth_header:{auth_header}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

    token = auth_header[7:]

    user = User.query(session, token=token)
    if not user:
        logger.error(f'Invalid token, auth_header:{auth_header}')
        return error_response(ErrorCode.ERROR_TOKEN, "Invalid token")

    userBalance = UserBalance.query(session, user_id=user.id)

    if userBalance is None:
        return False

    # Extract the trade_no from the request
    trade_no = request.args.get('trade_no')
    if not trade_no:
        logger.error(f'No trade_no provided')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'No trade_no provided')

    # Fetch the order by trade_no
    order = Order.query(session, trade_no=trade_no)
    if not order:
        logger.error(f'No order found with trade_no:{trade_no}')
        return error_response(ErrorCode.ERROR_INTERNAL_SERVER, "No order found with this trade_no")

    # Return order status
    response_data_dict = {
        'trade_no': order.trade_no,
        'status': order.status,
        'amount': str(order.amount),
        "balance": userBalance.total_recharge - userBalance.consumed_amount,
    }

    response_data = ErrorCode.success(response_data_dict)
    return jsonify(response_data)

@user_bp.route('/pay/notify', methods=['POST'])
def handle_payment_notify():
    session = g.session
    logger.info('handle_payment notify')

    #获取订单号
    #获取user_id
    out_trade_no = g.data.get('out_trade_no')
    amount = g.data.get('amount')

    order_instance = Order.query(session, trade_no=out_trade_no, status=order_status_pending)
    if not order_instance:
        logger.error(f'Invalid out_trade_no, out_trade_no:{out_trade_no}')
        return error_response(ErrorCode.ERROR_INTERNAL_SERVER, "Invalid out_trade_no")

    user_id = order_instance.user_id

    if amount is None or amount == '':
        logger.error(f'Invalid amount, amount:{amount}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid amount')

    amount = int(amount)

    user = User.query(session, id=user_id)
    if not user:
        logger.error(f'Invalid user_id, user_id:{user_id}')
        return error_response(ErrorCode.ERROR_INTERNAL_SERVER, "Invalid user_id")

    token_amount = amount * 100
    instance, e = UserRecharge.create(session, user_id=user.id, amount=token_amount, pay_amount=amount,
                                      recharge_method=recharge_method_pay, status=status_success)
    if instance is None:
        logger.error(f'UserRecharge.create inviter_id:{user.id} error:{e}')

    update_user_balance(session, user.id, token_amount)

    Order.update_status_to_normal(session, order_instance.id)

    response_data = ErrorCode.success()
    return jsonify(response_data)

@user_bp.route('/get_user_info', methods=['GET'])
def handle_get_user_info():
    session = g.session
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.error(f'Invalid token, auth_header:{auth_header}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

    token = auth_header[7:]
    user = User.query(session, token=token)
    if not user:
        logger.error(f'Invalid token, auth_header:{auth_header}')
        return error_response(ErrorCode.ERROR_TOKEN, 'Invalid token')

    user_balance = UserBalance.query(session, user_id=user.id)
    if not user_balance:
        remaining_tokens = 0
    else:
        remaining_tokens = user_balance.total_recharge - user_balance.consumed_amount

    last_time_using_token = 0
    chat_message = ChatMessage.query_last(session, user_id=user.id)

    if chat_message:
        last_time_using_token = chat_message.tokens_consumed

    user_info = {
        'username': user.username,
        'phone': user.phone,
        'email': user.email,
        'remaining_tokens': remaining_tokens,
        'referral_code': user.referral_code,
        'last_time_using_token': last_time_using_token,
    }

    response_data = ErrorCode.success(user_info)
    return jsonify(response_data)

@user_bp.route('/recharge', methods=['POST'])
def handle_recharge():
    session = g.session
    card_account = g.data.get('card_account')
    card_password = g.data.get('card_password')

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.error(f'Invalid token, auth_header:{auth_header}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

    token = auth_header[7:]

    user = User.query(session, token=token)
    if user is None:
        logger.error(f'Invalid token, auth_header:{auth_header}')
        return error_response(ErrorCode.ERROR_TOKEN, 'Invalid token')

    recharge_card = RechargeCard.query(session, card_account=card_account, card_password=card_password)

    if recharge_card is None or recharge_card.status != recharge_card_status_normal:
        logger.error(f'Invalid card_account, card_account:{card_account} card_password:{card_password}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid recharge card or already used')

    if update_user_balance(session, user.id, recharge_card.recharge_amount) is False:
        logger.error(f'handle_recharge update_user_balance, card_account:{card_account} '
                     f'card_password:{card_password} recharge_card.recharge_amount:{recharge_card.recharge_amount}')

    ret, err = update_recharge_card_status(session, recharge_card.card_account, recharge_card_status_used, user.username)
    if err:
        logger.error(f'handle_recharge update_recharge_card_status error:{err}')

    instance, e = UserRecharge.create(session, user_id=user.id, amount=recharge_card.recharge_amount,
                                      recharge_method=recharge_method_card, status=status_success)
    if instance is None:
        logger.error(f'handle_recharge UserRecharge.create inviter_id:{user.id} error:{e}')

    response_data = ErrorCode.success()
    return jsonify(response_data)

@user_bp.route('/recharge_cards', methods=['GET'])
def get_available_recharge_cards():
    session = g.session

    page = request.args.get('page')
    page_size = request.args.get('pageSize')

    if page is None or int(page) <= 0:
        page = 1

    if page_size is None or int(page_size) <= 0:
        page_size = 50

    offset = (int(page) - 1) * int(page_size)
    available_cards, e = RechargeCard.query_all(session, limit=int(page_size), offset=offset, status=recharge_card_status_normal)

    if e:
        logger.error(f'get_available_recharge_cards RechargeCard.query_all error:{e}')

    cards_data = [{'card_account': card.card_account, 'card_password': card.card_password,
                   'recharge_amount': str(card.recharge_amount)} for card in available_cards]

    response_data = ErrorCode.success(cards_data)
    return jsonify(response_data)

@user_bp.route('/add_recharge_card', methods=['POST'])
def add_recharge_card():
    session = g.session
    card_account = g.data.get('card_account')
    card_password = g.data.get('card_password')
    recharge_amount = int(g.data.get('recharge_amount', 100000))
    num = int(g.data.get('num', 1))

    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        logger.error(f'Invalid token, auth_header:{auth_header}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Invalid token')

    token = auth_header[7:]

    user = User.query(session, token=token)
    if user is None:
        logger.error(f'Invalid token, auth_header:{auth_header}')
        return error_response(ErrorCode.ERROR_TOKEN, 'Invalid token')

    created_cards = []
    for _ in range(num):
        card_account = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        card_password = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

        new_card, e = RechargeCard.create(session, card_account=card_account,
                                          card_password=card_password, recharge_amount=recharge_amount)

        if new_card is None:
            logger.error(f'add_recharge_card, Failed to create recharge card, error:{e}')
            return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'Failed to create recharge card')

        created_cards.append({'card_account': card_account, 'card_password': card_password, 'recharge_amount': recharge_amount})

    response_data = ErrorCode.success()
    response_data['cards'] = created_cards
    return jsonify(response_data)


@user_bp.route('/reset_password', methods=['POST'])
def reset_password():
    session = g.session
    username = g.data.get('username')
    verification_code = g.data.get('verification_code')
    verification_type = g.data.get('verification_type')
    phone = g.data.get('phone')
    email = g.data.get('email')
    new_password = g.data.get('new_password')

    if verification_type == verification_type_phone:
        user = User.query(session, phone=phone)
    elif verification_type == verification_type_email:
        user = User.query(session, email=email)
    else:
        user = User.query(session, username=username)

    if user is None:
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, 'User not found')

    is_verified, err_msg = user_verification(session, verification_type, verification_code, email, phone)

    if not is_verified:
        logger.error(f'reset_password, register_verification, error:{err_msg}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, err_msg)

    hashed_new_password = hash_token(new_password)
    new_token = generate_token(user.username, hashed_new_password)

    success, error_message = User.update(session, {"id": user.id},
                                         {"password": hashed_new_password, "token": new_token})
    if success:
        response_data = ErrorCode.success()
    else:
        logger.error(f'user not exist, username:{username}')
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, error_message)

    return jsonify(response_data)