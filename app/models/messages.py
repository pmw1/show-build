"""Inter-user messaging models."""
from sqlalchemy import Column, BigInteger, Integer, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class UserMessage(Base):
    """A direct or broadcast message between users.

    Created by g011_user_messaging migration. The route is identified by
    `to_user_id`: NULL means broadcast (admin-only at the API layer).
    """
    __tablename__ = "user_messages"

    id = Column(BigInteger, primary_key=True, index=True)

    from_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    to_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)

    content = Column(Text, nullable=False)

    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)

    reply_to = Column(BigInteger, ForeignKey("user_messages.id", ondelete="SET NULL"), nullable=True)

    sender = relationship("User", foreign_keys=[from_user_id])
    recipient = relationship("User", foreign_keys=[to_user_id])
    parent = relationship("UserMessage", remote_side=[id])

    def __repr__(self):
        return f"<UserMessage id={self.id} {self.from_user_id}->{self.to_user_id}>"
