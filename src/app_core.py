from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import Column, Integer, DateTime
from flask_cors import CORS
import json 
import os
import datetime
import requests


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
ma = Marshmallow(app)
db = SQLAlchemy()

def create_test_app(db_name='test.sqlite'):
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, db_name)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = 'False'
    db.init_app(app)
    app.app_context().push()
    return app


def create_production_app(db_name='epic.sqlite'):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, db_name)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = 'False'
    db.init_app(app)
    app.app_context().push()
    return app


def create_app(run_mode):
    global app
    global ma
    if run_mode == 'TEST_MODE':
        app = create_test_app()
    else:
        app = create_production_app()
    cors = CORS(app)
    ma = Marshmallow(app)
    return app, cors, ma

def check_missing_parameters(received, required):
    if request.json is None:
        return required
    missing = []
    for param in required:
        if param not in request.json:
            missing.append(param)
    return missing

