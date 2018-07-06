from database_setup import Base, Category, Item
from flask import Blueprint
from flask import jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import json

api = Blueprint('api', 'api', url_prefix='/api')
CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog App"

engine = create_engine('sqlite:///catalog.db')

Base.metadata.bind = engine
session = scoped_session(sessionmaker(bind=engine))


@api.route('/categories')
def categoriesJSON():
    """ Returns categories. """
    categories = session.query(Category).all()
    return jsonify(categories=[c.serialize for c in categories])


@api.route('/categories/<int:cat_id>/')
def categoryJSON(cat_id):
    """ Returns items of a specific category. """
    items = session.query(Item).filter(Item.cat_id == cat_id).all()
    return jsonify(category_items=[c.serialize for c in items])


@api.route('/categories/<int:cat_id>/item/<int:id>/')
def songJSON(cat_id, id):
    """ Returns description of a specific item. """
    item = session.query(Item).filter(Item.id == id).one()
    return jsonify(item=item.serialize)
