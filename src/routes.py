from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import Column, Integer, DateTime
from flask_cors import CORS
import app_core
from app_core import db, ma, app
import json 
import os
import datetime
import requests
from models import Company, CompanySchema, company_schema, companies_schema
from models import Employee, EmployeeSchema, employee_schema, employees_schema


def valid_company_structure(managerID, employeeID):
    
    print("============ Checking company structure ============")
    print ("manager: {};     employee: {};".format(managerID, employeeID))
    # the recursion has come to a loop
    if managerID == employeeID: 
        return False
    
    # the recursion has come to someone without a boss => there's no loop
    if managerID == None:
        return True

    # go up a level and check again
    return valid_company_structure(Employee.query.get(managerID).managerID, employeeID)
# =================================================================================== #
# ================================== C O M P A N Y ================================== #
# =================================================================================== #
@app.route("/companies", methods=['POST'])
def add_company():
    required = ['name']
    missing = app_core.check_missing_parameters(request, required)
    if len(missing) > 0:
        return jsonify({"HTTP Error": "Missing required parameter(s) " + str(missing) + "." }), 400
    name = request.json['name']
    new_company = Company(name)

    try:
        db.session.add(new_company)
        db.session.flush()
        sql_result = company_schema.dump(new_company)
        db.session.commit()
        return jsonify(sql_result), 200

    except Exception as e:
        return jsonify({"SQL ERROR: ": str(e)}), 400


# endpoint to show all lines
@app.route("/companies", methods=['GET'])
def get_companies():
    all_companies = Company.query.all()
    sql_result = companies_schema.dump(all_companies)
    return jsonify(sql_result), 200

@app.route("/companies/<id>", methods=['GET'])
def get_company_detail(id):
    company = Company.query.get(id)
    if company is None:
        return "Company not found", 404
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
    company_employees = Employee.query.filter(Employee.companyID==id)
    sql_result = employees_schema.dump(company_employees)
    return jsonify(sql_result), 200

# =================================================================================== #


# =================================================================================== #
# ================================== E M P L O Y E E ================================ #
# =================================================================================== #

@app.route("/employees", methods=['POST'])
def add_employee():
    required = ['name', 'email']

    missing = app_core.check_missing_parameters(request, required)
    if len(missing) > 0:
        return jsonify({"HTTP Error": "Missing required parameter(s) " + str(missing) + "." }), 400

    name = request.json['name']
    email = request.json['email']
    companyID = None if 'companyID' not in request.json else request.json['companyID']
    managerID = None if 'managerID' not in request.json else request.json['managerID']

    new_employee = Employee(name, email, companyID, managerID)

    try:
        db.session.add(new_employee)
        db.session.flush()
        sql_result = employee_schema.dump(new_employee)
        db.session.commit()
        return jsonify(sql_result), 200

    except Exception as e:
        db.session.rollback()
        db.session.flush()
        return jsonify({"SQL ERROR": str(e)}), 400

@app.route("/employees", methods=['GET'])
def get_employees():
    all_employees = Employee.query.all()
    sql_result = employees_schema.dump(all_employees)
    return jsonify(sql_result), 200

@app.route("/employees/filter", methods=['GET'])
def get_employee_by_name():
    name = request.args.get('name')
    filtered_employees = Company.query.filter(Company.name.like("%"+name+"%"))
    sql_result = employees_schema.dump(filtered_employees)
    if len(sql_result) == 0:
        return jsonify(sql_result), 404        
    return jsonify(sql_result), 200

@app.route("/employees/<id>", methods=['GET'])
def get_employee_detail(id):
    employee = Employee.query.get(id)
    if employee is None:
        return "Company not found", 404
    sql_result = employee_schema.dump(employee)
    return jsonify(sql_result), 200

@app.route("/employees/<id>", methods=["DELETE"])
def usuario_delete(id):
        employee = Employee.query.get(id)
        if employee == None:
            return jsonify({"SQL ERROR": "Employee to be deleted does not exist."}), 404

        try:
            db.session.delete(employee)
            db.session.commit()
            return employee_schema.jsonify(employee), 200
        except Exception as e:
            db.session.rollback()
            db.session.flush()
            return jsonify({"SQL ERROR": str(e)}), 400

@app.route("/employees/<id>", methods=["PUT"])
def employee_update(id):
        employee = Employee.query.get(id)
        if employee is not None:
            if 'name' in request.json:
                employee.name = request.json['name']

            if 'email' in request.json:
                employee.email = request.json['email']

            if 'companyID' in request.json:
                if get_company_detail(request.json['companyID'])[1] != 200:
                    return "No company found with ID " + str(request.json['companyID']) + " to associate employee.", 404
                employee.companyID = request.json['companyID']

            if 'managerID' in request.json:
                manager = Employee.query.get(request.json['managerID'])
                if manager == None:
                    return "No employee found with ID " + str(request.json['managerID']) + " to assign as manager.", 404
                if manager.companyID != employee.companyID:
                    return "Manager and subordinate can't work in different companies.", 400
                if not valid_company_structure(manager.employeeID, employee.employeeID):
                    return "Not possible to assign this management relationship (probably due to a structure loop, see 'Loops' in README for more information).", 400

            db.session.commit()

            return employee_schema.jsonify(employee)

        return None

# =================================================================================== #