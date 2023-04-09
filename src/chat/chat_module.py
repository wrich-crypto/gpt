from init import *

class ChatMessage(BaseModel):
    __tablename__ = 'chat_messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    channel_id = Column(Integer, nullable=False)
    message_id = Column(Integer, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text,nullable=False)
    tokens_consumed = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, default='CURRENT_TIMESTAMP', nullable=False)

class ChatChannel(BaseModel):
    __tablename__ = 'chat_channels'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    status = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, default='CURRENT_TIMESTAMP', nullable=False)

    @classmethod
    def get_channels_by_user(cls, session, user_id, status=None):
        query = session.query(cls).filter_by(user_id=user_id)
        if status is not None:
            query = query.filter_by(status=status)
        return query.all()

    @classmethod
    def delete_channel(cls, session, channel_id):
        try:
            session.query(cls).filter_by(id=channel_id).update({"status": 2})
            session.commit()
            return True, None
        except SQLAlchemyError as e:
            session.rollback()
            return False, str(e)
        except Exception as e:
            session.rollback()
            return False, str(e)
