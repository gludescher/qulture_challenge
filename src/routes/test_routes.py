from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import Column, Integer, DateTime, and_
from flask_cors import CORS
import json 
import os
import datetime
import requests

from app.app_core import db, ma, app
import routes.api_error_handler as aeh
from routes.api_error_handler import error_handler, check_missing_parameters

from models.company_model import Company, CompanySchema, company_schema, companies_schema
from models.employee_model import Employee, EmployeeSchema, employee_schema, employees_schema, update_manager_trigger


def fill_test_database():
    basedir = os.path.abspath(os.path.dirname(__file__))
    project_dir = os.path.dirname(os.path.dirname(basedir)) # up two levels
    with open(os.path.join(project_dir, 'tests', 'starting_companies.json')) as file:
        companies_json = json.load(file)
    with open(os.path.join(project_dir, 'tests', 'starting_employees.json')) as file:
        employees_json = json.load(file)
    companies = [Company(c['name']) for c in companies_json]
    employees = [Employee(e['name'], e['email'], e['companyID'] if 'companyID' in e else None, e['managerID'] if 'managerID' in e else None) for e in employees_json]
    db.session.add_all(companies)
    db.session.add_all(employees)
    db.session.commit()

def empty_test_database():
    db.session.remove()
    db.drop_all()

@app.route("/tests/start", methods=['POST'])
def set_up():
    print("\n")
    print("Setting up database and stuff".center(80, "="))
    print("\n")
    db.create_all()
    fill_test_database()
    return "Database up and ready for testing!", 200

@app.route("/tests/end", methods=['POST'])
def tear_down():
    print("\n")
    print("Tearing down database and stuff".center(80, "="))
    print("\n")
    empty_test_database()
    return "Database destroyed!", 200
