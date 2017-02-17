import os
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
                  render_template, flash
from datetime import datetime
from . import app
from .db import get_db
from .forms import NextActionForm, OpenNavForm
from .decorators import login_required


@app.route('/', methods=['GET', 'POST'])
def main_view():
    '''Fetch the current user's tasks and calculate the size of the bucket.'''
    if not session.get('logged_in'):
        open_nav = OpenNavForm()
        if open_nav.validate_on_submit():
            return parse_open_nav(open_nav)
        '''if form.validate_on_submit():
            next_action = form.next_action.data[0].upper() + \
            form.next_action.data[1:]
            if next_action == 'Log in':
                return redirect(url_for('login'))
            elif next_action == 'Sign up':
                return redirect(url_for('register'))
            elif next_action == 'Home':
                return redirect(url_for('main_view'))'''
        return render_template('welcome.html', open_nav=open_nav)
    else:
        form = NextActionForm()
        current_user = session.get('current_user')
        if form.validate_on_submit():
            return get_next_action(form, current_user)
        db = get_db()
        cur = db.execute('select id, description from tasks \
            where creator_id = ? order by id asc limit 5', (current_user,))
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
        session['task_ids'] = task_ids
        db = get_db()
        cur = db.execute('select count(id) from tasks where creator_id = ?', \
                         (current_user,))
        bucket = cur.fetchone()
        if bucket is not None:
            bucket = bucket[0]
            bucket -= 5
        return render_template('main.html', tasks=tasks, bucket=bucket, \
            missing_rows=missing_rows, form=form)


def parse_open_nav(form):
    next_action = form.next_action.data[0].upper() + \
    form.next_action.data[1:]
    if next_action == 'Log in':
        return redirect(url_for('login'))
    elif next_action == 'Sign up':
        print('sign up')
        return redirect(url_for('register'))
    elif next_action == 'Home':
        return redirect(url_for('main_view'))


def get_next_action(form, current_user):
    '''Parse the input and either:
    1. Create a new task (anything that isn't a command)
    2. Delete a task on the list (e.g., 'c2' will delete task number 2)
    3. Revise a task on the list (e.g., 'rev3 New task' will replace
    the old conten of task number 3 with 'New task')
    4. Wipe the list and start over ('reset list')
    5. Redirect the user to a different page (e.g., 'help' will redirect
    to the how-to page; 'back' will redirect to the homepage)
    '''
    next_action = form.next_action.data[0].upper() + \
        form.next_action.data[1:]
    if next_action[0] == 'C':
        try:
            int(next_action[1]) == int
        except ValueError:
            print('huh')
            return add_task(next_action, current_user)
        return clear_task(next_action[:2], current_user)
    elif next_action[:3] == 'Rev':
        try:
            int(next_action[3]) == int
        except ValueError:
            return add_task(next_action, current_user)
        return revise(next_action, current_user)
    elif next_action == 'Reset list':
        return restart(current_user)
    elif next_action == 'Help':
        return redirect(url_for('how_to'))
    elif next_action == 'Back':
        return redirect(url_for('main_view'))
    elif next_action == 'Log out':
        return redirect(url_for('logout'))
    elif next_action == 'Account':
        return redirect(url_for('manage_account'))
    else:
        return add_task(next_action, current_user)


def add_task(next_action, current_user):
    '''Add the task to the task table.'''
    current_time = datetime.utcnow()
    db = get_db()
    db.execute('insert into tasks (description, creator_id, created_on) \
               values (?, ?, ?)', (next_action, current_user, current_time))
    db.commit()
    return redirect(url_for('main_view'))


def clear_task(next_action, current_user):
    '''Delete the task from the task table.'''
    task_ids = session.get('task_ids')
    task_number = int(next_action[1])
    task_id = task_ids[task_number-1]
    db = get_db()
    db.execute('delete from tasks where id = ? and creator_id = ?', \
        (task_id, current_user))
    db.commit()
    return redirect(url_for('main_view'))


def restart(current_user):
    '''Erase all tasks for the given user and start a fresh list.'''
    db = get_db()
    db.execute('delete from tasks where creator_id = ?', (current_user,))
    db.commit()
    flash('To do list and bucket emptied – enjoy your fresh start!')
    return redirect(url_for('main_view'))


def revise(next_action, current_user):
    '''Revise the given task (indicated by index[3] of the input).
    All text from index[5] onward is considered to be the new content
    of the task.'''
    task_ids = session.get('task_ids')
    task_number = int(next_action[3])
    task_id = task_ids[task_number-1]
    new_task = next_action[5].upper() + next_action[6:]
    db = get_db()
    db.execute('update tasks set description = ? where id = ? \
        and creator_id = ?', (new_task, task_id, current_user))
    db.commit()
    return redirect(url_for('main_view'))


@app.route('/how_to', methods=['GET', 'POST'])
@login_required
def how_to():
    form = NextActionForm()
    current_user = session.get('current_user')
    if form.validate_on_submit():
        return get_next_action(form, current_user)
    return render_template('how_to.html', form=form)