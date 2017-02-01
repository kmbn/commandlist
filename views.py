import os
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
                  render_template, flash
from datetime import datetime
from db import get_db, close_db
from config import app


@app.route('/')
def main_view():
    '''Fetch the current user's tasks and calculate the size of the bucket.'''
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
    missing_rows = [] # Create placeholders for formatting based on five items
    for i in range(5 - len(tasks)):
        missing_rows.append('item')
    limit = len(tasks) # Necessary for parsing input in get_next_action
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
    '''Parse the input and either:
    1. Create a new task (anything that isn't a command)
    2. Delete a task on the list (e.g., 'c2' will delete task number 2)
    3. Revise a task on the list (e.g., 'rev3 New task' will replace
    the old conten of task number 3 with 'New task')
    4. Wipe the list and start over ('reset list')
    5. Redirect the user to a different page (e.g., 'help' will redirect
    to the how-to page; 'back' will redirect to the homepage)

    The limit is used ensure that a user is referring to an actual position
    on the task list.'''
    if request.method != 'POST':
        return redirect(url_for('main_view'))
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
        return redirect(url_for('how_to'))
    elif next_action == 'Back' or next_action == "'back'":
        return redirect(url_for('main_view'))
    else:
        return check_task()


def check_task():
    '''Verify that the task is not a duplicate.'''
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
    '''Add the task to the task table.'''
    next_action = session.get('next_action')
    current_user = 1
    current_time = datetime.utcnow()
    db = get_db()
    db.execute('insert into tasks (description, creator_id, created_on) \
               values (?, ?, ?)', (next_action, current_user, current_time))
    db.commit()
    return redirect(url_for('main_view'))


def clear_task():
    '''Delete the task from the task table.'''
    next_action = session.get('next_action')
    tasks = session.get('tasks')
    task_number = int(next_action[1])
    task_id = tasks[task_number-1]
    db = get_db()
    db.execute('delete from tasks where id = ?', (task_id,))
    db.commit()
    return redirect(url_for('main_view'))


def restart():
    '''Erase all tasks for the given user and start a fresh list.'''
    current_user = 1
    db = get_db()
    db.execute('delete from tasks where creator_id = ?', (current_user,))
    db.commit()
    flash('To do list and bucket emptied – enjoy your fresh start!')
    return redirect(url_for('main_view'))


def revise():
    '''Revise the given task (indicated by index[3] of the input).
    All text from index[5] onward is considered to be the new content
    of the task.'''
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