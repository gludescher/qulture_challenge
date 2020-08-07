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


# =================================================================================== #
# ================================== C O M P A N Y ================================== #
# =================================================================================== #
@app.route("/companies", methods=['POST'])
def add_company():
    required = ['name']
    missing = check_missing_parameters(request, required)
    if len(missing) > 0:
        return jsonify({"HTTP Error": "Missing required parameter(s) " + str(missing) + "."}), 400
    name = request.json['name']
    new_company = Company(name)

    try:
        db.session.add(new_company)
        db.session.flush()
        sql_result = company_schema.dump(new_company)
        db.session.commit()
        return jsonify(sql_result), 200

    except Exception as e:
        return error_handler(400, aeh.SQL_CONSTRAINT_FAILED, message=str(e))


@app.route("/companies", methods=['GET'])
def get_companies():
    all_companies = Company.query.all()
    sql_result = companies_schema.dump(all_companies)
    if len(sql_result) == 0:
        return jsonify(sql_result), 404
    return jsonify(sql_result), 200


@app.route("/companies/<id>", methods=['GET'])
def get_company_detail(id):
    company = Company.query.get(id)
    if company is None:
        return error_handler(404, aeh.SQL_NOT_FOUND, 'company')
    sql_result = company_schema.dump(company)
    return jsonify(sql_result), 200


@app.route("/companies/filter", methods=['GET'])
def get_company_by_name():
    name = request.args.get('name')
    filtered_companies = Company.query.filter(Company.name.like("%"+name+"%"))
    sql_result = companies_schema.dump(filtered_companies)
    if len(sql_result) == 0:
        return jsonify(sql_result), 404        
    return jsonify(sql_result), 200


@app.route("/companies/<id>/employees", methods=['GET'])
def get_company_employees(id):
    company = Company.query.get(id)
    if company is None:
        return error_handler(404, aeh.SQL_NOT_FOUND, 'company')
    company_employees = Employee.query.filter(Employee.companyID==id)
    sql_result = employees_schema.dump(company_employees)
    if len(sql_result) == 0:
        return jsonify(sql_result), 404
    return jsonify(sql_result), 200

# =================================================================================== #
