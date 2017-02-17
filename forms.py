from flask import session
from flask_wtf import Form
from wtforms import StringField, SubmitField, ValidationError
from wtforms.validators import Required, Length, Email
from db import get_db


# Custom validators

def check_clear(form, field):
    '''Verify that the clear command is valid.'''
    if field.data[0] in ['c', 'C']:
        try:
            int(field.data[1]) == int
        except ValueError:
            return True
        limit = session.get('limit')
        if int(field.data[1]) > session.get('limit'):
            raise ValidationError('You can only clear tasks 1-%d.' % (limit))


def check_revise(form, field):
    '''Verify that that the revision command is valid.'''
    if field.data[:3] in ['rev', 'Rev']:
        try:
            int(field.data[3]) == int
        except ValueError:
            return True
        limit = session.get('limit')
        if int(field.data[3]) > limit:
            raise ValidationError('You can only revise tasks 1-%d.' % (limit))
        if len(field.data) < 5:
            raise ValidationError('Enter the revision like "rev3 new task".')


def check_dupe(form, field):
    '''Verify that the task is not a duplicate.'''
    task = field.data[0].upper() + field.data[1:]
    db = get_db()
    cur = db.execute('select description from tasks where description = ?', \
                     (task,))
    check = cur.fetchone()
    if check != None:
        raise ValidationError('That task is already on your list.')


class NextActionForm(Form):
    next_action = StringField('Add, clear or revise a task, or start fresh:',\
     validators=[Required(), check_clear, check_revise, check_dupe])
    submit = SubmitField('Go!')