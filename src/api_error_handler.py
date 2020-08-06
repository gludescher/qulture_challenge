from flask import Flask, request, jsonify

SQL_NOT_FOUND = "sql-0404"
SQL_CONSTRAINT_FAILED = "sql-0001"
HTTP_MISSING_PARAMS = "http-0001"
HTTP_PARAM_TYPE = "http-0002"
API_NOT_SAME_COMPANY = "api-0001"
API_STRUCTURE_LOOP = "api-0002"

error_messages = {
    "http-0001": "Missing required parameter(s) {}. Please try again with these parameters.",
    "sql-0404": "Specified {} not found in database.",
    "api-0001": "Manager and subordinate can't work in different companies. {}",
    "api-0002": "Not possible to assign this management relationship (probably due to a structure loop, see 'Loops' in README for more information). {}"
}

# TODO: implement message_params as **kwargs.
# For now it stands as is since the messages have mostly one parameter.
def error_handler(status_code, error_code, message="", message_param=""):
    if message == "":
        message = error_messages[error_code].format(str(message_param))

    response = {
        "error": {
            "status_code": status_code,
            "error_code": error_code,
            "message": message
        }
    }

    return jsonify(response), status_code   
    