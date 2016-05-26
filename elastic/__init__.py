import os
import sys

from flask import Flask

from flask.ext.cors import CORS
from flask.ext.pagedown import PageDown
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager

from flask_restful import reqparse, Api
from flask_bootstrap import Bootstrap

from elasticsearch import Elasticsearch

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('elastic.settings')
app.config.from_pyfile('settings.conf')


upload_folder = (app.instance_path + '/files/')
app.config['UPLOAD_FOLDER'] = upload_folder

es = Elasticsearch()

CORS(app)

db = SQLAlchemy(app)
pagedown = PageDown(app)
Bootstrap(app)

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

from . import models, views, settings

@lm.user_loader
def load_user(id):
    """
    LoginManager callback to assign `current_user` proxy object.

    :param id: User ID
    :returns: :class:`User` filter by Email as Primary Key
    """
    x = models.Users.query.filter_by(id=id).first()
    return x