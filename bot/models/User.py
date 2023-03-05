from typing import Optional

from sqlalchemy import Column, Integer, String, Boolean, func, DateTime, BigInteger
from sqlalchemy.orm import relationship
from telegram.ext import ContextTypes

from bot.models.BaseModel import BaseModel


class User(BaseModel):
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

    async def get_user_html(self, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        tg_user = await context.bot.get_chat_member(self.tg_id, self.tg_id)
        if not tg_user.user:
            return None
        return tg_user.user.mention_html()

    async def get_user_name(self, context: ContextTypes.DEFAULT_TYPE) -> Optional[str]:
        tg_user = await context.bot.get_chat_member(self.tg_id, self.tg_id)
        if not tg_user.user:
            return None
        if not tg_user.user.username:
            return '%d: %s %s' % (self.id if self.id else -1, tg_user.user.first_name, tg_user.user.last_name)

        return '%d: %s %s (%s)' % (
            self.id if self.id else -1, tg_user.user.first_name, tg_user.user.last_name, tg_user.user.username)

    def __repr__(self):
        return self._repr(id=self.id, tg_id=self.tg_id, lang=self.lang_code)
