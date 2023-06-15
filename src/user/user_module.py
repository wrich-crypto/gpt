from init import *
from src.admin.admin_module import DevConfig

recharge_method_pay = 1
recharge_method_invite = 2
recharge_method_card = 3
recharge_method_register = 4

status_success = 1
status_failed = 2

code_type_email = 1
code_type_phone = 2

verification_type_email = 1
verification_type_phone = 2

recharge_card_status_normal = 1
recharge_card_status_used = 2

user_role_normal = 1
user_role_agent = 2
user_role_manager = 3
user_role_promotion = 4

status_normal = 1
status_delete = 2

order_status_success = 1
order_status_pending = 2
order_status_error = 3

order_pay_type_native = 1
order_pay_type_jsapi = 2
order_pay_type_h5 = 3


class User(BaseModel):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)

    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    token = Column(String(100), index=True, nullable=True)
    invitation_code = Column(String(20), unique=True, nullable=False)
    referral_code = Column(String(20), unique=True, nullable=False)
    invitation_user_id = Column(String(20), nullable=True)
    invitation_user_name = Column(String(100), nullable=True)

    bind_phone = Column(Integer, nullable=True)
    card_count = Column(Integer, nullable=True)
    points = Column(Integer, nullable=True)
    used_points = Column(Integer, nullable=True)
    remaining_points = Column(Integer, nullable=True)
    source = Column(String(255), nullable=True)
    remarks = Column(String(255), nullable=True)
    role = Column(String(255), default=str(user_role_normal))
    status = Column(Integer, default=status_normal)
    created_at = Column(DateTime, default=datetime.datetime.now(), nullable=False)
    createTime = Column(DateTime, default=datetime.datetime.now(), nullable=False)
    updateTime = Column(DateTime, default=datetime.datetime.now(), nullable=False)

    @classmethod
    def update_user_source(cls, session, user_id, source):
        try:
            user = session.query(cls).get(user_id)
            if user:
                user.source = source
                session.commit()

            return None
        except Exception as e:
            return e

    def is_role_present(self, role_to_check):
        """
        Check if the given role is present in the role attribute of the User instance.

        Parameters
        ----------
        role_to_check: int
            The role to check.

        Returns
        -------
        bool
            True if the role is present, False otherwise.
        """
        role_to_check = str(role_to_check)
        roles = self.role.split(',')
        return role_to_check in roles

class Order(BaseModel):
    __tablename__ = 'user_orders'
    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_no = Column(String(100), nullable=False)
    user_id = Column(Integer, nullable=False)
    order_type = Column(Integer, nullable=False, default=1)     #默认1微信支付native 2微信支付jsapi 3微信支付h5
    amount = Column(DECIMAL(10, 2), nullable=False)
    status = Column(Integer, nullable=False, default=1) #默认1表示正常 2表示订单执行中 3表示订单失败
    created_at = Column(DateTime, default=datetime.datetime.now(), nullable=False)
    createTime = Column(DateTime, default=datetime.datetime.now(), nullable=False)
    updateTime = Column(DateTime, default=datetime.datetime.now(), nullable=False)


    @classmethod
    def update_status_to_normal(cls, session, order_id, status=order_status_success):
        """
        Update the status of an order to normal (1).

        :param session: The database session to use for the update.
        :param order_id: The ID of the order to update.
        """
        order = session.query(cls).filter_by(id=order_id).first()
        if order:
            order.status = status
            session.commit()
        else:
            raise ValueError(f"Order with ID {order_id} not found")

class UserInvitation(BaseModel):
    __tablename__ = 'user_invitations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    inviter_id = Column(Integer, nullable=False)
    inviter_reward = Column(DECIMAL(10, 2), nullable=False)
    invitee_id = Column(Integer, nullable=False)
    invitee_reward = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(), nullable=False)
    createTime = Column(DateTime, default=datetime.datetime.now(), nullable=False)
    updateTime = Column(DateTime, default=datetime.datetime.now(), nullable=False)

class UserBalance(BaseModel):
    __tablename__ = 'user_balances'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    total_recharge = Column(DECIMAL(20, 2), nullable=False)
    consumed_amount = Column(DECIMAL(20, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(), nullable=False)
    createTime = Column(DateTime, default=datetime.datetime.now(), nullable=False)
    updateTime = Column(DateTime, default=datetime.datetime.now(), nullable=False)

class UserRecharge(BaseModel):
    __tablename__ = 'user_recharges'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    pay_amount = Column(DECIMAL(20, 2), nullable=False)
    amount = Column(DECIMAL(20, 2), nullable=False)
    recharge_method = Column(Integer, nullable=False)           #1支付通道 2邀请 3充值卡 4注册
    status = Column(Integer, nullable=False)                    #1成功 2失败
    created_at = Column(DateTime, default=datetime.datetime.now(), nullable=False)
    createTime = Column(DateTime, default=datetime.datetime.now(), nullable=False)
    updateTime = Column(DateTime, default=datetime.datetime.now(), nullable=False)

    @classmethod
    def total_pay_amount(cls, session):
        try:
            total = session.query(func.sum(cls.pay_amount)).scalar()
            return total if total is not None else Decimal('0.00'), None
        except SQLAlchemyError as e:
            return None, str(e)
        except Exception as e:
            return None, str(e)

    @classmethod
    def count_recharge_method(cls, session, user_id):
        try:
            count = session.query(cls).filter(cls.user_id == user_id, cls.recharge_method == recharge_method_card).count()
            return count, None
        except SQLAlchemyError as e:
            return 0, str(e)
        except Exception as e:
            return 0, str(e)

class VerificationCode(BaseModel):
    __tablename__ = 'verification_code'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(100), nullable=False)
    code_type = Column(String(10), nullable=False)              #1邮箱2手机
    code = Column(String(10), nullable=False)
    expired_at = Column(DateTime, default=datetime.datetime.now(), nullable=False)
    createTime = Column(DateTime, default=datetime.datetime.now(), nullable=False)
    updateTime = Column(DateTime, default=datetime.datetime.now(), nullable=False)

class RechargeCard(BaseModel):
    __tablename__ = 'recharge_cards'

    id = Column(Integer, primary_key=True, autoincrement=True)
    card_account = Column(String(20), unique=True, nullable=False)
    card_password = Column(String(20), nullable=False)
    expire_time = Column(DateTime, nullable=True)
    used_points = Column(Integer, nullable=True)
    bound_user = Column(String(255), nullable=True)
    recharge_type = Column(String(50), nullable=True)
    recharge_amount = Column(DECIMAL(20, 2), nullable=False)
    status = Column(Integer, nullable=False, default=1)  # 1未使用, 2已使用
    recharge_time = Column(DateTime, nullable=True)
    create_user = Column(String(100), nullable=True)
    create_user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now(), nullable=False)
    createTime = Column(DateTime, default=datetime.datetime.now(), nullable=False)
    updateTime = Column(DateTime, default=datetime.datetime.now(), nullable=False)

class Agent(BaseModel):
    __tablename__ = 'agent'

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=True, comment="标题")
    slogan = Column(String(100), nullable=True, comment="广告语")
    ai_name = Column(String(50), nullable=True, comment="AI名字")
    ai_avatar = Column(String(50), nullable=True, comment="AI头像")
    referral_reward = Column(Integer, nullable=True, comment="邀请奖励开关1打开 2关闭")
    wechat_qr_code = Column(String(255), nullable=True, comment="微信二维码")
    customer_service_phone = Column(String(20), nullable=True, comment="客服电话")
    domain = Column(String(100), nullable=True, comment="域名多个用逗号隔开")
    referral_code = Column(String(100), nullable=True, comment="邀请码")
    user_id = Column(Integer, nullable=True, comment="用户ID 2关闭")
    balance = Column(DECIMAL(20, 2), default=0, nullable=False)
    createTime = Column(DateTime, default=datetime.datetime.now(), nullable=False)
    updateTime = Column(DateTime, default=datetime.datetime.now(), nullable=False)

    @classmethod
    def get_user_id_by_source(cls, session, source):
        try:
            agent = session.query(cls).filter(cls.domain.like(f"%{source}%")).first()
            if agent:
                return agent.user_id
            else:
                return ""
        except:
            return ""

    @classmethod
    def get_agent_by_source(cls, session, source):
        try:
            agent = session.query(cls).filter(cls.domain.like(f"%{source}%")).first()
            if agent:
                return agent
            else:
                return ""
        except:
            return ""

def update_recharge_card_status(session, card_account, status=recharge_card_status_used, username=''):
    return RechargeCard.update(session, {'card_account': card_account},
                       {'status': status, 'bound_user': username})

def get_reward(session, inviter_recharge, invitee_recharge):
    invite_token_count = DevConfig.get_invite_token_count(session)
    recharge_token_count = 20000

    if inviter_recharge is True and invitee_recharge is True:
        return (recharge_token_count + invite_token_count), (recharge_token_count + invite_token_count)
    elif inviter_recharge is False and invitee_recharge is True:
        return invite_token_count, (recharge_token_count + invite_token_count)
    elif inviter_recharge is True and invitee_recharge is False:
        return (recharge_token_count + invite_token_count), invite_token_count
    elif inviter_recharge is False and invitee_recharge is False:
        return invite_token_count, invite_token_count

def update_user_balance(session, user_id, reward):
    userBalance = UserBalance.query(session, user_id=user_id)
    reward = Decimal(reward)

    if userBalance is None:
        total_recharge = reward
        consumed_amount = 0
    else:
        total_recharge = userBalance.total_recharge + reward
        consumed_amount = userBalance.consumed_amount

    result, e = UserBalance.upsert(session, {'user_id': user_id},
                       {'user_id': user_id, 'total_recharge': total_recharge, 'consumed_amount': consumed_amount})

    if result is False:
        logger.error(f'user_id:{user_id} update_balance_amount:{reward} error:{e}')
        return False

    card_count, e = UserRecharge.count_recharge_method(session, user_id)

    if e is not None:
        logger.error(f'user_id:{user_id} UserRecharge.count_recharge_method:{reward} error:{e}')

    user = User.query(session, id=user_id)

    if user is None:
        return False

    result, e = user.update(session, {'id': user_id},
                {'points': total_recharge, 'used_points': consumed_amount,
                 'remaining_points': total_recharge - consumed_amount, 'card_count': card_count})

    if result is False:
        logger.error(f'user_id:{user_id} update user balance:{(total_recharge - consumed_amount)} error:{e}')
        return False

    return True

def update_user_consumed(session, user_id, consumed_amount):
    userBalance = UserBalance.query(session, user_id=user_id)
    consumed_amount = Decimal(consumed_amount)

    if userBalance is None:
        return False

    current_consumed_amount = userBalance.consumed_amount
    current_total_amount = userBalance.total_recharge
    current_remain_amount = userBalance.total_recharge - userBalance.consumed_amount

    result, e = UserBalance.upsert(session, {'user_id': user_id},
                       {'user_id': user_id, 'consumed_amount': (consumed_amount + current_consumed_amount)})

    if result is False:
        logger.error(f'user_id:{user_id} update_user_consumed:{(consumed_amount + current_consumed_amount)} error:{e}')
        return False

    #points = Column(Integer, nullable=True)
    #used_points = Column(Integer, nullable=True)
    #remaining_points = Column(Integer, nullable=True)
    user = User.query(session, id=user_id)

    if user is None:
        return False

    result, e = user.update(session, {'id': user_id},
                {'points': userBalance.total_recharge, 'used_points': current_consumed_amount + consumed_amount,
                 'remaining_points': userBalance.total_recharge - current_consumed_amount - consumed_amount})

    if result is False:
        logger.error(f'user_id:{user_id} update:{(consumed_amount + current_consumed_amount)} error:{e}')
        return False

    return True

def balance_valid(session, user_id):
    userBalance = UserBalance.query(session, user_id=user_id)

    if userBalance is None:
        return False

    if userBalance.total_recharge - userBalance.consumed_amount > 0:
        return True

    return False

def generate_invication(session, inviter_id, invitee_id):
    inviter_recharge = UserRecharge.exists(session, user_id=inviter_id, recharge_method=recharge_method_pay)
    invitee_recharge = UserRecharge.exists(session, user_id=invitee_id, recharge_method=recharge_method_pay)
    inviter_reward, invitee_reward = get_reward(session, inviter_recharge, invitee_recharge)

    instance, e =UserInvitation.create(session, inviter_id=inviter_id, invitee_id=invitee_id,
                                       inviter_reward=inviter_reward, invitee_reward=invitee_reward)

    if instance is None:
        logger.error(f'invitee already inviter_id:{inviter_id} error:{e}')
        return

    logger.info('UserRecharge')
    instance, e = UserRecharge.create(session, user_id=inviter_id, amount=inviter_reward,
                                      recharge_method=recharge_method_invite, status=status_success)
    if instance is None:
        logger.error(f'UserRecharge.create inviter_id:{inviter_id} error:{e}')

    instance, e = UserRecharge.create(session, user_id=invitee_id, amount=invitee_reward,
                                      recharge_method=recharge_method_invite, status=status_success)
    if instance is None:
        logger.error(f'UserRecharge.create inviter_id:{inviter_id} error:{e}')

    logger.info('update_user_balance')
    update_user_balance(session, inviter_id, inviter_reward)
    update_user_balance(session, invitee_id, invitee_reward)

def generate_referral_code():
    referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return referral_code

def generate_code():
    code = ''.join(random.choices(string.digits, k=6))
    return code

def register_verification(session, registration_type, verification_code, email, phone):
    registration_type = int(registration_type)

    if registration_type == verification_type_email:
        if User.exists(session, email=email):
            logger.error(f'email:{email} exist')
            return False, f'email:{email} exist'

    elif registration_type == verification_type_phone:
        if User.exists(session, phone=phone):
            logger.error(f'phone:{phone} exist')
            return False, f'phone:{phone} exist'
    else:
        return False, f'registration_type:{registration_type} error'

    return user_verification(session, registration_type, verification_code, email, phone)

def user_verification(session, registration_type, verification_code, email, phone):
    registration_type = int(registration_type)

    if registration_type == verification_type_email:
        if email is None or email == '':
            logger.error(f'email:{email} is null')
            return False, f'email:{email} is null'

        verification = VerificationCode.query(session, code_type=registration_type, email=email)
    elif registration_type == verification_type_phone:
        if phone is None or phone == '':
            logger.error(f'phone:{phone} is null')
            return False, f'phone:{phone} is null'

        verification = VerificationCode.query(session, code_type=registration_type, phone=phone)
    else:
        return False, f'registration_type:{registration_type} error'

    if not verification:
        logger.error(f'verification not find '
                     f'registration_type:{registration_type},'
                     f'verification_code:{verification_code},'
                     f'email:{email},'
                     f'phone:{phone},'
                     f'verification.code:{verification.code}')
        return False, f'verification code error, send verification code again'

    if verification.code != verification_code:
        logger.error(f'verification not find'
                     f'registration_type:{registration_type},'
                     f'verification_code:{verification_code},'
                     f'email:{email},'
                     f'phone:{phone},'
                     f'verification.code:{verification.code}')
        return False, f'verification code error, send verification code again'

    return True, ''

def request_pay_by_type(session, order_type, amount, user_id, open_id=None):
    if order_type == order_pay_type_native:
        code, msg, out_trade_no, amount = request_pay(amount)
        if code != 200:
            return error_response(code, "Payment request failed")

        # Parse JSON from msg and extract the code_url value
        msg_data = json.loads(msg)
        code_url = msg_data.get('code_url')
        if not code_url:
            return error_response(ErrorCode.ERROR_INVALID_PARAMETER, "Missing code_url in response")

        response_data = ErrorCode.success({'code_url': code_url, 'trade_no': out_trade_no})

    elif order_type == order_pay_type_jsapi:
        reason, out_trade_no, amount = request_pay_jsapi(amount, open_id)
        response_data = ErrorCode.success({'reason': reason, 'trade_no': out_trade_no})

    elif order_type == order_pay_type_h5:
        code, reason, out_trade_no, amount = request_pay_h5(amount)

        if code != 200:
            return error_response(code, "Payment request failed")

        # Parse JSON from msg and extract the code_url value
        reason_data = json.loads(reason)
        h5_url = reason_data.get('h5_url')

        if not h5_url:
            return error_response(ErrorCode.ERROR_INVALID_PARAMETER, "Missing h5_url in response")

        response_data = ErrorCode.success({'h5_url': h5_url, 'trade_no': out_trade_no})

    else:
        return error_response(ErrorCode.ERROR_INVALID_PARAMETER, "Order.create error")

    instance, error_msg = Order.create(session, trade_no=out_trade_no, user_id=user_id,
                                       order_type=order_type,
                                       amount=amount, status=order_status_pending)

    if error_msg is not None:
        logger.error(f'Order.create, error_msg:{error_msg}')
        return error_response(ErrorCode.ERROR_INTERNAL_SERVER, "Order.create error")

    return response_data

def request_pay(amount):
    url = f"{main_config.pay_server_domain}/pay?amount={amount}"
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.text)
        if data.get('code') in range(200, 300):
            return data.get('code'), data.get('message'), data.get('out_trade_no'), data.get('amount')
        else:
            return None, "Error: " + data.get('message'), None, None
    else:
        return None, "Error: request failed", None, None

def request_pay_jsapi(amount, open_id):
    url = f"{main_config.pay_server_domain}/pay_jsapi?amount={amount}&open_id={open_id}"
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.text)
        if data.get('code') == 0:
            return data.get('result'), data.get('out_trade_no'), data.get('amount')
        else:
            return "Error: " + data.get('result')['reason'], None, None
    else:
        return "Error: request failed", None, None

def request_pay_h5(amount):
    url = f"{main_config.pay_server_domain}/pay_h5?amount={amount}"
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.text)
        if data.get('code') in range(200, 300):
            return data.get('code'), data.get('message'), data.get('out_trade_no'), data.get('amount')
        else:
            return None, "Error: " + data.get('message'), None, None
    else:
        return None, "Error: request failed", None, None

def get_openid_by_code(code):
    url = f'{main_config.pay_server_domain}/get_openid?code={code}'  # replace with your server url

    try:
        response = requests.get(url)
        response.raise_for_status()  # If the request returned an HTTP error this line will raise a HTTPError exception

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None

    except requests.exceptions.RequestException as err:
        print(f"Error occurred: {err}")
        return None

    data = response.json()
    print(data)
    if 'openid' in data:
        return data['openid']
    else:
        print('Could not get OpenID.')
        return None

def init_referral_code(session, source):
    user_id = Agent.get_user_id_by_source(session, source)

    user = User.query(session, id=user_id)

    if user is None:
        logger.error(f'init_referral_code User.query, account no exist')
        return ''


    return user.referral_code