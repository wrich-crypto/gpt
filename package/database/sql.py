from init import *
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True

    @classmethod
    def create(cls, session, **kwargs):
        try:
            instance = cls(**kwargs)
            session.add(instance)
            session.commit()
            return instance, None
        except SQLAlchemyError as e:
            session.rollback()
            return None, str(e)
        except Exception as e:
            session.rollback()
            return None, str(e)

    @classmethod
    def delete(cls, session, **kwargs):
        try:
            instance = cls.query(session, **kwargs)
            if instance:
                session.delete(instance)
                session.commit()
            return True, None
        except SQLAlchemyError as e:
            session.rollback()
            return False, str(e)
        except Exception as e:
            session.rollback()
            return False, str(e)


    @classmethod
    def update(cls, session, conditions, updates):
        try:
            session.query(cls).filter_by(**conditions).update(updates)
            session.commit()
            return True, None
        except SQLAlchemyError as e:
            session.rollback()
            return False, str(e)
        except Exception as e:
            session.rollback()
            return False, str(e)

    @classmethod
    def query(cls, session, **kwargs):
        return session.query(cls).filter_by(**kwargs).first()

    @classmethod
    def query_all(cls, session):
        return session.query(cls).all()

    @classmethod
    def exists(cls, session, **kwargs):
        return session.query(cls).filter_by(**kwargs).first() is not None

    @classmethod
    def count(cls, session, **kwargs):
        return session.query(cls).filter_by(**kwargs).count()