from init import *
import random
import string

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
    invitee_id = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, default='CURRENT_TIMESTAMP', nullable=False)


class UserBalance(BaseModel):
    __tablename__ = 'user_balances'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    remaining_balance = Column(DECIMAL(10, 2), nullable=False)
    total_recharge = Column(DECIMAL(10, 2), nullable=False)
    consumed_amount = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(TIMESTAMP, default='CURRENT_TIMESTAMP', nullable=False)

def generate_referral_code():
    referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return referral_code