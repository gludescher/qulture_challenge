import os
from flask import Flask, request, jsonify
import json 
import datetime
import requests
import time
import pytest
import routes
from flask_testing import TestCase
from main import db

BASE_URL = "http://127.0.0.1:5002/"

# time.sleep(5)

@pytest.fixture(scope='module', autouse=True)
def setup_and_teardown(): 
    response = requests.post(BASE_URL + "/tests/end")
    response = requests.post(BASE_URL + "/tests/start")    
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
    response = requests.get(BASE_URL + "/companies/"+ str(companyID) + "/employees") #pied piper
    employees = response.json()
    employee_names = [e['name'] for e in employees]
    assert employee_names == expected_result
    

@pytest.mark.parametrize("companyID, expected_result", [
    (3, 404),
    (4, 404)
])
def test_get_company_employees_error(companyID, expected_result):
    response = requests.get(BASE_URL + "/companies/"+ str(companyID) + "/employees") #pied piper
    status = response.status_code
    assert status == expected_result

@pytest.mark.parametrize("employeeID, structure_level, expected_result", [
    (2, 0, ['Michael Scott', 'Andy Bernard']),
    (2, 1, ['Dwight Schrute', 'Pam Beesly', 'Angela Martin']),
    (2, 2, ['Jim Halpert', 'Stanley Hudson', 'Kevin Malone', 'Oscar Martinez']),
    (1, 3, ['Jim Halpert', 'Stanley Hudson', 'Kevin Malone', 'Oscar Martinez', 'Pete Miller', 'Toby Flenderson'])
])
def test_get_company_structure(employeeID, structure_level, expected_result):
    response = requests.get(BASE_URL + "/employees/" + str(employeeID) + "/structure/" + str(structure_level)) #pied piper
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