from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, func, DateTime, BigInteger, ForeignKey

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True)
    lang_code = Column(String, nullable=False)
    lat = Column(String)
    long = Column(String)
    days = Column(Integer)
    active = Column(Boolean, default=True)
    last_touch = Column(DateTime, server_default=func.now())
    last_demand = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())

    messages = relationship("Message", back_populates="user", uselist=True)

    def __repr__(self):
        return "<User(id='{}', tg_id='{}', lat='{}', long={}, days={}, active={}, lang_code={}, last_touch)>" \
            .format(self.id, self.tg_id, self.lat, self.long, self.days, self.active, self.lang_code, self.last_touch)


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="messages")
    message_id = Column(BigInteger, nullable=False)

    created_at = Column(DateTime, server_default=func.now())
