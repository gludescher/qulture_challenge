# Companify - API

# 1. Intro

This is the documentation for the API of the Companify application. The RESTful API is expected to manage multiple companies and its employees, allowing an user to insert, edit, or delete data using HTTP requests.

It was developed using mainly Python 3, Flask and SQLAlchemy for integration with an SQLite local database.

# 2. Model

The model of the application consists of two tables: "Companies" and "Employees".

## 2.1. Companies Table

The "Companies" table is composed of the following columns:

- *companyID*: Integer; Primary key; Auto incremental; Not nullable;
- *name*: String; Unique; Not nullable.

## 2.2. Employees Table

The "Employees" table is composed of the following columns:

- *employeeID*: Integer; Primary key; Auto incremental; Not nullable;
- *name*: String; Not nullable;
- *email*: String; Unique; Not nullable;
- *managerID*: Integer; Foreign key (Employees.*employeeID*);
    - Refers the employee who is the manager of this employee. Set to NULL when employee has no manager.
- *companyID*: Integer; Foreign key (Companies.*companyID)*;
    - Refers the company in which the employee works. Set to NULL when employee has no company.

## 2.3. Company Structure & Constraints

By project definition, management relationship between employees must follow certain constraints to define an adequate company structure. These constraints are:

1. No employee may have more than one manager;
2. No employee may have a manager from another company;
3. No employee of someone above itself in the chain of management, i.e. there can be no structure loops.

To make the third constraint clearer, let's use an example. Take, for instance, the company Dunder Mifflin, structured as follows in the application:

![imgs/dunder_mifflin_(4).png](imgs/dunder_mifflin_(4).png)

Figure 1

For the structure above, we could consider the following operations:

- Invalid operations examples:
    - Assign Jim as Michael's manager: Jim is under Dwight who is under Michael. Therefore, this would create a loop.
    - Assign Nellie as Andy's manager: Nelly is under Andy. This would also create a loop.
- Valid operations examples:
    - Assign Robert California as Michael's manager.
    - Assign Nellie Bertram as Michael's manager: although unintuitive, Nellie isn't below Michael in the hierarchy. In this case, all employees currently under Michael would also be under Nellie. Thus, Michael would be on the same level as Toby.
    - Assign Dwight as Pete's manager: although Pete already has a manager, this would simply change his manager, as in a department change. If he had subordinates, they would come along as well.
    - Remove Jim's manager (set to NULL) and then assign Jim as Michael's manager: now, Jim has no manager when we try to assign him as Michael's manager, so there is no problem in that.

# 3. API

The API consists of the standard RESTful methods GET, POST, PUT and DELETE. 

The required parameters are marked in italic.

All the examples are built considering the Python's built-in library 'requests'.

## 3.1. Companies Endpoints

### Create company

- **Path:** '/companies'
- **Method:** POST
- **Parameters:**
    - *name* - String; name of the company to be created; must be unique in database.
- **Request example:**

    ```python
    company = {
        'name':'Sic Mundus'
    }
    response = requests.post(baseURL + '/companies', json=company)
    ```

- **Response example:**

    ```json
    {
      "companyID": 3,
      "name": "Sic Mundus"
    }
    Status: 200
    ```

### List companies

- **Path:** '/companies'
- **Method:** GET
- **Request example:**

    ```python
    response = requests.get(baseURL + '/companies')
    ```

- **Response example:**

    ```json
    [
      {
        "companyID": 1,
        "name": "Dunder-Mifflin"
      },
      {
        "companyID": 2,
        "name": "Pied Piper"
      },
      {
        "companyID": 3,
        "name": "Sic Mundus"
      }
    ]
    Status: 200
    ```

### Get company

- **Path:** '/companies/<*companyID*>'
- **Method:** GET
- **Request example:**

    ```python
    response = requests.get(baseURL + '/companies/2')
    ```

- **Response example:**

    ```json
    {
      "companyID": 2,
      "name": "Pied Piper"
    }
    Status: 200
    ```

### Search company

- **Path:** '/companies/search'
- **Method:** GET
- **Parameters:**
    - name - String; used to search the table Companies; when this parameter is absent, a list with all companies is returned.
- **Request example:**

    ```python
    response = requests.get(baseURL + '/companies/search?name=dunder')
    ```

- **Response example:**

    ```json
    [
      {
        "companyID": 1,
        "name": "Dunder-Mifflin"
      }
    ]
    Status: 200
    ```

### List company's employees

Lists all the employees associated to specified company.

- **Path:** '/companies/<*companyID*>/employees'
- **Method:** GET
- **Request example:**

    ```python
    response = requests.get(baseURL + '/companies/2/employees')
    ```

- **Response example:**

    ```json
    [
      {
        "companyID": 2,
        "email": "richie@pp.com",
        "employeeID": 15,
        "managerID": null,
        "name": "Richard Hendricks"
      },
      {
        "companyID": 2,
        "email": "gilfoyle666@pp.com",
        "employeeID": 16,
        "managerID": 15,
        "name": "Bertram Gilfoyle"
      },
      {
        "companyID": 2,
        "email": "dine$h_tesla@pp.com",
        "employeeID": 17,
        "managerID": 15,
        "name": "Dinesh"
      }
    ]
    Status: 200
    ```

## 3.2. Employees Endpoints

### Create employee

- **Path:** '/employees'
- **Method:** POST
- **Parameters:**
    - *name* - String; name of the employee to be created.
    - *email* - String; email of the employee to be created; must be unique in database.
    - companyID - Integer; company in which the employee works; must currently exist in database.
    - managerID - Integer; manager of the employee being created; must currently exist in database; must obey constraints defined in section 2.3.
- **Request example:**

    ```python
    employee = {
        "name":"Ryan Howard", 
        "email":"kelly_i_s2_you@dm.com", 
        "companyID":1, 
        "managerID":1
    }
    response = requests.post(baseURL + '/employees', json=employee)
    ```

- **Response example:**

    ```json
    {
        "companyID": 1,
        "email": "kelly_i_s2_you@dm.com",
        "employeeID": 19,
        "managerID": 1,
        "name": "Ryan Howard"
    }
    Status: 200
    ```

### List employees

- **Path:** '/employees'
- **Method:** GET
- **Request example:**

    ```python
    response = requests.get(baseURL + '/employees')
    ```

- **Response example:**

    ```json
    [
      {
        "companyID": 1,
        "email": "mikeymike@dm.com",
        "employeeID": 1,
        "managerID": null,
        "name": "Michael Scott"
      },
      {
        "companyID": 1,
        "email": "beets_bears_battlestargallactica@dm.com",
        "employeeID": 1,
        "managerID": 2,
        "name": "Dwight Schrute"
      },
      {
        "companyID": 1,
        "email": "hmmm_necks_O.O@dm.com",
        "employeeID": 14,
        "managerID": 1,
        "name": "Toby Flenderson"
      },
      {
        "companyID": 2,
        "email": "richie@pp.com",
        "employeeID": 15,
        "managerID": null,
        "name": "Richard Hendricks"
      },
      {
        "companyID": 2,
        "email": "gilfoyle666@pp.com",
        "employeeID": 16,
        "managerID": 15,
        "name": "Bertram Gilfoyle"
      }
    ]
    Status: 200
    ```

### ****Get employee

- **Path:** '/employees/<*employeeID*>'
- **Method:** GET
- **Request example:**

    ```python
    response = requests.get(baseURL + '/employees/11')
    ```

- **Response example:**

    ```json
    {
        "companyID": 1,
        "email": "donna_noble@dw.com",
        "employeeID": 11,
        "managerID": 10,
        "name": "Nellie Bertram"
    }
    Status: 200
    ```

### ****Search employee

- **Path:** '/employees/search'
- **Method:** GET
- **Parameters:**
    - name - String; used to search the table Employees; when this parameter is absent, a list with all employees is returned.
- **Request example:**

    ```python
    response = requests.get(baseURL + '/companies/search?name=bertram')
    ```

- **Response example:**

    ```json
    [
      {
        "companyID": 1,
        "email": "donna_noble@dw.com",
        "employeeID": 11,
        "managerID": 10,
        "name": "Nellie Bertram"
      },
      {
        "companyID": 2,
        "email": "gilfoyle666@pp.com",
        "employeeID": 16,
        "managerID": 15,
        "name": "Bertram Gilfoyle"
      }
    ]
    Status = 200
    ```

### Get employee's subordinates

Lists the employees N levels directly below the specified employee. If N = 0, lists the employees under the same manager as the specified employee, i.e. on the same hierarchy level. It is valid noting that the function accepts any level ≥0 of hierarchy as input.
Still using Dunder Mifflin structure (Figure 1), if a call is made passing Michael's employeeID and level = 1, the return would be Dwight, Pam and Angela. The level 2 return for Michael would be Stanley, Jim, Kevin and Oscar. Level 0 for Jim is just Stanley, since they share Dwight as manager. 

- **Path:** '/employees/<*employeeID>*/structure/*<level>*''
- **Method:** GET
- **Parameters:**
    - *employeeID* - Integer; specified employee to serve as base for the structure listing.
    - *level* - Integer; defines on how many hierarchic grades below the specified employee should be the return.
- **Request example:**

    ```python
    response = requests.get(baseURL + '/employees/1/structure/1')
    ```

- **Response example:**

    ```json
    [
      {
        "companyID": 1,
        "email": "beets_bears_battlestargallactica@dm.com",
        "employeeID": 3,
        "managerID": 1,
        "name": "Dwight Schrute"
      },
      {
        "companyID": 1,
        "email": "pamela@dm.com",
        "employeeID": 4,
        "managerID": 1,
        "name": "Pam Beesly"
      },
      {
        "companyID": 1,
        "email": "accountant_cats@dm.com",
        "employeeID": 5,
        "managerID": 1,
        "name": "Angela Martin"
    	}
    ]
    Status = 200
    ```

### Edit employee

This function edits any parameter (except for employeeID) of an employee. It requires special attention to some details.

- **Path:** '/employees/<*employeeID>*'
- **Method:** PUT
- **Parameters:**
    - *employeeID* - Integer; specified employee to be edited.
    - name - String; new name of the employee;
    - email - String; new email of the employee; must be unique in database;
    - companyID - Integer; new company of the employee;
    - managerID - Integer; new manager of the employee;

Changing one's company requires attention to some specific details:

- If the employee being moved from one company to another has subordinates, its subordinates will be left without a manager (managerID = NULL). This will be reported in the response as "indirect changes".
- If no new manager is assigned to the moving employee in the same request, it will be left without a manager (managerID = NULL).
- If a new manager is assigned as the employee changes companies, the new manager must be from the new company or the request will fail.

Changing one's manager is also worthy of note:

- It must, as always, follow the constraints defined in section 2.3.
- If it is necessary to assign a relationship that currently generates a loop, you should first unassign the manager from the lower-graded employee and then assign this employee as manager to the other. E.g.: using Dunder Mifflin (Figure 1), to assign Jim as Michael's manager, it is necessary to remove Jim's manager and only then proceed.

**NOTE:** To explicitly unassign a manager from an employee or remove an employee from a company, the corresponding ID should be set to null in the PUT request.

- **Request example 1:**

    ```python
    employee = {
        "name":"Pam Beesly Halpert",
        "email":"pam_halpert@dm.com"
    }
    response = requests.put(baseURL + '/employees/4', json=employee)
    ```

- **Response example 1:**

    ```json
    {
      "companyID": 1,
      "email": "pam_halpert@dm.com",
      "employeeID": 4,
      "managerID": 2,
      "name": "Pam Beesly Halpert"
    }
    Status = 200
    ```

- **Request example 2:**

    ```python
    {
        "email":"nard_dog@american.idol",
        "companyID":None
    }
    response = requests.put(baseURL + '/employees/10', json=employee)
    ```

- **Response example 2:**

    ```json
    {
      "employee": {
        "companyID": null,
        "email": "nard_dog@american.idol",
        "employeeID": 10,
        "managerID": null,
        "name": "Andy Bernard"
      },
      "indirect_changes": {
        "api_warning": "These employees were also changed to keep database consistency.",
        "changes": "Attribute managerID set to NULL.",
        "employees": [
          {
            "companyID": 1,
            "email": "donna_noble@dw.com",
            "employeeID": 11,
            "managerID": 10,
            "name": "Nellie Bertram"
          },
          {
            "companyID": 1,
            "email": "erin@foster.com",
            "employeeID": 12,
            "managerID": 10,
            "name": "Erin Hannon"
          }
        ]
      }
    }
    Status = 200
    ```

### Delete employee

- **Path:** '/employees/<*employeeID>*'
- **Method:** DELETE

This operation, as well as editing employee, also returns the indirect changes it may have caused, since the practical effects of deleting an employee or changing its company are basically the same for its subordinates.

- **Request example:**

    ```python
    response = requests.delete(baseURL + '/employees/10')
    ```

- **Response example:**

    ```json
    {
      "employee": {
        "companyID": 1,
        "email": "accountant_b@dm.com",
        "employeeID": 5,
        "managerID": 2,
        "name": "Angela Martin"
      },
      "indirect_changes": {
        "api_warning": "These employees were also changed to keep database consistency.",
        "changes": "Attribute 'managerID' set to NULL.",
        "employees": [
          {
            "companyID": 1,
            "email": "cookies@dm.com",
            "employeeID": 8,
            "managerID": 5,
            "name": "Kevin Malone"
          },
          {
            "companyID": 1,
            "email": "oscars2senator@dm.com",
            "employeeID": 9,
            "managerID": 5,
            "name": "Oscar Martinez"
          }
        ]
      }
    }
    Status = 200
    ```

## 3.3. Tests Endpoints

While running the application on Test mode, these endpoints are enabled. They should be used mostly for data preparation, maintaining consistency from one test session to another.

### Test Set Up

This endpoint uses .json files located in the /tests folder of the project directory to populate the tables Companies and Employees.

- **Path:** '/tests/setup'
- **Method:** POST

### Test Tear Down

This endpoint drops all tables located in the test database, cleaning the changes made for future test sessions.

- **Path:** '/tests/teardown'
- **Method:** POST

## 3.4. Error Handling

This API uses the default HTTP status codes to report the result of requests but also makes use of proprietary error codes, with the intent of better specifying the problem.

### Default status codes

The API uses HTTP status codes as default:

- 200: Success
- 400: Bad Request - Usually, there was a problem in the parameters of the request or the sql constraints
- 404: Not Found

**NOTE:** Some requests may succeed and still return 404 if a GET returned and empty list. In this cases, the response.json() will be an empty list and the status code will be 404.

### Error codes

The error codes are formed as "abc-0123" where "abc" represents the scope of the error and "0123" is simply a number associated with the error.

- **sql-0404:** Element not found in database. This code is usually returned in requests that specify a single element in the database such as "Get company" or "Edit employee".
    - **Request example:**

        ```python
        response = requests.delete(baseURL + '/employees/99')
        ```

    - **Response example:**

        ```json
        {
          "error": {
            "error_code": "sql-0404",
            "message": "Employee with ID 99 does not exist to be deleted.",
            "status_code": 404
          }
        }
        ```

- **sql-0001:** SQL constraint failed. This code is usually returned when a unique constraint in the database is not respected.
    - **Request example:**

        ```python
        company = {
        	"name":"Pied Piper"
        }
        response = requests.post(baseURL + '/companies', json=company)
        ```

    - **Response example:**

        ```json
        {
          "error": {
            "error_code": "sql-0001",
            "message": "(sqlite3.IntegrityError) UNIQUE constraint failed: Companies.name [SQL: INSERT INTO \"Companies\" (name) VALUES (?)] [parameters: ('Pied Piper',)] (Background on this error at: http://sqlalche.me/e/13/gkpj)",
            "status_code": 400
          }
        }
        ```

- **http-0001:** Missing required parameters.
    - **Request example:**

        ```python
        employee = {
        	"name":"Creed Bratton",
        	"companyID":1
        }
        response = requests.post(baseURL + '/employees', json=employee)
        ```

    - **Response example:**

        ```json
        {
          "error": {
            "error_code": "http-0001",
            "message": "Missing required parameter(s) ['email']. Please try again with these parameters.",
            "status_code": 400
          }
        }
        ```

- **http-0002:** Invalid parameter type.
    - **Request example:**

        ```python
        employee = {
        	"name":"Creed Bratton",
        	"email":"not_a_fugitive@dm.com",
        	"companyID":1,
        	"managerID":"potato"
        }
        response = requests.post(baseURL + '/employees', json=employee)
        ```

    - **Response example:**

        ```json
        {
          "error": {
            "error_code": "http-0002",
            "message": "Parameter(s) ['companyID', 'managerID'] expect numeric input.",
            "status_code": 400
          }
        }
        ```

- **api-0001:** Manager and subordinate not on same company. This error occurs when trying to assign a manager to an employee but they don't work on the same company.
    - **Request example:**

        ```python
        employee = {
            "email": "stanley_single@tinder.com",
            "managerID": 15
        }
        response = requests.put(baseURL + '/employees/7', json=employee)
        ```

    - **Response example:**

        ```json
        {
          "error": {
            "error_code": "api-0001",
            "message": "Manager (companyID = 2) and subordinate (companyID = 1) can't work in different companies.",
            "status_code": 400
          }
        }
        ```

- **api-0002:** Structure loop. This error occurs when the assignment of a manager would cause a hierarchy loop.
    - **Request example:**

        ```python
        employee = {
            "email": "stanley_single@tinder.com",
            "managerID": 15
        }
        response = requests.post(baseURL + '/employees', json=employee)
        ```

    - **Response example:**

        ```json
        {
          "error": {
            "error_code": "api-0002",
            "message": "Not possible to assign this management relationship (probably due to a structure loop, see 'Company Structure & Constraints' in README for more information).",
            "status_code": 400
          }
        }
        ```

# 4. Run Modes

The application was designed to allow different run modes that make it easy to alternate between a test and a production database.

There are 3 run modes: "Test", "Debug" and "Production". 

[Untitled](https://www.notion.so/20b4e5051f60435585438fe95d7228ae)

To select which mode to run the application, the name of the mode should be passed as argument on the command line while running main.py. If no argument is passed, it will run on default (debug) mode. For example, to run on "Test" mode:

```bash
python src/main.py t
```

### Test Mode

The Test Mode is the only mode that enables the test endpoints, avoiding messing with the production database.

To execute the automated tests, it is necessary to run the script with pytest, as following:

```bash
pytest tests/integration_tests.py
```

It is also necessary that the application is already up and running in Test Mode.

# Final Considerations

This was a project developed as a challenge for a recruitment process for internship in Qulture.Rocks and was built in about a week. If you have any suggestions or feedbacks, send me an email: guilherme.ludescher@usp.br. I'll gladly read and promptly answer them! 😁

Anyhow, thanks for reading! Hope you liked it!

![imgs/michael.gif](imgs/michael.gif)