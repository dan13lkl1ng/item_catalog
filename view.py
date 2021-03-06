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
from functools import wraps

# Blueprints
from api.api import api


CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"

engine = create_engine('sqlite:///catalog.db')

Base.metadata.bind = engine
session = scoped_session(sessionmaker(bind=engine))
app = Flask(__name__)

app.register_blueprint(api)


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state, CLIENT_ID=CLIENT_ID)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
        Gathers data from Google Sign In API and places it inside a session
        variable.
    """
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


@app.route('/gdisconnect', methods=['GET', 'POST'])
def gdisconnect():
    """
        Revokes OAuth Token from Google and deletes session.
    """
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user isn\'t connected.'),
                                 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Use HTTP GET request to revoke the current user's access token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' \
          % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    # check status of the response received in result
    if result['status'] == '200' or '400':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        return redirect(url_for('showLatestItems'))
    else:
        response = make_response(json.dumps('Failed to revoke token '
                                            'for a given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/')
def showLatestItems():
    """
        Renders template with categories and the latest items.
    """
    categories = session.query(Category).all()
    lastItems = session.query(Item).order_by(Item.id.desc()).limit(10).all()

    return render_template('index.html', lastItems=lastItems,
                           categories=categories,
                           title='Items Catalog',
                           loggedIn=loggedIn())


@app.route('/catalog/<int:cat_id>/items/')
def showItems(cat_id):
    """
        Renders template with items of a catgory.
        args:
        cat_id - ID of category
    """
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


def login_required(f):
    """ Decorator to guard routes. """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' in login_session:
            return f(*args, **kwargs)
        else:
            flash("You are not allowed to access there")
            return redirect('/login')
    return decorated_function


@app.route('/item/new/', methods=['GET', 'POST'])
@login_required
def newItem():
    """
        Creates new item if logged in, otherwise redirects to list of latest
        items.
    """
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
    """
        Renders template with description of a specific item.

        args:
        cat_id - ID of category
        item_id - ID of item
    """
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
@login_required
def deleteItem(item_id):
    """
        Deletes selected item.

        args:
        item_id  - ID of selected item to delete
    """
    itemToDelete = session.query(Item).filter_by(id=item_id).one()

    if itemToDelete.user_id != login_session['user_id']:
        flash('You are not the owner of this item!')
        return redirect(url_for('showLatestItems'))

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
@login_required
def editItem(item_id):
    """
        Renders template to edit item.

        args:
        item_id - ID of item to edit
    """
    item = session.query(Item).filter_by(id=item_id).one_or_none()

    if item.user_id != login_session['user_id']:
        flash('You are not the owner of this item')
        return redirect(url_for('showLatestItems'))

    if item.user_id == login_session['user_id']:
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
    else:
        return jsonify({"error": "You are not authorized to perform such.\
                        operation because you are not the creator of the.\
                        item"})


def getUserInfo(user_id):
    """
        Get user by ID.

        args:
        user_id - ID of logged in user

        returns:
        user
    """
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    """
        Creates new user from data in session, which is given by login
        into Google.

        args:
        login_session - session should have username, email und picture

        returns:
        user.id - ID of created user
    """
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
    # Set this to False in production
    app.run(host='0.0.0.0', port=5000)
