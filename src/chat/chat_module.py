from init import *

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    channel_id = Column(Integer, nullable=False)
    message_id = Column(Integer, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text,nullable=False)
    tokens_consumed = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, default='CURRENT_TIMESTAMP', nullable=False)

class ChatChannel(Base):
    __tablename__ = 'chat_channels'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    status = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, default='CURRENT_TIMESTAMP', nullable=False)
