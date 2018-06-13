#!/usr/bin/env python3

from flask import Flask, jsonify, request, url_for, abort, g, render_template, flash, redirect

from database_setup import Base, Category, Item #, User, Bagel
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session, lazyload, joinedload
from sqlalchemy import create_engine
#from flask.ext.httpauth import HTTPBasicAuth
from flask_httpauth import HTTPBasicAuth
from datetime import datetime

auth = HTTPBasicAuth() 


engine = create_engine('sqlite:///catalog.db')

Base.metadata.bind = engine
session = scoped_session(sessionmaker(bind=engine))
app = Flask(__name__)

@app.route('/')
def  showLatestItems():
    #lastItems = session.query.order_by('-id').first()
    #
    #bla = session.query(Category).options(lazyload(Item)).all()


    categories = session.query(Category).all()

    lastItems = session.query(Item).order_by(Item.id.desc()).limit(10).all()

    return render_template('index.html', lastItems = lastItems, categories = categories)


@app.route('/item/new/', methods=['GET','POST'])
def newItem():
    categories = session.query(Category).all()
    #categories = Category.query.all()
    if request.method == 'POST':
        newItem = Item(title = request.form['title'], cat_id = request.form['category'], description=request.form['description'], datetime = datetime.now())
        session.add(newItem)
        session.commit()
        #flash("new item created!")
        return redirect(url_for('showLatestItems'))
    else:
        return render_template('newItem.html', categories = categories)


@app.route('/catalog/<int:cat_id>/<int:item_id>/')
def showDescription(item_id, cat_id):
    item = session.query(Item).filter_by(id=item_id).one()
    return render_template('showDescription.html', item = item)


@app.route('/catalog/<int:cat_id>/items/')
def showItems(cat_id):
    selectedCategory = session.query(Category).filter_by(id=cat_id).one()
    categories = session.query(Category).all()
    items = session.query(Item).filter_by(cat_id=cat_id).all()
    number = session.query(Item).filter_by(cat_id=cat_id).count()
    return render_template('items.html', categories = categories, selectedCategory = selectedCategory, items = items, number = number )


@app.route('/catalog/<int:item_id>/edit/', methods=['GET','POST'])
def editItem(item_id):
    item = session.query(Item).filter_by(id=item_id).one()
    categories = session.query(Category).all()
    if request.method =='POST':
        #editedItem = Item(


        #session.execute(update(Item).where(id==item_id).values(title='lorem'))
        #session.commit()
        session.query(Item).\
            filter(Item.id == item_id).\
            update({"title": request.form['title'],\
            "description": request.form['description'],\
            "cat_id": request.form['category']})
        session.commit()

        return redirect(url_for('showLatestItems'))
    else:
        return render_template('edit_item.html', item = item, categories = categories)



if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.debug = True
    app.run(host='0.0.0.0', port=5001)
