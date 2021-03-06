import os
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, redirect, url_for, abort, \
    render_template, flash, request, Markup, Blueprint
from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from . import auth, pwd_context
from .forms import RegistrationForm, NewEmailForm, LoginForm, \
    ChangePasswordForm, RequestPasswordResetForm, SetNewPasswordForm
from app import app
from app.db import get_db
from app.mail import send_email
from app.decorators import login_required
from app.main.views import main_view


@auth.route('account/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in') == True:
        flash('You are already logged in')
        return redirect(url_for('main.main_view'))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        db = get_db()
        cur = db.execute('select id, status from users \
            where email is ?', (email,))
        row = cur.fetchone()
        session['logged_in'] = True
        session['current_user'] = row[0]
        session['status'] = row[1]
        if row[1] == 'unconfirmed':
            flash(Markup('Please confirm your email address. </br>\
                Click <a href="%s">here</a> \
                if you need a new confirmation link.' % \
                (url_for('auth.resend_confirmation'))))
        if request.args.get('next'):
            return redirect(request.args.get('next'))
        else:
            return redirect(url_for('main.main_view'))
    return render_template('login.html', form=form)


@auth.route('account/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    session.pop('current_user', None)
    session.pop('status', None)
    flash('You have been logged out.')
    return redirect(url_for('main.main_view'))


@auth.route('account/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        db = get_db()
        email = form.email.data
        password = form.password.data
        current_time = datetime.utcnow().date()
        password_hash = pwd_context.hash(password)
        role = 'user'
        db.execute('insert into users (email, password, role, \
            joined_on, status) values (?, ?, ?, ?, ?)', \
            (email, password_hash, role, current_time, 'unconfirmed'))
        db.commit()
        session['logged_in'] = True
        session['status'] = 'unconfirmed'
        cur = db.execute('select id from users where email = ?', (email,))
        row = cur.fetchone()
        user_id = row[0]
        session['current_user'] = user_id
        token = generate_confirmation_token(user_id)
        send_email(email, 'Thanks for registering—please confirm your email',
                       'email/confirm', token=token)
        flash(Markup('You have been registered and are now logged in. \
            </br>A confirmation has been sent to your email address.'))
        return redirect(url_for('main.main_view'))
    return render_template('register.html', form=form)


# For confirmation
def generate_confirmation_token(user_id, expiration=3600):
    s = Serializer(app.config['SECRET_KEY'], expiration)
    return s.dumps({'confirm': user_id})

def generate_email_token(user_id, new_email, expiration=3600):
    s = Serializer(app.config['SECRET_KEY'], expiration)
    return s.dumps({'confirm': user_id, 'email': new_email})


@auth.route('account/confirm/<token>')
def confirm(token):
    s = Serializer(app.config['SECRET_KEY'])
    user_id = session.get('current_user')
    try:
        data = s.loads(token)
    except:
        flash('The confirmation link is invalid or has expired.')
        return redirect(url_for('auth.resend_confirmation'))
    if data.get('confirm') != user_id:
        flash('You need to log in to confirm your email address.')
        return redirect(url_for('auth.login', next=request.url))
    elif data.get('confirm') == user_id:
        session['status'] = 'confirmed'
        current_time = datetime.utcnow().date()
        db = get_db()
        db.execute('update users set status = ?, confirmed_on = ? \
            where id = ?', ('confirmed', current_time, user_id))
        db.commit()
        if session.get('logged_in') == True:
            session['status'] = 'confirmed'
            flash('Email confirmed—thank you!')
            return redirect(url_for('main.main_view'))
        else:
            flash('Email confirmed—you can log in now!')
            return redirect(url_for('auth.login'))


@auth.route('account/confirm')
@login_required
def resend_confirmation():
    user_id = session.get('current_user')
    status = session.get('status')
    if status == 'confirmed':
        flash('You have already confirmed your email address')
        return redirect(url_for('main.main_view'))
    elif status == 'unconfirmed':
        token = generate_confirmation_token(user_id)
        db = get_db()
        cur = db.execute('select email from users where id = ?', (user_id,))
        row = cur.fetchone()
        email = row[0]
        send_email(email, 'Your new confirmation token',
                   'email/confirm', token=token)
        flash('A new confirmation email has been sent to your address.')
    return redirect(url_for('main.main_view'))


@auth.route('account/change_email/<token>')
def confirm_new_email(token):
    s = Serializer(app.config['SECRET_KEY'])
    user_id = session.get('current_user')
    try:
        data = s.loads(token)
    except:
        flash('The confirmation link is invalid or has expired.')
        return redirect(url_for('auth.change_email'))
    if data.get('confirm') != user_id:
        flash('You need to log in with your currently registered email \
            address to confirm your new email address.')
        return redirect(url_for('auth.login', next=request.url))
    elif data.get('confirm') == user_id:
        new_email = data.get('email')
        db = get_db()
        db.execute('update users set email = ? where id = ?', \
            (new_email, user_id))
        db.commit()
        if session.get('logged_in') == True:
            flash('New email address %s confirmed—thank you!' % (new_email))
            return redirect(url_for('main.main_view'))
        else:
            flash('New email address %s confirmed—\
                you can now use it to log in!' % (new_email))
            return redirect(url_for('auth.login'))


@auth.route('account/change_email', methods=['GET', 'POST'])
@login_required
def change_email():
    user_id = session.get('current_user')
    form = NewEmailForm()
    if form.validate_on_submit():
        new_email = form.new_email.data
        db = get_db()
        cur = db.execute('select email from users where email is ?', \
            (new_email,))
        row = cur.fetchone()
        if row == None:
            token = generate_email_token(user_id, new_email)
            send_email(new_email, 'Confirm your new email address',
                   'email/change_email', token=token)
            flash('A confirmation email has been sent to your address.')
            return redirect(url_for('main.main_view'))
        else:
            flash('That email address is already registered.')
            return redirect(url_for('auth.change_email'))
    db = get_db()
    cur = db.execute('select email from users where id is ?', (user_id,))
    row = cur.fetchone()
    current_email = row[0]
    return render_template('change_email.html', form=form, \
        current_email=current_email)


@auth.route('account/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    user_id = session.get('current_user')
    form = ChangePasswordForm()
    if form.validate_on_submit():
        db = get_db()
        cur = db.execute('select password from users where id is ?', \
            (user_id,))
        row = cur.fetchone()
        db_password = row[0]
        password_for_verification = form.current_password.data
        if pwd_context.verify(password_for_verification, db_password) is True:
            new_password = form.new_password.data
            password_hash = pwd_context.hash(new_password)
            db.execute('update users set password = ? where id = ?', \
                (password_hash, user_id))
            db.commit()
            flash('Password updated')
            return redirect(url_for('main.main_view'))
        else:
            flash('The current password you submitted \
                did not match the password in the db')
    return render_template('change_password.html', form=form)


@auth.route('account/reset_password', methods=['GET', 'POST'])
def request_password_reset():
    form = RequestPasswordResetForm()
    if form.validate_on_submit(): # Verify that email is not already in use
        email = form.email.data
        db = get_db()
        cur = db.execute('select id from users where email is ?', (email,))
        row = cur.fetchone()
        if row != None:
            user_id = row[0]
            token = generate_confirmation_token(user_id)
            send_email(email, 'Link to reset your password',
                       'email/reset_password', token=token)
            flash('A link to reset your password has been sent.')
            return redirect(url_for('auth.login'))
        else:
            flash('That email is not registered')
            return redirect(url_for('auth.request_password_reset'))
    return render_template('reset_password.html', form=form)


@auth.route('account/reset_password/<token>', methods=['GET', 'POST'])
def confirm_password_reset(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except:
        flash('The password reset link is invalid or has expired.')
        return redirect(url_for('auth.request_password_reset'))
    if not data.get('confirm'):
        flash('The password reset link is invalid or has expired.')
        return redirect(url_for('auth.request_password_reset'))
    user_id = data.get('confirm')
    form = SetNewPasswordForm()
    if form.validate_on_submit():
        new_password = form.new_password.data
        password_hash = pwd_context.hash(new_password)
        db = get_db()
        db.execute('update users set password = ? where id = ?', \
            (password_hash, user_id))
        db.commit()
        flash('Password updated—you can now log in.')
        return redirect(url_for('auth.login'))
    return render_template('set_new_password.html', form=form, token=token)


@auth.route('account', methods=['GET', 'POST'])
@login_required
def manage_account():
    current_user = session.get('current_user')
    db = get_db()
    cur = db.execute('select email from users where id = ?', (current_user,))
    row = cur.fetchone()
    email = row[0]
    return render_template('account.html', email=email)


@auth.route('account/delete_account')
@login_required
def delete_account():
    current_user = session.get('current_user')
    db = get_db()
    cur = db.execute('select email from users where id = ?', \
        (current_user,))
    row = cur.fetchone()
    email = row[0]
    db.execute('update users set email = ?, password = ? where id = ?', \
        (None, None, current_user,))
    db.execute('delete from tasks where creator_id = ?', \
        (current_user,))
    db.commit()
    session['logged_in'] = False
    send_email(email, 'Your account has been deleted at your request',
        'email/account_deleted')
    flash('Your account has been deleted at your request. \
        You are now logged out.')
    return(redirect(url_for('main.main_view')))