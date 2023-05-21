from init import *
from sqlalchemy import and_

SUPPLIER_TYPE_OPENAI = 'openai'
SUPPLIER_TYPE_UCHAT = 'uchat'

status_normal = 1
status_delete = 2

GPT3_5 = '3.5'
GPT4 = '4'

class DevConfig(BaseModel):
    __tablename__ = 'dev_config'

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_type = Column(String(20), nullable=False)
    supplier = Column(String(50), nullable=False, default='openai')
    free_token_count = Column(Integer, nullable=False, default=0)
    invite_token_count = Column(Integer, nullable=False, default=0)

    @classmethod
    def get_model_type_by_version(cls, version):
        if version == '3.5':
            return GPT3_5
        else:
            return GPT4

    @classmethod
    def get_model_type(cls, session, id: int = 1):
        try:
            dev_config = session.query(cls).filter_by(id=id).first()

            if dev_config.model_type not in [GPT3_5, GPT4]:
                return GPT3_5

            return dev_config.model_type if dev_config else GPT3_5
        except Exception as e:
            return GPT3_5

    @classmethod
    def get_supplier(cls, session, id: int = 1):
        try:
            dev_config = session.query(cls).filter_by(id=id).first()

            if dev_config.supplier not in [SUPPLIER_TYPE_OPENAI, SUPPLIER_TYPE_UCHAT]:
                return SUPPLIER_TYPE_OPENAI

            return dev_config.supplier if dev_config else SUPPLIER_TYPE_OPENAI
        except Exception as e:
            return SUPPLIER_TYPE_OPENAI

    @classmethod
    def get_free_token_count(cls, session, id: int = 1):
        try:
            dev_config = session.query(cls).filter_by(id=id).first()
            return dev_config.free_token_count if dev_config else 10000
        except Exception as e:
            return 10000

    @classmethod
    def get_invite_token_count(cls, session, id: int = 1):
        try:
            dev_config = session.query(cls).filter_by(id=id).first()
            return dev_config.invite_token_count if dev_config else 20000
        except Exception as e:
            return 20000


class ApiKeys(BaseModel):
    __tablename__ = 'api_keys'

    id = Column(Integer, primary_key=True, autoincrement=True)
    api_key = Column(String(255), nullable=False)
    model_type = Column(String(20), nullable=False)
    status = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=True)
    daily_tokens = Column(Integer, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    supplier = Column(String(50), nullable=False, default='openai')

    @classmethod
    def get_random_key(cls, session, model_type, supplier):

        if supplier == SUPPLIER_TYPE_OPENAI:
            default_key = hot_config.get_next_openai_api_key()
        else:
            default_key = hot_config.get_next_api_key()

        try:
            # Query the database for all keys matching the specified model_type and supplier
            keys = session.query(cls).filter(
                and_(cls.status == status_normal, cls.model_type == model_type, cls.supplier == supplier)
            ).all()

            if keys:
                # Return a random api_key
                return random.choice(keys).api_key
            else:
                return default_key
        except SQLAlchemyError as e:
            print(f"Database error: {str(e)}")
            return default_key
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return default_key

    @classmethod
    def update_total_tokens(cls, session, api_key, total_tokens):
        session.query(cls).filter_by(api_key=api_key).update({"total_tokens": total_tokens})
        session.commit()

    @classmethod
    def update_daily_tokens(cls, session, api_key, daily_tokens):
        session.query(cls).filter_by(api_key=api_key).update({"daily_tokens": daily_tokens})
        session.commit()