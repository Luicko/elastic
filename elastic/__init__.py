import os
import sys

from flask import Flask
from flask.ext.cors import CORS
from flask.ext.login import LoginManager
from flask_restful import reqparse, Api
from elasticsearch import Elasticsearch

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('elastic.settings')
app.config.from_pyfile('settings.conf')
UPLOAD_FOLDER = sys.prefix
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CORS(app)
api = Api(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
es = Elasticsearch()

parsor = reqparse.RequestParser()

db = None

from . import models, views, settings