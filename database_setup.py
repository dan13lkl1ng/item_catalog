#!/usr/bin/env python3

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from datetime import datetime


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


class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    title = Column(String(80), nullable=False)
    description = Column(String(1000))
    cat_id = Column(Integer, ForeignKey('category.id'))
    item = relationship(Category)
    datetime = Column(DateTime, nullable=False, default=datetime.utcnow)



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
