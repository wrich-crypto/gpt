from init import *
from sqlalchemy import desc
import tiktoken

using_context_open = 1
using_context_stop = 2

class ChatMessage(BaseModel):
    __tablename__ = 'chat_messages'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)
    channel_id = Column(Integer, nullable=False)
    message_id = Column(String(100), nullable=False)
    stream_id = Column(String(100), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    using_context = Column(Integer, nullable=False)
    tokens_consumed = Column(DECIMAL(10, 2), nullable=False)
    version = Column(String(10), nullable=False)
    created_at = Column(TIMESTAMP, default='CURRENT_TIMESTAMP', nullable=False)

    @classmethod
    def get_message_history_by_channel_id(cls, session, channel_id):
        query = session.query(cls).filter_by(channel_id=channel_id)
        query = query.order_by(cls.id.desc())
        query = query.limit(3)
        message_list = query.all()
        message_list = list(reversed(message_list))
        return message_list

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

def num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301"):
    """Returns the number of tokens used by a list of messages."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        print("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")
    if model == "gpt-3.5-turbo":
        print("Warning: gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0301.")
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0301")
    elif model == "gpt-4":
        print("Warning: gpt-4 may change over time. Returning num tokens assuming gpt-4-0314.")
        return num_tokens_from_messages(messages, model="gpt-4-0314")
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif model == "gpt-4-0314":
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        raise NotImplementedError(f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens.""")
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens