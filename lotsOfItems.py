#!/usr/bin/env python2
# This Python file uses the following encoding: utf-8
import os, sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
 
from database_setup import Category, Item, Base
 
engine = create_engine('sqlite:///catalog.db')

Base.metadata.bind = engine
 
DBSession = sessionmaker(bind=engine)

session = DBSession()



category1 = Category(name="Baseball")
category2 = Category(name="Soccer")
category3 = Category(name="Darts")
category4 = Category(name="Tennis")

session.add(category1)
session.add(category2)
session.add(category3)
session.add(category4)
session.commit()

item1 = Item(title = "Baseball", description = "A baseball is a ball used in the sport of the same name. The ball features a rubber or cork center, wrapped in yarn, and covered, in the words of the Official Baseball Rules ", cat_id = 1, user_id = 1)

item2 = Item(title="Baseball Field", description="A baseball field, also called a ball field, sandlot or a baseball diamond, is the field upon which the game of baseball is played. The term can also be used as a metonym for a baseball park.", cat_id = 1, user_id = 1)

item3 = Item(title="Baseball Glove", description = "A baseball glove or mitt is a large leather glove worn by baseball players of the defending team, which assists players in catching and fielding balls hit by a batter or thrown by a teammate.", cat_id = 1, user_id = 2)

item4 = Item(title ="Baseball bat", description = "A baseball bat is a smooth wooden or metal club used in the sport of baseball to hit the ball after it is thrown by the pitcher. By regulation it may be no more than 2.75 inches (70 mm) in diameter at the thickest part and no more than 42 inches (1,100 mm) long. Although historically bats approaching 3 pounds (1.4 kg) were swung,[1] today bats of 33 ounces (0.94 kg) are common, topping out at 34 ounces (0.96 kg) to 36 ounces (1.0 kg)", cat_id = 1, user_id = 1)

item5 = Item(title="Football", description ="A football, soccer ball, or association football ball is the ball used in the sport of association football. The name of the ball varies according to whether the sport is called \"football\", \"soccer\", or \"association football\". The ball's spherical shape, as well as its size, weight, and material composition, are specified by Law 2 of the Laws of the Game maintained by the International Football Association Board. Additional, more stringent, standards are specified by FIFA and subordinate governing bodies for the balls used in the competitions they sanction.", cat_id = 2, user_id = 1)

item6 = Item(title="Tennis ball", description ="A tennis ball is a ball designed for the sport of tennis. Tennis balls are fluorescent yellow at major sporting events,[1][2] but in recreational play can be virtually any color. Tennis balls are covered in a fibrous felt which modifies their aerodynamic properties, and each has a white curvilinear oval covering it.", cat_id = 4, user_id = 3)

item7 = Item(title="Tennis racket", description="A racket or racquet[1] is a sports implement consisting of a handled frame with an open hoop across which a network of strings or catgut is stretched tightly. It is used for striking a ball or shuttlecock in games such as squash, tennis, racquetball, and badminton.", cat_id = 4, user_id = 1)

session.add(item1)
session.add(item2)
session.add(item3)
session.add(item4)
session.add(item5)
session.add(item6)
session.add(item7)
session.commit()

print 'added menu items!'
