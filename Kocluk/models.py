from pyasn1.compat import integer
from datetime import datetime
from database import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, Index, func
from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy.ext.mutable import MutableDict   # tracks in-place changes



class Chat(Base):
    __tablename__ = 'chat'

    id = Column(Integer, primary_key=True, index=True)
    chat_title = Column(String)
    body_text = Column(Text)
    created_at = Column(DateTime(timezone=True),server_default=func.now())
    owner_id = Column(Integer, ForeignKey('users.id'))
    techniques = relationship(
        "Technique",
        back_populates="chat",
        cascade="all, delete-orphan",
    )


class Technique(Base):
    __tablename__ = 'technique'

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey('chat.id'))
    technique = Column(String)
    time = Column(Integer, nullable=True)
    explanation = Column(String)
    chat = relationship("Chat", back_populates="techniques")


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at  = Column(DateTime(timezone=True),server_default=func.now())
