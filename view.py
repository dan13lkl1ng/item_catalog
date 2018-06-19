#!/usr/bin/env python3

from flask import Flask, jsonify, request, url_for, abort, g, render_template, flash, redirect

from database_setup import Base, Category, Item , User#, Bagel
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


@auth.verify_password
def verify_password(username, password):
    print( "Looking for user %s" % username)
    user = session.query(User).filter_by(username = username).first()
    if not user: 
        print("User not found")
        return False
    elif not user.verify_password(password):
        print("Unable to verfy password")
        return False
    else:
        g.user = user
        return True


@app.route('/')
def showLatestItems():
    #lastItems = session.query.order_by('-id').first()


    categories = session.query(Category).all()

    lastItems = session.query(Item).order_by(Item.id.desc()).limit(10).all()


    return render_template('index.html', lastItems = lastItems, categories = categories, logged_in = True if g.user else False )


@app.route('/item/new/', methods=['GET','POST'])
@auth.login_required
def newItem():
    categories = session.query(Category).all()
    #categories = Category.query.all()
    if request.method == 'POST':
        newItem = Item(title = request.form['title'], cat_id = request.form['category'], description=request.form['description'], datetime = datetime.now(), user_id = g.user.id)
        session.add(newItem)
        session.commit()
        flash("New Item Created!")
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
@auth.login_required
def editItem(item_id):
    item = session.query(Item).filter_by(id=item_id).filter_by(user_id=g.user.id).one()
    categories = session.query(Category).all()
    if request.method =='POST':
        #editedItem = Item(

        #session.execute(update(Item).where(id==item_id).values(title='lorem'))
        #session.commit()
        session.query(Item).\
            filter(Item.id == item_id).\
            update({"title": request.form['title'],\
            "description": request.form['description'],\
            "cat_id": request.form['category'],\
            "user_id": g.user.id})
        session.commit()

        return redirect(url_for('showLatestItems'))
    else:
        return render_template('edit_item.html', item = item, categories = categories)


@app.route('/catalog/<int:item_id>/delete/', methods=['GET','POST']) 
@auth.login_required
def deleteItem(item_id):
    itemToDelete = session.query(Item).filter_by(id=item_id).filter_by(user_id=g.user.id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash("Item deleted")
        return redirect(url_for('showLatestItems'))
    else:
        return render_template('deleteItem.html', item=itemToDelete)


@app.route('/users', methods = ['POST'])
def new_user():

    username = request.json.get('username')
    print(username)
    password = request.json.get('password')
    if username is None or password is None:
        print("missing arguments")
        abort(400) 
        
    if session.query(User).filter_by(username = username).first() is not None:
        print("existing user")
        user = session.query(User).filter_by(username=username).first()
        return jsonify({'message':'user already exists'}), 200#, {'Location': url_for('get_user', id = user.id, _external = True)}
        
    user = User(username = username)
    user.hash_password(password)
    session.add(user)
    session.commit()
    return jsonify({'username': user.username }), 201#, {'Location': url_for('get_user', id = user.id, _external = True)}


@app.route('/users/<int:id>')
@auth.login_required
def get_user(id):
    user = session.query(User).filter_by(id=id).one()
    if not user:
        abort(400)
    return jsonify({'username': user.username})


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.debug = True
    app.run(host='0.0.0.0', port=5001)
