from __future__ import absolute_import, print_function # In python 2.7
import random

from flask.ext.login import UserMixin

from . import db, app

class Users(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column('id', db.Integer, db.Sequence('id_seq'))
    email = db.Column('email', db.String(255), primary_key=True)
    nickname = db.Column('nickname', db.String(255))
    password = db.Column('password', db.String(255))

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False
    
    def __repr__(self):
        return '<User %r>' % (self.nickname)