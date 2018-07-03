# Item Catalog App
Made during Google Scholarship of Full Stack Web Developer Nanodegree Program at Udacity - 2018

This project sets up a sqlite database for an item catalog app. The provided Python script uses the sqlalchemy library to query the database.
## Requirements
1. Python2
2. sqlite
3. python-sqlalchemy
4. flask
5. NPM

## Getting started
1. Clone repository:
```
$ git clone git@github.com:dan13lkl1ng/item_catalog.git
```
2. Create Sqlite-Database
```
$ cd item_catalog
$ touch catalog.db
$ python database_setup.py
$ python lotsOfItems.py
```
3. Solve NPM Dependencies
```
$ cd static
$ npm i
```
4. Get Credentials from Google Oauth and save as ```client_secret.json```
5. Start server
```
$ cd ..
$ python view.py 
```
## Built with
* Bootstrap Material Design
* Flask

## Third Party Dependencies
* Google OAuth

## Issues
* Not secured against XSS
