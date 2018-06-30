#!/usr/bin/env python3

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from datetime import datetime
from passlib.apps import custom_app_context as pwd_context


Base = declarative_base()


class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)

    @property
    def serialize(self):
        return {
                'id': self.id,
                'name': self.name
                }

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    #username = Column(String(32), index=True)
    #password_hash = Column(String(64))
    name    = Column(String(250), nullable=False)
    email   = Column(String(250), nullable=False)
    picture = Column(String(250))


    #def hash_password(self, password):
        #self.password_hash = pwd_context.encrypt(password)

    #def verify_password(self, password):
        #return pwd_context.verify(password, self.password_hash)

    #def get_id(self):
        # returns the user e-mail
        #return unicode(self.id)





class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    title = Column(String(80), nullable=False)
    description = Column(String(1000))
    cat_id = Column(Integer, ForeignKey('category.id'))
    item = relationship(Category)
    datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)



    @property
    def serialize(self):
        return {
                'id': self.id,
                'title': self.title,
                'description': self.description,
                'cat_id': self.cat_id
            }



engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)
