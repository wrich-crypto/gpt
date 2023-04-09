from init import *
import random
import string

recharge_method_pay = 1
recharge_method_invite = 2

status_success = 1
status_failed = 2

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
    remaining_balance = Column(DECIMAL(10, 2), nullable=False)
    total_recharge = Column(DECIMAL(10, 2), nullable=False)
    consumed_amount = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(TIMESTAMP, default='CURRENT_TIMESTAMP', nullable=False)

class UserRecharge(BaseModel):
    __tablename__ = 'user_recharges'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    pay_amount = Column(DECIMAL(10, 2), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    recharge_method = Column(Integer, nullable=False)           #1支付通道 2邀请
    status = Column(Integer, nullable=False)                    #1成功 2失败
    created_at = Column(TIMESTAMP, default='CURRENT_TIMESTAMP', nullable=False)

def get_reward(inviter_recharge, invitee_recharge):
    if inviter_recharge is True and invitee_recharge is True:
        return 100000, 100000
    elif inviter_recharge is False and invitee_recharge is True:
        return 50000, 100000
    elif inviter_recharge is False and invitee_recharge is False:
        return 50000, 50000

def update_user_balance(user_id, reward):
    userBalance = UserBalance.query(session, user_id=user_id)

    if userBalance is None:
        remaining_balance = reward
        total_recharge = reward
        consumed_amount = 0
    else:
        remaining_balance = userBalance.remaining_balance + reward
        total_recharge = userBalance.total_recharge + reward
        consumed_amount = userBalance.consumed_amount

    result, e = UserBalance.upsert(session, {'user_id': user_id},
                       {'user_id': user_id, 'remaining_balance': remaining_balance,
                        'total_recharge': total_recharge, 'consumed_amount': consumed_amount})

    if result is False:
        logger.error(f'user_id:{user_id} update_balance_amount:{reward} error:{e}')
        return

def generate_invication(inviter_id, invitee_id):
    inviter_recharge = UserRecharge.exists(session, user_id=inviter_id, recharge_method=recharge_method_pay)
    invitee_recharge = UserRecharge.exists(session, user_id=invitee_id, recharge_method=recharge_method_pay)
    inviter_reward, invitee_reward = get_reward(inviter_recharge, invitee_recharge)

    instance, e =UserInvitation.create(session, inviter_id=inviter_id, invitee_id=invitee_id,
                                       inviter_reward=inviter_reward, invitee_reward=invitee_reward)

    if instance is None:
        logger.error(f'invitee already inviter_id:{inviter_id} error:{e}')
        return

    print('UserRecharge')
    instance, e = UserRecharge.create(session, user_id=inviter_id, amount=inviter_reward,
                                      recharge_method=recharge_method_invite, status=status_success)
    if instance is None:
        logger.error(f'UserRecharge.create inviter_id:{inviter_id} error:{e}')

    instance, e = UserRecharge.create(session, user_id=invitee_id, amount=invitee_reward,
                                      recharge_method=recharge_method_invite, status=status_success)
    if instance is None:
        logger.error(f'UserRecharge.create inviter_id:{inviter_id} error:{e}')

    print('update_user_balance')
    update_user_balance(inviter_id, inviter_reward)
    update_user_balance(invitee_id, invitee_reward)

def generate_referral_code():
    referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return referral_code