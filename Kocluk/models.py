from pyasn1.compat import integer
from database import Base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.mutable import MutableDict   # tracks in-place changes


class DersKocluk(Base):
    __tablename__ = 'DersKocluk'

    id = Column(Integer, primary_key=True, index=True)
    ders_kocluk_title = Column(String)
    description = Column(String)
    KeptData = Column(MutableDict.as_mutable(JSON)) #AI'dan dönen veriden tutulan veri
    owner_id = Column(Integer, ForeignKey('users.id'))


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)