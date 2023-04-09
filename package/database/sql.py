from init import *

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True

    @classmethod
    def create(cls, session, **kwargs):
        instance = cls(**kwargs)
        session.add(instance)
        session.commit()
        return instance

    @classmethod
    def delete(cls, session, **kwargs):
        instance = cls.query(session, **kwargs)
        if instance:
            session.delete(instance)
            session.commit()

    @classmethod
    def update(cls, session, conditions, updates):
        session.query(cls).filter_by(**conditions).update(updates)
        session.commit()

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