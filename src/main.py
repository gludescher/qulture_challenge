from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy import Column, Integer, DateTime
from flask_cors import CORS
from app_core import app, db
import json 
import os
import datetime
import requests
import time
from models import Company, Employee
import routes

if __name__ == '__main__':
    print(" Aquecendo os motores!!! ".center(90, '='))
    db.create_all()
    app.run(debug=True, port=5002)


