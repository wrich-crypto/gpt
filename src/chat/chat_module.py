from init import *
from sqlalchemy import desc
import tiktoken
from sqlalchemy.orm import Session
from src.admin.admin_module import ApiKeys

SUPPLIER_TYPE_OPENAI = 'openai'
SUPPLIER_TYPE_UCHAT = 'uchat'

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
    api_key = Column(String(255), nullable=False)  # 新增的字段
    created_at = Column(DateTime, default=datetime.datetime.now(timezone('Asia/Shanghai')), nullable=False)
    createTime = Column(DateTime, default=datetime.datetime.now(timezone('Asia/Shanghai')), nullable=False)
    updateTime = Column(DateTime, default=datetime.datetime.now(timezone('Asia/Shanghai')), nullable=False)

    @classmethod
    def get_message_history_by_channel_id(cls, session, channel_id):
        query = session.query(cls).filter_by(channel_id=channel_id)
        query = query.order_by(cls.id.desc())
        query = query.limit(3)
        message_list = query.all()
        message_list = list(reversed(message_list))
        return message_list

    @classmethod
    def get_token_sum_by_api_key(cls, session, api_key, begin_time=None, end_time=None):
        query = session.query(func.sum(cls.tokens_consumed)).filter(cls.api_key == api_key)
        if begin_time is not None:
            query = query.filter(cls.created_at >= begin_time)
        if end_time is not None:
            query = query.filter(cls.created_at <= end_time)
        return query.scalar() or 0

    @classmethod
    def get_today_token_sum_by_api_key(cls, session, api_key):
        today_begin = datetime.datetime.now(timezone('Asia/Shanghai')).replace(hour=0, minute=0, second=0, microsecond=0)
        tomorrow_begin = today_begin + datetime.timedelta(days=1)
        return cls.get_token_sum_by_api_key(session, api_key, begin_time=today_begin, end_time=tomorrow_begin)

class ChatChannel(BaseModel):
    __tablename__ = 'chat_channels'
    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_uuid = Column(String(100), nullable=True)
    title = Column(Text, nullable=True)
    user_id = Column(Integer, nullable=False)
    version = Column(String(10), nullable=False)
    status = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.now(timezone('Asia/Shanghai')), nullable=False)
    createTime = Column(DateTime, default=datetime.datetime.now(timezone('Asia/Shanghai')), nullable=False)
    updateTime = Column(DateTime, default=datetime.datetime.now(timezone('Asia/Shanghai')), nullable=False)

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

def update_api_key_tokens(session: Session, api_key: str):
    """
    Updates the total_tokens and daily_tokens of the given api_key in the database.

    :param api_key: The API key to update.
    :param session: The SQLAlchemy session.
    :return: None
    """

    try:
        total_tokens = ChatMessage.get_token_sum_by_api_key(session, api_key)
        daily_tokens = ChatMessage.get_today_token_sum_by_api_key(session, api_key)

        ApiKeys.update_total_tokens(session, api_key, total_tokens)
        ApiKeys.update_daily_tokens(session, api_key, daily_tokens)
    except Exception as e:
        logger.error(f"Error updating API key tokens: {e}")