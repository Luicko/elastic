import os
import sys

from flask import Flask
from flask.ext.cors import CORS
from flask_restful import reqparse, Api
from elasticsearch import Elasticsearch

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('elastic.settings')
app.config.from_pyfile('settings.conf')
upload_folder = (app.instance_path + '/files/')
app.config['UPLOAD_FOLDER'] = upload_folder
CORS(app)
es = Elasticsearch()

db = None

from . import models, views, settings