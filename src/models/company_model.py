from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import Column, Integer, DateTime, DDL, event
from flask_cors import CORS
import json 
import os
import datetime
import requests

from app.app_core import db, ma

# ======================================= M O D E L ======================================== #
class Company(db.Model):
    __tablename__ = 'Companies'
    companyID = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)

    employees = db.relationship("Employee", backref='company_employees')

    def __init__(self, name):
        self.name = name
# ========================================================================================== #


# ====================================== S C H E M A ======================================= #
class CompanySchema(ma.Schema):
    class Meta:
        # Fields to expose
        fields = ('companyID', 'name')

company_schema = CompanySchema()
companies_schema = CompanySchema(many=True)
# ========================================================================================== #
