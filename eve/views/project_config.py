# -*- coding: UTF-8 -*-

from flask import redirect
from flask import render_template, Blueprint, jsonify
from flask import request
from flask import url_for
from flask.ext.mail import Message
from flask_login import login_required, current_user

from eve import db, mail
from eve.models import Project, Group, User

__author__ = 'youpengfei'

mod = Blueprint('project_config', __name__)


@mod.route('/list', methods=['GET'])
@login_required
def project_config_list():
    kw = request.args.get('kw')
    if kw:
        projects = Project.query.filter(Project.name.like('%' + kw + '%')).all()
    else:
        kw = ''
        projects = Project.query.all()

    return render_template('project_config_list.html', projects=projects, kw=kw)


@mod.route('/edit/', methods=['GET'])
@login_required
def project_config_edit_index():
    project_id = int(request.args.get('projectId'))
    project = Project.query.filter_by(id=project_id).one()
    return render_template('project_config_edit.html', project=project)


@mod.route('/edit/', methods=['POST'])
@login_required
def project_config_edit():
    project_id = int(request.form.get('projectId'))
    project = Project.query.filter_by(id=project_id).one()
    for arg in request.form:
        project.__setattr__(arg, request.form.get(arg))
    project.audit = request.form.get('audit', 0)
    project.status = request.form.get('status', 0)
    db.session.add(project)
    db.session.commit()

    return redirect(url_for('project_config.project_config_list'))


@mod.route('/new', methods=['GET'])
@login_required
def project_config_new_page():
    return render_template('project_config_new.html', project=None)


@mod.route('/clone', methods=['POST'])
@login_required
def clone_project_config():
    project_id = int(request.form.get('projectId'))
    project = Project.query.filter_by(id=project_id).one()
    project_clone = Project()

    for var in vars(project):
        if var != 'id' and var != '_sa_instance_state':
            project_clone.__setattr__(var, project.__getattribute__(var))
    project_clone.name += "-clone"
    db.session.add(project_clone)
    db.session.commit()

    return jsonify(code=None, message="成功")


@mod.route('/new', methods=['POST'])
@login_required
def project_config_new():
    project = Project()
    for arg in request.form:
        project.__setattr__(arg, request.form.get(arg))
    project.audit = request.form.get('audit', 0)
    project.status = request.form.get('status', 0)
    project.user_id = current_user.id
    db.session.add(project)
    db.session.commit()

    return render_template('project_config_new.html', project=project)


@mod.route('/delete', methods=['GET'])
@login_required
def delete_project_config():
    project_id = request.args.get('projectId')
    project = Project.query.filter_by(id=project_id).one()
    db.session.delete(project)
    db.session.commit()
    return jsonify()


@mod.route('/preview/', methods=['GET'])
@login_required
def project_review():
    project_id = int(request.args.get('projectId'))
    project = Project.query.filter_by(id=project_id).one()
    return render_template('project_preview.html', project=project)


@mod.route('/group/', methods=['GET'])
@login_required
def project_group():
    project_id = int(request.args.get('projectId'))
    groups = Group.query.filter_by(project_id=project_id).all()
    project = Project.query.filter_by(id=project_id).one()
    users = User.query.filter(User.id.in_(map(lambda x: x.user_id, groups))).all()
    all_users = User.query.all()
    return render_template('project_group.html', users=users, project=project, all_users=all_users)


@mod.route('/group/', methods=['POST'])
@login_required
def add_group():
    project_id = int(request.args.get('projectId'))
    user_ids = request.form.getlist('users')
    user_emails = []
    for user_id in user_ids:
        group = Group(user_id=int(user_id), project_id=project_id)
        db.session.add(group)
        user_emails.append(User.query.filter_by(id=user_id).one().email)
    project = Project.query.filter_by(id=project_id).one()

    msg = Message('已经被绑定到项目', sender='eva@notice.baokeyun.com', recipients=user_emails)
    msg.html = '<b>' + '您已经被绑定到项目 【%s】' % (project.name) + '，您可以愉快的发布系统了</b> '
    mail.send(msg)

    db.session.commit()

    return redirect(url_for('project_config.project_group', projectId=project_id))


@mod.route('/group/', methods=['DELETE'])
@login_required
def delete_group():
    id = int(request.args.get('id'))
    group = Group.query.filter_by(id=id)
    db.session.delete(group)
    return jsonify(data='success')
