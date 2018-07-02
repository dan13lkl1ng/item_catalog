#!/usr/bin/env python2

from database_setup import Base, Category, Item, User
from datetime import datetime
from flask import Flask, url_for, render_template, redirect, request, flash
from flask import make_response, jsonify
from flask import session as login_session
from oauth2client.client import FlowExchangeError
from oauth2client.client import flow_from_clientsecrets
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import httplib2
import json
import random
import requests
import string
from sqlalchemy.orm.exc import NoResultFound

CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"

engine = create_engine('sqlite:///catalog.db')

Base.metadata.bind = engine
session = scoped_session(sessionmaker(bind=engine))
app = Flask(__name__)


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
                   'Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # see if user exists, of it doesn't make a new one
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;".\
              "-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


@app.route("/gdisconnect")
def gdisconnect():
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps('Current user not connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        # return response
    return redirect(url_for('showLatestItems'))
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's session.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        # return response
    return redirect(url_for('showLatestItems'))


@app.route('/')
def showLatestItems():
    categories = session.query(Category).all()
    lastItems = session.query(Item).order_by(Item.id.desc()).limit(10).all()

    return render_template('index.html', lastItems=lastItems,
                           categories=categories,
                           title='Items Catalog',
                           loggedIn=loggedIn())


@app.route('/catalog/<int:cat_id>/items/')
def showItems(cat_id):
    selectedCategory = session.query(Category).filter_by(id=cat_id).one()
    categories = session.query(Category).all()
    items = session.query(Item).filter_by(cat_id=cat_id).all()
    number = session.query(Item).filter_by(cat_id=cat_id).count()
    return render_template('items.html',
                           categories=categories,
                           selectedCategory=selectedCategory,
                           items=items,
                           number=number,
                           loggedIn=loggedIn())


@app.route('/item/new/', methods=['GET', 'POST'])
def newItem():
    categories = session.query(Category).all()
    if request.method == 'POST':
        newItem = Item(title=request.form['title'],
                       cat_id=request.form['category'],
                       description=request.form['description'],
                       datetime=datetime.now(),
                       user_id=login_session['user_id'])

        session.add(newItem)
        session.commit()
        flash("New Item Created!")
        return redirect(url_for('showLatestItems'))
    elif loggedIn() is True:
        return render_template('newItem.html', categories=categories,
                               loggedIn=loggedIn())
    else:
        return redirect(url_for('showLatestItems'))


def loggedIn():
    """
    Checks if user is logged in.

    Returns:
        True if user is logged in
        False if user is not logged in
    """
    if 'username' in login_session:
        return True
    else:
        return False


@app.route('/catalog/<int:cat_id>/<int:item_id>/')
def showDescription(item_id, cat_id):

    item = session.query(Item).filter_by(id=item_id).one()
    return render_template('showDescription.html',
                           item=item,
                           loggedIn=loggedIn())


def getUserID(email):
    """Searches for and returns id for given email address."""
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except NoResultFound:
        return None


@app.route('/catalog/<int:item_id>/delete/', methods=['GET', 'POST'])
def deleteItem(item_id):
    itemToDelete = session.query(Item).filter_by(id=item_id).\
            filter_by(user_id=login_session['user_id']).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash("Item deleted")
        return redirect(url_for('showLatestItems'))
    else:
        return render_template('deleteItem.html',
                               item=itemToDelete,
                               loggedIn=loggedIn())


@app.route('/catalog/<int:item_id>/edit/', methods=['GET', 'POST'])
def editItem(item_id):
    item = session.query(Item).filter_by(id=item_id).\
           filter_by(user_id=login_session['user_id']).one()
    categories = session.query(Category).all()
    if request.method == 'POST':
        session.query(Item).\
            filter(Item.id == item_id).\
            update({"title": request.form['title'],
                    "description": request.form['description'],
                    "cat_id": request.form['category'],
                    "user_id": login_session['user_id']})
        session.commit()

        return redirect(url_for('showLatestItems'))
    else:
        return render_template('edit_item.html',
                               item=item,
                               categories=categories,
                               loggedIn=loggedIn())


@app.route('/api/categories')
def categoriesJSON():
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])


@app.route('/api/categories/<int:cat_id>/')
def categoryJSON(cat_id):
    items = session.query(Item).filter(Item.cat_id == cat_id).all()
    return jsonify(category_items=[c.serialize for c in items])


@app.route('/api/categories/<int:cat_id>/item/<int:id>/')
def songJSON(cat_id, id):
    item = session.query(Item).filter(Item.id == id).one()
    return jsonify(item=item.serialize)


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


"""
Code in this section only runs when program is executed
directly.
"""
if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
