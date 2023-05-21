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
user_role_manager = 2

status_normal = 1
status_delete = 2

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

    bind_phone = Column(Integer, nullable=True)
    card_count = Column(Integer, nullable=True)
    points = Column(Integer, nullable=True)
    used_points = Column(Integer, nullable=True)
    remaining_points = Column(Integer, nullable=True)
    source = Column(String(255), nullable=True)
    remarks = Column(String(255), nullable=True)
    role = Column(Integer, default=user_role_normal)
    status = Column(Integer, default=status_normal)
    created_at = Column(DateTime, default=datetime.datetime.now(), nullable=False)

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

class UserInvitation(BaseModel):
    __tablename__ = 'user_invitations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    inviter_id = Column(Integer, nullable=False)
    inviter_reward = Column(DECIMAL(10, 2), nullable=False)
    invitee_id = Column(Integer, nullable=False)
    invitee_reward = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(), nullable=False)

class UserBalance(BaseModel):
    __tablename__ = 'user_balances'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    total_recharge = Column(DECIMAL(20, 2), nullable=False)
    consumed_amount = Column(DECIMAL(20, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(), nullable=False)

class UserRecharge(BaseModel):
    __tablename__ = 'user_recharges'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    pay_amount = Column(DECIMAL(20, 2), nullable=False)
    amount = Column(DECIMAL(20, 2), nullable=False)
    recharge_method = Column(Integer, nullable=False)           #1支付通道 2邀请
    status = Column(Integer, nullable=False)                    #1成功 2失败
    created_at = Column(DateTime, default=datetime.datetime.now(), nullable=False)

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
    expired_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP + INTERVAL '5' MINUTE"), nullable=False)

class RechargeCard(BaseModel):
    __tablename__ = 'recharge_cards'

    id = Column(Integer, primary_key=True, autoincrement=True)
    card_account = Column(String(20), unique=True, nullable=False)
    card_password = Column(String(20), nullable=False)
    create_time = Column(DateTime, default=datetime.datetime.now(), nullable=False)
    expire_time = Column(DateTime, nullable=True)
    total_points = Column(Integer, nullable=True)
    used_points = Column(Integer, nullable=True)
    bound_user = Column(String(255), nullable=True)
    recharge_type = Column(String(50), nullable=True)
    recharge_amount = Column(DECIMAL(20, 2), nullable=False)
    status = Column(Integer, nullable=False, default=1)  # 1未使用, 2已使用
    recharge_time = Column(DateTime, nullable=True)

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
                {'points': userBalance.total_recharge, 'used_points': userBalance.consumed_amount + consumed_amount,
                 'remaining_points': userBalance.total_recharge - userBalance.consumed_amount - consumed_amount})

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