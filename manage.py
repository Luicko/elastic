#!/usr/bin/env python

from flask.ext.script import Manager

from elastic import app

manager = Manager(app)

@manager.command
def clean():
    from elastic import db, models

    u = models.Users.query.all()
    for user in u:
        db.session.delete(user)
        db.session.commit()

if __name__ == "__main__":
    manager.run()
