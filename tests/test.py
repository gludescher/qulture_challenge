import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import Column, Integer, DateTime
from flask_cors import CORS
import json 
import datetime
import requests
import time
import pytest
from flask_testing import TestCase
from app_core import db, create_test_app
from models import Company, Employee
import routes

basedir = os.path.abspath(os.path.dirname(__file__))
# BASE_URL = "http://127.0.0.1:5000"

class MyTest(TestCase):
    
    def create_app(self):
        app = create_test_app()
        return create_test_app()

    def setUp(self):
        db.create_all()
        with open('starting_companies.json') as file:
            companies_json = json.load(file)
        with open('starting_employees.json') as file:
            employees_json = json.load(file)
        companies = [Company(c['name']) for c in companies_json]
        employees = [Employee(e['name'], e['email'], e['companyID'] if 'companyID' in e else None, e['managerID'] if 'managerID' in e else None) for e in employees_json]
        db.session.add_all(companies)
        db.session.add_all(employees)
        db.session.commit()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()

t = MyTest()
app = t.create_app().test_client()
try:
    t.setUp()
except:
    t.tearDown()


# @pytest.mark.parametrize("new_company, expected_result", [
#     (Company("Dunder-Mifflin"), True),
#     (Company("Pied Piper"), False),
#     (Company("Qulture.Rocks"), True)
# ])
# def test_get_companies():
#     resp = app.get('/companies')
#     companies = resp.json()
#     assert len(companies) == 2

        

# t.tearDown()
