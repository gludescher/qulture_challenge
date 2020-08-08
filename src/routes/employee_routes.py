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


# Recursive function that goes up a company's structure, checking for possible 
# management loops when creating/editing an employee. 
# This logic relies on two basic rules:
#     - No employee can have more than one manager
#     - No employee can be assigned a manager that doesn't exist
def valid_company_structure(managerID, employeeID):
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
    subordinates = Employee.query.filter(Employee.managerID.in_(employees)).all()
    sql_result = employees_schema.dump(subordinates)
    level -= 1
    if level <= 0:
        return sql_result
    else:
        employees = [sub['employeeID'] for sub in sql_result]
    return(get_employees_under(employees, level))

# Returns indirect changes when an object is altered.
# Although deleting a compnay is yet to be implemented, this
# function is ready to report the indirect changes to that.
def get_indirect_changes(altered_object):
    if type(altered_object) == Company:
        indirect_changes = Employee.query.filter(Employee.companyID==altered_object.companyID).all()
    elif type(altered_object) == Employee:
        indirect_changes = Employee.query.filter(Employee.managerID==altered_object.employeeID)
    else:
        return None
    sql_result = employees_schema.dump(indirect_changes)
    return sql_result


# =================================================================================== #
# ================================== E M P L O Y E E ================================ #
# =================================================================================== #

@app.route("/employees", methods=['POST'])
def add_employee():
    required = ['name', 'email']

    missing = check_missing_parameters(request, required)
    if len(missing) > 0:
        return error_handler(400, aeh.HTTP_MISSING_PARAMS, missing)

    name = request.json['name']
    email = request.json['email']
    
    try:
        companyID = None if 'companyID' not in request.json else int(request.json['companyID'])
        managerID = None if 'managerID' not in request.json else int(request.json['managerID'])
    except:
        return error_handler(400, aeh.HTTP_PARAM_TYPE, ['companyID', 'managerID'], 'numeric')

    new_employee = Employee(name, email, companyID, managerID)

    if companyID is not None:
        company = Company.query.get(request.json['companyID'])
        if company is None:
            return error_handler(400, aeh.SQL_NOT_FOUND, request.json['companyID'], message=aeh.NO_COMPANY_TO_ASSOCIATE)
    
    if managerID is not None:
        manager = Employee.query.get(request.json['managerID'])
        if manager is None:
            return error_handler(400, aeh.SQL_NOT_FOUND, request.json['managerID'], message=aeh.NO_EMPLOYEE_TO_ASSIGN)
        if manager.companyID != new_employee.companyID:
            return error_handler(400, aeh.API_NOT_SAME_COMPANY, manager.companyID, new_employee.companyID)
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


@app.route("/employees/search", methods=['GET'])
def get_employee_by_name():
    name = request.args.get('name')
    if name is None:
        return get_employees()
    filtered_employees = Employee.query.filter(Employee.name.like("%{}%".format(name)))
    sql_result = employees_schema.dump(filtered_employees)
    if len(sql_result) == 0:
        return jsonify(sql_result), 404        
    return jsonify(sql_result), 200


@app.route("/employees/<id>", methods=['GET'])
def get_employee_detail(id):
    employee = Employee.query.get(id)
    if employee is None:
        return error_handler(404, aeh.SQL_NOT_FOUND, 'employee')
    sql_result = employee_schema.dump(employee)
    return jsonify(sql_result), 200


@app.route("/employees/<id>", methods=["DELETE"])
def usuario_delete(id):
    employee = Employee.query.get(id)
    if employee is None:
        return error_handler(404, aeh.SQL_NOT_FOUND, id, message=aeh.NO_EMPLOYEE_TO_DELETE)

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
                        'changes': "Attribute 'managerID' set to NULL.",
                        'employees':changed_employees }
                    }), 200

        return jsonify(sql_result), 200

    except Exception as e:
        db.session.rollback()
        db.session.flush()
        return error_handler(400, aeh.SQL_CONSTRAINT_FAILED, message=str(e))


@app.route("/employees/<id>", methods=["PUT"])
def employee_update(id):
    employee = Employee.query.get(id)
    if employee is None:
        return error_handler(404, aeh.SQL_NOT_FOUND, id, message=aeh.NO_EMPLOYEE_TO_EDIT)

    try:
        companyID = None if 'companyID' not in request.json or request.json['companyID'] is None else int(request.json['companyID'])
        managerID = None if 'managerID' not in request.json or request.json['managerID'] is None else int(request.json['managerID'])
    except:
        return error_handler(400, aeh.HTTP_PARAM_TYPE, ['companyID', 'managerID'], 'numeric')

    if 'name' in request.json:
        employee.name = request.json['name']

    if 'email' in request.json:
        employee.email = request.json['email']

    changed_employees = None
    if 'companyID' in request.json:
        if companyID is not None:
            company = Company.query.get(companyID)
            if company is None:
                return error_handler(404, aeh.SQL_NOT_FOUND, companyID, message=aeh.NO_COMPANY_TO_ASSOCIATE)
        if employee.companyID != companyID:
            changed_employees = get_indirect_changes(employee)
        employee.companyID = companyID

    if 'managerID' in request.json:
        if managerID is not None:
            manager = Employee.query.get(request.json['managerID'])
            if manager is None:
                return error_handler(404, aeh.SQL_NOT_FOUND, request.json['managerID'], message=aeh.NO_EMPLOYEE_TO_ASSIGN)
            if manager.companyID != employee.companyID:
                return error_handler(400, aeh.API_NOT_SAME_COMPANY, manager.companyID, employee.companyID)
            if not valid_company_structure(manager.employeeID, employee.employeeID):
                return error_handler(400, aeh.API_STRUCTURE_LOOP)
        employee.managerID = managerID

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
        return error_handler(400, aeh.HTTP_PARAM_TYPE, "'level'", 'numeric')

    employee = Employee.query.get(id)
    if employee is None:
        return error_handler(404, aeh.SQL_NOT_FOUND, 'employee')
    
    if level <= 0:
        subordinates = Employee.query.filter(and_(Employee.managerID==employee.managerID, Employee.companyID == employee.companyID)).all()
        sql_result = employees_schema.dump(subordinates)
    else:
        sql_result = get_employees_under([id], int(level))
    if len(sql_result) == 0:
        return jsonify(sql_result), 404
    return jsonify(sql_result), 200

# =================================================================================== #

