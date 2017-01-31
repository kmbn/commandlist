'''
    CommandList:
    A browser-based command line todo list built with Flask and sqlite3.
'''

import os
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
                  render_template, flash
from datetime import datetime
from flask_bootstrap import Bootstrap


app = Flask(__name__)
bootstrap = Bootstrap(app)


# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'commandlist.db')
    ))


app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'secret_key'


def connect_db():
    '''Connects to the specific database.'''
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    '''Opens a new database connection if there is none yet for the
    current application context.
    '''
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    '''Closes the database again at the end of the request.'''
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


# MAIN APP VIEWS AND LOGIC
@app.route('/')
def main_view():
    current_user = 1
    db = get_db()
    cur = db.execute('select id, description from tasks where creator_id = ? \
                     order by id asc limit 5', (current_user,))
    tasks = cur.fetchall()
    if tasks is None:
        tasks = []
    else:
        task_ids = []
        for row in tasks:
            task_ids.append(row[0])
    missing_rows = []
    for i in range(5 - len(tasks)):
        missing_rows.append('item')
    limit = len(tasks)
    session['limit'] = limit
    session['tasks'] = task_ids
    db = get_db()
    cur = db.execute('select count(id) from tasks where creator_id = ?', \
                     (current_user,))
    bucket = cur.fetchone()
    if bucket is not None:
        bucket = bucket[0]
        bucket -= 5
    return render_template('main.html', tasks=tasks, bucket=bucket, \
                           missing_rows=missing_rows)


@app.route('/get_next_action', methods=['GET', 'POST'])
def get_next_action():
    limit = session.get('limit')
    next_action = request.form['next_action']
    if len(next_action) == 0:
        flash('You have to type something in the box ;\).')
        return redirect(url_for('main_view'))
    next_action = next_action[0].upper() + next_action[1:]
    session['next_action'] = next_action
    if next_action[0] == 'C':
        try:
            int(next_action[1]) == int
        except ValueError:
            return check_task()
        if 0 < int(next_action[1]) <= limit:
            return clear_task()
        elif int(next_action[1]) > limit:
            flash('You can only clear tasks 1-%d.' % (limit))
            return redirect(url_for('main_view'))
    elif next_action == 'Reset list':
        return restart()
    elif next_action[:3] == 'Rev':
        try:
            int(next_action[3]) == int
        except ValueError:
            return check_task()
        if 0 < int(next_action[3]) <= limit:
            return revise()
        elif int(next_action[3]) > limit:
            flash('You can only revise tasks 1-%d.' % (limit))
            return redirect(url_for('main_view'))
    elif next_action == 'Help':
        return redirect(url_for('help'))
    else:
        return check_task()


def check_task():
    next_action = session.get('next_action')
    db = get_db()
    cur = db.execute('select description from tasks where description = ?', \
                     (next_action,))
    check = cur.fetchone()
    if check is None:
        return add_task()
    else:
        flash('That task is already on your list.')
        return redirect(url_for('main_view'))


def add_task():
    next_action = session.get('next_action')
    current_user = 1
    current_time = datetime.utcnow()
    db = get_db()
    db.execute('insert into tasks (description, creator_id, created_on) \
               values (?, ?, ?)', (next_action, current_user, current_time))
    db.commit()
    flash('Task added.')
    return redirect(url_for('main_view'))


def clear_task():
    next_action = session.get('next_action')
    tasks = session.get('tasks')
    task_number = int(next_action[1])
    task_id = tasks[task_number-1]
    db = get_db()
    db.execute('delete from tasks where id = ?', (task_id,))
    db.commit()
    flash('Task deleted')
    return redirect(url_for('main_view'))


def restart():
    current_user = 1
    db = get_db()
    db.execute('delete from tasks where creator_id = ?', (current_user,))
    db.commit()
    flash('To do list and bucket emptied – enjoy your fresh start!')
    return redirect(url_for('main_view'))


def revise():
    next_action = session.get('next_action')
    tasks = session.get('tasks')
    if len(next_action) > 5:
        task_number = int(next_action[3])
        task_id = tasks[task_number-1]
        new_task = next_action[4:]
        db = get_db()
        db.execute('update tasks set description = ? where id = ?', \
                   (new_task, task_id))
        db.commit()
        return redirect(url_for('main_view'))
    else:
        flash('Enter the revised task on the same line.')
        return redirect(url_for('main_view'))


@app.route('/how_to')
def how_to():
    return render_template('how_to.html')

@app.route('/about')
def about():
    return render_template('about.html')


# ERROR HANDLERS
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500
# ==============================================================

# RUN APP
if __name__ == '__main__':
    app.run(debug=True)
# ==============================================================