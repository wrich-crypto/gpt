from init import *

recharge_method_pay = 1
recharge_method_invite = 2

status_success = 1
status_failed = 2

code_type_email = 1
code_type_phone = 2

verification_type_email = 1
verification_type_phone = 2

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
    created_at = Column(TIMESTAMP, default='CURRENT_TIMESTAMP', nullable=False)

class UserInvitation(BaseModel):
    __tablename__ = 'user_invitations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    inviter_id = Column(Integer, nullable=False)
    inviter_reward = Column(DECIMAL(10, 2), nullable=False)
    invitee_id = Column(Integer, nullable=False)
    invitee_reward = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(TIMESTAMP, default='CURRENT_TIMESTAMP', nullable=False)

class UserBalance(BaseModel):
    __tablename__ = 'user_balances'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    total_recharge = Column(DECIMAL(20, 2), nullable=False)
    consumed_amount = Column(DECIMAL(20, 2), nullable=False)
    created_at = Column(TIMESTAMP, default='CURRENT_TIMESTAMP', nullable=False)

class UserRecharge(BaseModel):
    __tablename__ = 'user_recharges'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    pay_amount = Column(DECIMAL(20, 2), nullable=False)
    amount = Column(DECIMAL(20, 2), nullable=False)
    recharge_method = Column(Integer, nullable=False)           #1支付通道 2邀请
    status = Column(Integer, nullable=False)                    #1成功 2失败
    created_at = Column(TIMESTAMP, default='CURRENT_TIMESTAMP', nullable=False)

    @classmethod
    def total_pay_amount(cls, session):
        try:
            total = session.query(func.sum(cls.pay_amount)).scalar()
            return total if total is not None else Decimal('0.00'), None
        except SQLAlchemyError as e:
            return None, str(e)
        except Exception as e:
            return None, str(e)

class VerificationCode(BaseModel):
    __tablename__ = 'verification_code'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(100), nullable=False)
    code_type = Column(String(10), nullable=False)              #1邮箱2手机
    code = Column(String(10), nullable=False)
    expired_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP + INTERVAL '5' MINUTE"), nullable=False)

def get_reward(inviter_recharge, invitee_recharge):
    if inviter_recharge is True and invitee_recharge is True:
        return 100000, 100000
    elif inviter_recharge is False and invitee_recharge is True:
        return 50000, 100000
    elif inviter_recharge is False and invitee_recharge is False:
        return 50000, 50000

def update_user_balance(user_id, reward):
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

    return True

def generate_invication(session, inviter_id, invitee_id):
    inviter_recharge = UserRecharge.exists(session, user_id=inviter_id, recharge_method=recharge_method_pay)
    invitee_recharge = UserRecharge.exists(session, user_id=invitee_id, recharge_method=recharge_method_pay)
    inviter_reward, invitee_reward = get_reward(inviter_recharge, invitee_recharge)

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
    update_user_balance(inviter_id, inviter_reward)
    update_user_balance(invitee_id, invitee_reward)

def generate_referral_code():
    referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return referral_code

def generate_code():
    code = ''.join(random.choices(string.digits, k=6))
    return code

def register_verification(session, registration_type, verification_code, email, phone):
    registration_type = int(registration_type)

    if registration_type == verification_type_email:
        if email is None or email == '':
            logger.error(f'email:{email} is null')
            return False, f'email:{email} is null'

        if User.exists(session, email=email):
            logger.error(f'email:{email} exist')
            return False, f'email:{email} exist'

        verification = VerificationCode.query(session, code_type=registration_type, email=email)
    elif registration_type == verification_type_phone:
        if phone is None or phone == '':
            logger.error(f'phone:{phone} is null')
            return False, f'phone:{phone} is null'

        if User.exists(session, phone=phone):
            logger.error(f'phone:{phone} exist')
            return False, f'phone:{phone} exist'

        verification = VerificationCode.query(session, code_type=registration_type, phone=phone)
    else:
        return False, f'registration_type:{registration_type} error'

    if not verification:
        logger.error(f'verification not find'
                     f'registration_type:{registration_type},'
                     f'verification_code:{verification_code},'
                     f'email:{email},'
                     f'phone:{phone},')
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