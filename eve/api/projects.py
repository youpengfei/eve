# -*- coding: UTF-8 -*-

import flask
from flask import Blueprint, request
from flask_login import login_required
from werkzeug.exceptions import abort

from eve.models import Project, project_schemas, project_list_schemas, project_schema
from eve import db, app

api = Blueprint('project-api', __name__)


@api.route("/projects", methods=['GET'])
@login_required
def project_list():
    all_project = Project.query.filter_by(status=1).all()
    return flask.jsonify(data=project_schemas.dump(all_project).data)


@api.route("/project-configs", methods=['GET'])
@login_required
def project_list_page():
    page = int(request.args.get('page', 1))
    query = Project.query
    all_project = []
    kw = request.args.get('kw', None)
    if kw:
        query = query.filter(Project.name.like('%' + kw + '%'))

    count = query.count()

    if count > 0:
        all_project = query.order_by(Project.id.desc()).limit(
            10).offset((page - 1) * 10).all()

    return flask.jsonify(data=project_list_schemas.dump(all_project).data, count=count)


@api.route("/project-configs/<int:project_id>", methods=['GET'])
@login_required
def get_project(project_id):
    project = Project.query.filter_by(id=project_id).one()

    return flask.jsonify(data=project_schema.dump(project).data, code=200)


@api.route("/project-configs/<int:project_id>", methods=['DELETE'])
@login_required
def delete_project(project_id):
    """
    删除项目配置信息,如果这个配置有任务则设置为任务失效
    """
    query = Project.query.filter_by(id=project_id)
    if query.count() > 0:
        deleted_project = query.one()
        if len(deleted_project.tasks) > 0:
            deleted_project.status = 2
            db.session.add(deleted_project)
        else:
            query.delete()

    db.session.commit()
    return flask.jsonify(data="删除成功", code=200)


@api.route("/project-configs", methods=['POST'])
@login_required
def add_project():
    """
    新建一个项目
    """
    project_web = request.json
    project = Project()
    for arg in project_web:
        project.__setattr__(arg, project_web.get(arg))

    if not project.name or len(project.name) == 0:
        return flask.jsonify(data="项目名称不能为空", code=406)
    else:
        if Project.query.filter_by(name=project.name).count() > 0:
            return flask.jsonify(data="项目名称已经存在了", code=406)

    if not project.repo_url or len(project.repo_url) == 0 or not str.startswith(project.repo_url, "git@"):
        return flask.jsonify(data="项目地址不能为空，且必须是ssh开头", code=406)

    db.session.add(project)
    db.session.commit()

    return flask.jsonify(data=project_schema.dump(project).data, code=200)


@api.route("/project-configs/<int:config_id>/duplicate", methods=['POST'])
@login_required
def clone_project(config_id):
    project = Project.query.filter_by(id=config_id).one()
    project_clone = Project()

    for var in vars(project):
        if var != 'id' and var != '_sa_instance_state':
            project_clone.__setattr__(var, project.__getattribute__(var))

    project_clone.name += "-clone"
    db.session.add(project_clone)
    db.session.commit()

    return flask.jsonify(code=None, message="成功")


@api.route("/project-configs", methods=['PUT'])
@login_required
def edit_project():
    """
    新建一个项目
    """
    project_web = request.json

    if not project_web['id']:
        return flask.jsonify(data="id为必传项", code=406)

    project_count = Project.query.filter_by(id=int(project_web['id'])).count()

    if project_count > 0:

        project = Project.query.filter_by(id=int(project_web['id'])).one()

        for arg in project_web:
            if arg == 'users' or arg == 'tasks':
                continue
            project.__setattr__(arg, project_web.get(arg))

        if not project.name or len(project.name) == 0:
            return flask.jsonify(data="项目名称不能为空", code=406)
        else:
            if Project.query.filter(Project.name == project.name, Project.id != project.id).count() > 0:
                return flask.jsonify(data="项目名称已经存在了", code=406)

        if not project.repo_url or len(project.repo_url) == 0 or not str.startswith(project.repo_url, "git@"):
            return flask.jsonify(data="项目地址不能为空，且必须是ssh开头", code=406)

        db.session.add(project)
    else:
        return flask.jsonify(data="项目不存在，不能修改", code="406")

    db.session.commit()

    return flask.jsonify(data=project_schema.dump(project).data, code=200)
