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
from models import Employee, EmployeeSchema, employee_schema, employees_schema, update_manager_trigger
import api_error_handler as aeh
from api_error_handler import error_handler

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
        return error_handler(400, aeh.SQL_CONSTRAINT_FAILED, message=str(e))


# endpoint to show all lines
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
        return error_handler(404, aeh.SQL_NOT_FOUND, message_param='company')
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
        return error_handler(404, aeh.SQL_NOT_FOUND, message_param='company')
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
        return error_handler(400, aeh.HTTP_MISSING_PARAMS, message_param=missing)

    name = request.json['name']
    email = request.json['email']
    
    try:
        companyID = None if 'companyID' not in request.json else int(request.json['companyID'])
        managerID = None if 'managerID' not in request.json else int(request.json['managerID'])
    except:
        return error_handler(400, aeh.HTTP_PARAM_TYPE, message="Parameters 'companyID' and 'managerID' expect numeric input.")

    new_employee = Employee(name, email, companyID, managerID)

    if companyID is not None:
        company = Company.query.get(request.json['companyID'])
        if company is None:
            return error_handler(400, aeh.SQL_NOT_FOUND, message="No company found with ID " + str(request.json['companyID']) + " to associate employee.")
    
    if managerID is not None:
        manager = Employee.query.get(request.json['managerID'])
        if manager is None:
            return error_handler(400, aeh.SQL_NOT_FOUND, message="No employee found with ID " + str(request.json['managerID']) + " to assign as manager.")
        if manager.companyID != new_employee.companyID:
            print(" Manager Company: {};      Employee Company: {} ".format(type(manager.companyID), type(new_employee.companyID)).center(90, "="))    
            return error_handler(400, aeh.API_NOT_SAME_COMPANY)
        # There's no need to verify for loops since the employee is being created now, therefore has no subordinates.

    try:
        db.session.add(new_employee)
        db.session.flush()
        sql_result = employee_schema.dump(new_employee)
        db.session.commit()
        return jsonify(sql_result), 200

    except Exception as e:
        db.session.rollback()
        db.session.flush()
        return error_handler(400, aeh.SQL_CONSTRAINT_FAILED, message=str(e))


@app.route("/employees", methods=['GET'])
def get_employees():
    all_employees = Employee.query.all()
    sql_result = employees_schema.dump(all_employees)
    if len(sql_result) == 0:
        return jsonify(sql_result), 200
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
        return error_handler(404, aeh.SQL_NOT_FOUND, message_param='employee')
    sql_result = employee_schema.dump(employee)
    return jsonify(sql_result), 200


@app.route("/employees/<id>", methods=["DELETE"])
def usuario_delete(id):
    employee = Employee.query.get(id)
    if employee is None:
        return error_handler(404, aeh.SQL_NOT_FOUND, message='Employee to be deleted does not exist.')

    subordinates = get_employees_under([id], 1)
    subordinatesID = [s['employeeID'] for s in subordinates]
    try:
        changed_employees = get_indirect_changes(employee)
        sql_result = employee_schema.dump(employee)
        db.session.delete(employee)
        db.session.commit()
        if changed_employees is not None and len(changed_employees) > 0:
            return jsonify({
                    'employee':sql_result, 
                    'indirect_changes':{
                        'api_warning':'These employees were also changed to keep database consistency.',
                        'changes': 'Attribute managerID set to NULL.',
                        'employees':changed_employees }
                    }), 200

        return jsonify({'employee': sql_result, 'indirect_changes': indirect_changes}), 200

    except Exception as e:
        db.session.rollback()
        db.session.flush()
        return error_handler(400, aeh.SQL_CONSTRAINT_FAILED, message=str(e))


def get_indirect_changes(altered_object):
    if type(altered_object) == Company:
        indirect_changes = Employee.query.filter(Employee.companyID==altered_object.companyID).all()
    elif type(altered_object) == Employee:
        indirect_changes = Employee.query.filter(Employee.managerID==altered_object.employeeID).all()
    else:
        return None
    sql_result = employees_schema.dump(indirect_changes)
    return sql_result

@app.route("/employees/<id>", methods=["PUT"])
def employee_update(id):
    employee = Employee.query.get(id)
    if employee is None:
        return error_handler(404, aeh.SQL_NOT_FOUND, message="Employee with ID "+ str(id) +" not found. If you wish to create an employee, please use the POST request.")

    if 'name' in request.json:
        employee.name = request.json['name']

    if 'email' in request.json:
        employee.email = request.json['email']

    changed_employees = None
    if 'companyID' in request.json:
        if request.json['companyID'] == 0:
            employee.companyID = None
        else:
            company = Company.query.get(request.json['companyID'])
            if company is None:
                return error_handler(404, aeh.SQL_NOT_FOUND, message="No company found with ID " + str(request.json['companyID']) + " to associate employee.")
        if employee.companyID != request.json['companyID']:
            changed_employees = get_indirect_changes(employee)
        employee.companyID = request.json['companyID']

    if 'managerID' in request.json:
        if request.json['managerID'] == 0:
            employee.managerID = None
        else:
            manager = Employee.query.get(request.json['managerID'])
            if manager is None:
                return error_handler(404, aeh.SQL_NOT_FOUND, message="No employee found with ID " + str(request.json['managerID']) + " to assign as manager.")
            if manager.companyID != employee.companyID:
                return error_handler(400, aeh.API_NOT_SAME_COMPANY)
            if not valid_company_structure(manager.employeeID, employee.employeeID):
                return error_handler(400, aeh.API_STRUCTURE_LOOP)
        employee.managerID = request.json['managerID']

    # if all went right so far, commit to database
    try:    
        db.session.flush()
        db.session.commit()
        sql_result = employee_schema.dump(employee) 
    except Exception as e:
        return error_handler(400, aeh.SQL_CONSTRAINT_FAILED, message=str(e))

    if changed_employees is not None and len(changed_employees) > 0:
        return jsonify({
                'employee':sql_result, 
                'indirect_changes':{
                    'api_warning':'These employees were also changed to keep database consistency.',
                    'changes': 'Attribute managerID set to NULL.',
                    'employees':changed_employees }
                }), 200

    return employee_schema.jsonify(employee), 200



@app.route("/employees/<id>/structure/<level>", methods=['GET'])
def get_company_structure(id, level):
    try:
        level = int(level)
    except Exception as e:
        return error_handler(400, aeh.HTTP_PARAM_TYPE, message="Parameter 'level' expects numeric input.")

    employee = Employee.query.get(id)
    if employee is None:
        return error_handler(404, aeh.SQL_NOT_FOUND, message_param='employee')
    
    if level == 0:
        subordinates = Employee.query.filter(and_(Employee.managerID==employee.managerID, Employee.companyID == employee.companyID)).all()
        sql_result = employees_schema.dump(subordinates)
    else:
        sql_result = get_employees_under([id], int(level))
    if len(sql_result) == 0:
        return jsonify(sql_result), 404
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
