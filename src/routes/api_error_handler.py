from flask import Flask, request, jsonify

# ===================== E R R O R   C O D E S ====================== #
SQL_NOT_FOUND = "sql-0404"
SQL_CONSTRAINT_FAILED = "sql-0001"
HTTP_MISSING_PARAMS = "http-0001"
HTTP_PARAM_TYPE = "http-0002"
API_NOT_SAME_COMPANY = "api-0001"
API_STRUCTURE_LOOP = "api-0002"
# ================================================================== #


# ============ N O N - D E F A U L T   M E S S A G E S ============= #
NO_COMPANY_TO_ASSOCIATE = "No company found with ID {} to associate employee."
NO_EMPLOYEE_TO_ASSIGN = "No employee found with ID {} to assign as manager."
NO_EMPLOYEE_TO_DELETE = "Employee with ID {} does not exist to be deleted."
NO_EMPLOYEE_TO_EDIT = "Employee with ID {} not found. If you wish to create an employee, please use the POST request."
# ================================================================== #


default_messages = {
    "http-0001": "Missing required parameter(s) {}. Please try again with these parameters.",
    "http-0002": "Parameter(s) {} expect {} input.",
    "sql-0404": "Specified {} not found in database.",
    "api-0001": "Manager (companyID = {}) and subordinate (companyID = {}) can't work in different companies.",
    "api-0002": "Not possible to assign this management relationship (probably due to a structure loop, see 'Company Structure & Constraints' in README for more information)."
}


# Handles error message to be returned to client. 
# When no message is passed, assumes default message according to internal error_code.
# Messages usually expect some parameters to be passed in *argv to fill in the blanks. 
def error_handler(status_code, error_code, *argv, message=""):
    if message == "":
        message = default_messages[error_code]

    message = message.format(*argv)

    response = {
        "error": {
            "status_code": status_code,
            "error_code": error_code,
            "message": message
        }
    }

    return jsonify(response), status_code


def check_missing_parameters(request, required):
    if request.json is None:
        return required

    missing = []
    for param in required:
        if param not in request.json:
            missing.append(param)
            
    return missing 
    