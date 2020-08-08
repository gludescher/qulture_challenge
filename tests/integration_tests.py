import os
from flask import Flask, request, jsonify
import json 
import datetime
import requests
import time
import pytest
from flask_testing import TestCase

# we need this here so the test script can find the dir from which to import aeh
import sys
sys.path.append("..")

from src.routes import api_error_handler as aeh


BASE_URL = "http://127.0.0.1:5002/"


@pytest.fixture(scope='module', autouse=True)
def setup_and_teardown(): 
    response = requests.post(BASE_URL + "/tests/teardown")
    response = requests.post(BASE_URL + "/tests/setup")    
    yield response
    
basedir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(basedir, 'starting_companies.json')) as file:
    base_companies = json.load(file)
with open(os.path.join(basedir, 'starting_employees.json')) as file:
    base_employees = json.load(file)


def test_get_companies():
    response = requests.get(BASE_URL + "/companies")
    companies = response.json()
    company_names = [c['name'] for c in companies]
    expected_company_names = [bc['name'] for bc in base_companies]
    assert company_names == expected_company_names


@pytest.mark.parametrize("companyID, expected_result", [
    (1, [be['name'] for be in base_employees if be['companyID'] == 1]),
    (2, [be['name'] for be in base_employees if be['companyID'] == 2])
])
def test_get_company_employees(companyID, expected_result):
    response = requests.get(BASE_URL + "/companies/"+ str(companyID) + "/employees")
    employees = response.json()
    employee_names = [e['name'] for e in employees]
    assert employee_names == expected_result
    
# Test with empty company
@pytest.mark.parametrize("companyID, expected_status, expected_json", [
    (3, 404, [])
])
def test_get_empty_company_employees(companyID, expected_status, expected_json):
    response = requests.get(BASE_URL + "/companies/"+ str(companyID) + "/employees")
    status = response.status_code
    assert status == expected_status and response.json() == expected_json


# Test with company that does not exist
@pytest.mark.parametrize("companyID, expected_status, expected_error", [
    (4, 404, aeh.SQL_NOT_FOUND)
])
def test_get_company_employees_error(companyID, expected_status, expected_error):
    response = requests.get(BASE_URL + "/companies/"+ str(companyID) + "/employees")
    status = response.status_code
    assert status == expected_status and response.json()['error']['error_code'] == expected_error


@pytest.mark.parametrize("employeeID, structure_level, expected_result", [
    (2, 0, ['Michael Scott', 'Andy Bernard']),
    (2, 1, ['Dwight Schrute', 'Pam Beesly', 'Angela Martin']),
    (2, 2, ['Jim Halpert', 'Stanley Hudson', 'Kevin Malone', 'Oscar Martinez']),
    (1, 3, ['Jim Halpert', 'Stanley Hudson', 'Kevin Malone', 'Oscar Martinez', 'Pete Miller', 'Toby Flenderson'])
])
def test_get_company_structure(employeeID, structure_level, expected_result):
    response = requests.get(BASE_URL + "/employees/" + str(employeeID) + "/structure/" + str(structure_level)) 
    employees = response.json()
    employee_names = [e['name'] for e in employees]
    assert employee_names == expected_result


@pytest.mark.parametrize("new_company, expected_result", [
    ({"name": base_companies[0]['name']}, 400),
    ({"name":"Qulture.Rocks"}, 200)
])
def test_insert_company(new_company, expected_result):
    response = requests.post(BASE_URL + "/companies", json=new_company)
    status = response.status_code
    assert status == expected_result


@pytest.mark.parametrize("new_employee, expected_result", [
    ({"name":"Gabe Lewis", "email":"jared_dunn@dm.com", "companyID":"1"}, 200),
    ({"name":"Jared Dunn", "email":"gabe_lewis@pp.com", "companyID":"2", "managerID":"15"}, 200)
])
def test_insert_employee(new_employee, expected_result):
    response = requests.post(BASE_URL + "/employees", json=new_employee)
    status = response.status_code
    assert status == expected_result


@pytest.mark.parametrize("new_employee, expected_status, expected_error", [
    ({"name":"Jim", "email":"beets_bears_battlestargallactica@dm.com", "companyID":"1"}, 400, aeh.SQL_CONSTRAINT_FAILED), # repeated email
    ({"name":"Russ Hanneman", "email":"brian@filming.crew", "companyID":"2", "managerID":"4"}, 400, aeh.API_NOT_SAME_COMPANY),
    ({"name":"Ryan Howard", "email":"kelly_i_love_you@dm.com", "companyID":"10"}, 400, aeh.SQL_NOT_FOUND)
])
def test_insert_employee_errors(new_employee, expected_status, expected_error):
    response = requests.post(BASE_URL + "/employees", json=new_employee)
    status = response.status_code
    error = response.json()['error']['error_code']
    assert status == expected_status and error == expected_error


@pytest.mark.parametrize("employeeID, employee_data, expected_status", [
    (4, {"name":"Pam Beesly Halpert", "email":"pamela_beehal@dm.com"}, 200), # married
    (13, {"managerID": 10}, 200), # changing boss
])
def test_edit_employee(employeeID, employee_data, expected_status): 
    response = requests.put(BASE_URL + "/employees/"+str(employeeID), json=employee_data)
    status = response.status_code    
    assert status == expected_status


@pytest.mark.parametrize("employeeID, employee_data, expected_status, expected_error", [
    (10, {"companyID": 10}, 404, aeh.SQL_NOT_FOUND),
    (5, {"managerID": 15}, 400, aeh.API_NOT_SAME_COMPANY),
    (2, {"managerID": 6}, 400, aeh.API_STRUCTURE_LOOP),
])
def test_edit_employee_errors(employeeID, employee_data, expected_status, expected_error): 
    response = requests.put(BASE_URL + "/employees/"+str(employeeID), json=employee_data)
    status = response.status_code
    error = response.json()['error']['error_code']
    assert status == expected_status and error == expected_error

@pytest.mark.parametrize("employeeID, expected_indirect", [
    (3, [6, 7]),
    (14, [])
])
def test_delete_employee(employeeID, expected_indirect):
    response = requests.delete(BASE_URL + "/employees/" + str(employeeID))
    status = response.status_code
    if 'indirect_changes' in response.json():
        indirect = response.json()['indirect_changes']['employees']
        indirectID = [i['employeeID'] for i in indirect]
        indirectID.sort()
    else:
        indirectID = []

    assert status == 200 and indirectID == expected_indirect

@pytest.mark.parametrize("employeeID, expected_status, expected_error", [
    (100, 404, aeh.SQL_NOT_FOUND)
])
def test_delete_employee_error(employeeID, expected_status, expected_error):
    response = requests.delete(BASE_URL + "/employees/" + str(employeeID))
    status = response.status_code
    error = response.json()['error']['error_code']
    assert status == expected_status and error == expected_error