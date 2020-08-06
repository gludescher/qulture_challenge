from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import Column, Integer, DateTime, DDL, event
from flask_cors import CORS
import app_core
from app_core import db, ma, app
import json 
import os
import datetime
import requests

################################################## M O D E L ##################################################
class Employee(db.Model):
    __tablename__ = 'Employees'
    employeeID = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=False, nullable=False)
    email = db.Column(db.String(80), unique=True)
    companyID = db.Column(db.Integer, db.ForeignKey("Companies.companyID"))
    managerID = db.Column(db.Integer, db.ForeignKey("Employees.employeeID"))

    # self-referential relationship
    manager = db.relationship("Employee", backref='subordinates', remote_side=employeeID)

    def __init__(self, name, email, companyID=None, managerID=None):
        self.name = name
        self.email = email
        self.companyID = companyID
        self.managerID = managerID

# When a manager changes companies, its subordinates must be assigned other manager.
# The policy defined was to set as NULL, but could be easily be defined as the manager
# of the person that is leaving company. Also, if the moving employee's manager hasn't 
# changed, it must be set to NULL. If it has, the API takes care of validation.
update_manager_trigger = DDL('''\
        CREATE TRIGGER change_manager_after_update_companyID
            AFTER UPDATE OF companyID ON Employees
        BEGIN
            UPDATE Employees
            SET managerID = NULL
            WHERE (managerID = OLD.employeeID)
            OR (employeeID = NEW.employeeID AND NEW.managerID = OLD.managerID);
        END;'''
    )
event.listen(Employee.__table__, 'after_create', update_manager_trigger)

################################################## S C H E M A ##################################################
class EmployeeSchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = ('employeeID', 'name', 'email', 'companyID', 'managerID')

employee_schema = EmployeeSchema()
employees_schema = EmployeeSchema(many=True)


################################################## M O D E L ##################################################
class Company(db.Model):
    __tablename__ = 'Companies'
    companyID = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)

    employees = db.relationship("Employee", backref='company_employees')

    def __init__(self, name):
        self.name = name

################################################## S C H E M A ##################################################
class CompanySchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = ('companyID', 'name')

company_schema = CompanySchema()
companies_schema = CompanySchema(many=True)

