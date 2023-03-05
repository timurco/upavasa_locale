from sqlalchemy import Column, Integer, String, func, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import relationship

from bot.models.BaseModel import BaseModel


class Message(BaseModel):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)

    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="messages")
    message_id = Column(BigInteger, nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        # easy to override, and it'll honor __repr__ in foreign relationships
        return self._repr(id=self.id, type=self.type, user=self.user, message_id=self.message_id, created_at=self.created_at)
