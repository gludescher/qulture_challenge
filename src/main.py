from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import Column, Integer, DateTime
from flask_cors import CORS
import json 
import datetime
import requests
import time
import os
import sys
import atexit


from app.app_core import db, create_app

run_modes = {
    "debug": "DEBUG_MODE",
    "d": "DEBUG_MODE",
    "test": "TEST_MODE",
    "t": "TEST_MODE",
    "production": "PRODUCTION_MODE",
    "p": "PRODUCTION_MODE"
}


if len(sys.argv) > 1 and sys.argv[1].lower() in run_modes:
    run_mode = run_modes[sys.argv[1]]
else:
    run_mode = run_modes['debug']



if __name__ == '__main__':
    app, cors, ma = create_app(run_mode)

    # these imports need to be done after 'app' has been created
    from routes import company_routes, employee_routes
    from models.employee_model import Employee, update_manager_trigger
    from models.company_model import Company
    
    print(" Running Companify API - {} ".format(run_mode).center(90, "="))
    if run_mode == run_modes['test']:
        import routes.test_routes
        db.create_all()
        routes.test_routes.tear_down()
        routes.test_routes.set_up()
        atexit.register(routes.test_routes.empty_test_database)
        app.run(debug=True, port=5002)
    else: # debug or production
        db.create_all() 
        app.run(debug=run_mode==run_modes['debug'], port=5002)



