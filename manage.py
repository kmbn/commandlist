from flask_script import Manager
import os
from sqlite3 import dbapi2 as sqlite3

from commandlist import app
from commandlist import get_db, connect_db

manager = Manager(app)

@manager.command
def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    print('Initialized database')

if __name__ == "__main__":
    manager.run()