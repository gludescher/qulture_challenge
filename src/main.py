from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import Column, Integer, DateTime
from flask_cors import CORS
import json 
import datetime
import requests
import time
import os
import sys
import atexit
from app_core import db, create_app

run_modes = {
    "debug": "DEBUG_MODE",
    "d": "DEBUG_MODE",
    "test": "TEST_MODE",
    "t": "TEST_MODE",
    "production": "PRODUCTION_MODE",
    "p": "PRODUCTION_MODE"
}

def fill_test_database():
    basedir = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(basedir, 'starting_companies.json')) as file:
        companies_json = json.load(file)
    with open(os.path.join(basedir, 'starting_employees.json')) as file:
        employees_json = json.load(file)
    companies = [Company(c['name']) for c in companies_json]
    employees = [Employee(e['name'], e['email'], e['companyID'] if 'companyID' in e else None, e['managerID'] if 'managerID' in e else None) for e in employees_json]
    db.session.add_all(companies)
    db.session.add_all(employees)
    db.session.commit()
    
def empty_test_database():
    # print("I have a bad feeling about this :c")
    db.session.remove()
    db.drop_all()


if len(sys.argv) > 1 and sys.argv[1].lower() in run_modes:
    run_mode = run_modes[sys.argv[1]]
else:
    run_mode = run_modes['debug']

if __name__ == '__main__':
    app, cors, ma = create_app(run_mode)
    from models import Company, Employee, update_manager_trigger
    import routes
    print (" Running Epic API - {} ".format(run_mode).center(90, "="))
    if run_mode == run_modes['debug']:
        db.create_all() 
        app.run(debug=True, port=5002)
    if run_mode == run_modes['test']:        
        db.create_all()
        routes.tear_down()
        routes.set_up()
        atexit.register(routes.empty_test_database)
        app.run(debug=True, port=5002)



