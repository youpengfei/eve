# -*- coding: UTF-8 -*-
import bcrypt
import gitlab
from flask import flash, jsonify
from flask import request, redirect, render_template, Blueprint
from flask import url_for
from flask.ext.login import login_user, login_required, current_user, logout_user

from .. import app, db, login_manager, gl
from ..models import User, TaskAudit, Task

__author__ = 'youpengfei'

mod = Blueprint('user', __name__)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        remeber_me = request.form.get('remember_me', False)
        query = User.query.filter_by(email=email)
        if query.count() == 1:
            user = query.one()
            if user is not None and user.verify_password(password):
                if user.status == 2:
                    return render_template('login.html', error_message='用户账号已经被冻结了，请先解冻')

                login_user(user, remember=remeber_me)
                return redirect('/')
            else:
                return render_template('login.html', error_message='用户名或者密码错误')
        else:
            return render_template('login.html', error_message='用户名或者密码错误')
    else:
        return render_template('login.html')


@mod.route('/user/administrator', methods=['GET'])
@login_required
def admin_list():
    task_id = request.args.get('task_id')
    count = TaskAudit.query.join(Task, Task.id == TaskAudit.task_id) \
        .filter(TaskAudit.task_id == task_id, TaskAudit.flag == 0).count()

    admin_list = User.query.filter_by(role=2).all()

    return render_template("admin_list.html", admin_list=admin_list, task_id=task_id, count=count)


@mod.route('/user/list', methods=['GET', 'POST'])
@login_required
def user_list():
    users = User.query.all()
    return render_template('user_list.html', users=users)


@app.route('/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def user_profile(user_id):
    user = User.query.filter_by(id=user_id).one()
    return render_template("user_profile.html", user_info=user)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")


@login_manager.user_loader
def get_user(ident):
    return User.query.get(int(ident))


@app.route('/user/reset-password', methods=['GET'])
@login_required
def reset_password_page():
    return render_template("reset-password.html")


@app.route('/user/reset-password', methods=['POST'])
@login_required
def reset_password():
    password = request.form.get('password')
    confirm_password = request.form.get('confirmPassword')
    if password != confirm_password:
        flash("密码不能跟确认密码不同")
    else:
        user = User.query.filter_by(id=current_user.id).one()
        user.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        db.session.commit()
    return redirect(url_for('logout'))
