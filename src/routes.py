from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import Column, Integer, DateTime, and_
from flask_cors import CORS
import app_core
from app_core import db
from app_core import db, ma, app
import json 
import os
import datetime
import requests
from models import Company, CompanySchema, company_schema, companies_schema
from models import Employee, EmployeeSchema, employee_schema, employees_schema

# app = create_production_app()

# Recursive function that goes up a company's structure, checking for possible 
# management loops when creating/editing an employee. 
# This logic relies on two basic rules:
#     - No employee can have more than one manager
#     - No employee can be assigned a manager that doesn't exist
def valid_company_structure(managerID, employeeID):
    print("============ Checking company structure ============")
    print ("manager: {};     employee: {};".format(managerID, employeeID))
    # the recursion has come to a loop
    if managerID == employeeID: 
        return False
    
    # the recursion has come to someone without a boss => there's no loop
    if managerID is None:
        return True

    # go up a level and check again
    return valid_company_structure(Employee.query.get(managerID).managerID, employeeID)

# Recursive function that returns the subordinates N levels 
# under the selected employee.
def get_employees_under(employees, level):
    print("\n\n")
    print("========= Getting Subordinates Level {} =========".format(level))
    print(employees)
    subordinates = Employee.query.filter(Employee.managerID.in_(employees)).all()
    sql_result = employees_schema.dump(subordinates)
    print(sql_result)
    print("================================================")
    level -= 1
    if level <= 0:
        return sql_result
    else:
        employees = [sub['employeeID'] for sub in sql_result]
    return(get_employees_under(employees, level))


# =================================================================================== #
# ================================== C O M P A N Y ================================== #
# =================================================================================== #
@app.route("/companies", methods=['POST'])
def add_company():
    required = ['name']
    missing = app_core.check_missing_parameters(request, required)
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
    company = Company.query.get(id)
    if company is None:
        return "Company not found", 404
    company_employees = Employee.query.filter(Employee.companyID==id)
    sql_result = employees_schema.dump(company_employees)
    if len(sql_result) == 0:
        return jsonify(sql_result), 404
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

    if companyID != None:
        company = Company.query.get(request.json['companyID'])
        if company is None:
            return jsonify({"SQL ERROR": "No company found with ID " + str(request.json['companyID']) + " to associate employee."}), 404
    
    if managerID != None:
        manager = Employee.query.get(request.json['managerID'])
        if manager is None:
            return jsonify({"SQL ERROR": "No employee found with ID " + str(request.json['managerID']) + " to assign as manager."}), 404
        if manager.companyID != employee.companyID:
            return jsonify({"API ERROR": "Manager and subordinate can't work in different companies."}), 400
        # There's no need to verify for loops since the employee is being created now.

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
        return jsonify({"SQL ERROR":"Employee not found"}), 404
    sql_result = employee_schema.dump(employee)
    return jsonify(sql_result), 200


@app.route("/employees/<id>", methods=["DELETE"])
def usuario_delete(id):
    employee = Employee.query.get(id)
    if employee is None:
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
            company = Company.query.get(request.json['companyID'])
            if company is None:
                return jsonify({"SQL ERROR":"No company found with ID " + str(request.json['companyID']) + " to associate employee."}), 404
            employee.companyID = request.json['companyID']

        if 'managerID' in request.json:
            manager = Employee.query.get(request.json['managerID'])
            if manager is None:
                return jsonify({"SQL ERROR": "No employee found with ID " + str(request.json['managerID']) + " to assign as manager."}), 404
            if manager.companyID != employee.companyID:
                return jsonify({"API ERROR": "Manager and subordinate can't work in different companies."}), 400
            if not valid_company_structure(manager.employeeID, employee.employeeID):
                return jsonify({"API ERROR": "Not possible to assign this management relationship (probably due to a structure loop, see 'Loops' in README for more information)."}), 400
            employee.managerID = request.json['managerID']

        # if all went right so far, commit to database
        try:    
            db.session.flush()
            db.session.commit() 
        except Exception as e:
            return jsonify({"SQL ERROR: ": str(e)}), 400

        return employee_schema.jsonify(employee), 200
    return jsonify({"SQL ERROR": "Employee with ID " + str(id) + " not found. If you wish to create an employee, please use the POST request." }), 404


@app.route("/employees/<id>/structure/<level>", methods=['GET'])
def get_company_structure(id, level):
    try:
        level = int(level)
    except Exception as e:
        return jsonify({"HTTP ERROR":"Parameter 'level' expects numeric input."}), 400

    employee = Employee.query.get(id)
    if employee is None:
        return jsonify({"SQL ERROR":"Employee not found"}), 404
    
    if level == 0:
        subordinates = Employee.query.filter(and_(Employee.managerID==employee.managerID, Employee.companyID == employee.companyID)).all()
        sql_result = employees_schema.dump(subordinates)
    else:
        sql_result = get_employees_under([id], int(level))
    return jsonify(sql_result), 200

# =================================================================================== #
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
