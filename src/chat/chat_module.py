from init import *
from sqlalchemy import desc

class ChatMessage(BaseModel):
    __tablename__ = 'chat_messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    channel_id = Column(Integer, nullable=False)
    message_id = Column(String(100), nullable=False)
    stream_id = Column(String(100), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text,nullable=False)
    tokens_consumed = Column(DECIMAL(10, 2), nullable=False)
    version = Column(String(10), nullable=False)
    created_at = Column(TIMESTAMP, default='CURRENT_TIMESTAMP', nullable=False)

    @classmethod
    def get_message_history_by_channel_id(cls, session, channel_id):
        message_history = ''
        query = session.query(cls).filter_by(channel_id=channel_id)
        query = query.order_by(cls.id.desc())
        query = query.limit(3)
        message_list = query.all()
        message_list = list(reversed(message_list))

        for message in message_list:
            if message.question is None or message.question == '':
                continue

            if message.answer is None or message.answer == '':
                continue

            message_history = message_history + f"User: {message.question}\n"
            message_history = message_history + f"The assistant: {message.answer}\n"

        if len(message_list) > 0:
            message_history = message_history + '\n Answers to questions do not need to begin with "The assistant:"'

        return message_history

class ChatChannel(BaseModel):
    __tablename__ = 'chat_channels'
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_uuid = Column(String(100), nullable=True)
    title = Column(Text, nullable=True)
    user_id = Column(Integer, nullable=False)
    version = Column(String(10), nullable=False)
    status = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, default='CURRENT_TIMESTAMP', nullable=False)

    @classmethod
    def get_channels_by_user(cls, session, user_id, status=None):
        query = session.query(cls).filter_by(user_id=user_id)
        if status is not None:
            query = query.filter_by(status=status)
        return query.all()

    @classmethod
    def delete_channel(cls, session, channel_id, user_id):
        try:
            session.query(cls).filter_by(id=channel_id, user_id=user_id).update({"status": 2})
            session.commit()
            return True, None
        except SQLAlchemyError as e:
            session.rollback()
            return False, str(e)
        except Exception as e:
            session.rollback()
            return False, str(e)
