# -*- coding: UTF-8 -*-

import flask
from flask import Blueprint, request
from flask_login import current_user, login_required
from werkzeug.exceptions import abort

from eve.constant import TaskStatus
from eve.models import Task, task_schema, task_schemas, Record, TaskAudit, record_schemas
from eve import app, db, deploy

api = Blueprint('api', __name__)


@api.route("/tasks", methods=["GET"])
@login_required
def task_list():
    """
    任务列表
    :return: 带分页的任务列表
    """
    user_id = current_user.id
    page = int(request.args.get('page', 1))

    status = request.args.get('status')
    kw = request.args.get('kw', '')
    param = [Task.user_id == user_id, Task.title.like("%" + kw + "%")]
    if status:
        param.append(Task.status == status)

    query = Task.query.filter(*param)
    count = query.count()
    tasks = query.order_by(Task.created_at.desc()).limit(
        10).offset((page - 1) * 10).all()
    return flask.jsonify(data=task_schemas.dump(tasks).data, total_count=count)


@api.route("/tasks", methods=["POST"])
@login_required
def add_task():
    """
    新增任务
    :return: 创建成功的任务
    """
    task_web = request.json

    if not task_web:
        abort(400)

    user_id = current_user.id

    project_id = int(task_web['project_id'])

    query = Task.query.filter(Task.project_id == project_id,
                              Task.status != TaskStatus.REJECTED.value,
                              Task.status != TaskStatus.FINISHED.value,
                              Task.status != TaskStatus.PROCESSING.value)
    if query.count() > 0:
        task = query.all()[0]
        return flask.jsonify(code=406, data="这个任务已经有人在发布了，发布人是:%s" % task.user.email)

    task = Task()

    for arg in task_web:
        if arg == "project":
            continue
        task.__setattr__(arg, task_web.get(arg))

    if task_web['projectLevel'] == '1' or current_user.role == 2:
        task.status = TaskStatus.APPROVED.value
    else:
        task.status = TaskStatus.NEW.value

    task.user_id = user_id
    # 全量上线
    task.file_transmission_mode = 1
    db.session.add(task)

    db.session.commit()
    return flask.jsonify(data=task_schema.dump(task).data, code=200)


@api.route("/tasks/<int:task_id>", methods=["delete"])
@login_required
def delete_task(task_id):
    """
    删除任务
    :return: 任务删除成功
    """

    task = Task.query.filter_by(id=task_id).one()
    if not task:
        return flask.jsonify(data="删除的任务不存在", code=500)

    if task.status == TaskStatus.FINISHED.value:
        return flask.jsonify(data="任务已经完成了", code=500)

    # 删除关联的审核记录
    task_audits = TaskAudit.query.filter_by(task_id=task_id)
    if task_audits.count() > 0:
        task_audits.delete(synchronize_session=False)

    # 删除关联的record记录
    records = Record.query.filter_by(task_id=task_id)
    if records.count() > 0:
        records.delete(synchronize_session=False)

    # 删除任务
    db.session.delete(task)
    db.session.commit()

    return flask.jsonify(data="删除成功", code=200)


@api.route("/tasks/<int:task_id>", methods=["GET"])
@login_required
def get_task_by_id(task_id):
    """
    获取指定id的任务
    :return: 任务不存在返回404
    """

    query = Task.query.filter_by(id=task_id)
    if query.count() == 0:
        abort(404)

    return flask.jsonify(data=task_schema.dump(query.one()).data, code=200)


@api.route('/tasks/release', methods=['PUT'])
@login_required
def deploy_start():
    """
    任务发布
    :return:
    """
    task_id = int(request.form.get('taskId'))
    task = Task.query.filter_by(id=task_id).one()

    try:
        task.status = TaskStatus.PROCESSING
        db.session.add(task)
        db.session.commit()
        result = deploy.start_deploy(task_id)
        return result
    except Exception as e:
        app.logger.error(e)
        task.status = 4
        db.session.add(task)
        db.session.commit()
        return flask.jsonify(code=500, message="出现异常请联系管理员")


@api.route('/tasks/<int:task_id>/processes', methods=['GET'])
@login_required
def task_process(task_id):
    """
    获取发布进度
    :return:
    """
    if Record.query.filter_by(task_id=task_id).count() > 0:
        one = Record.query.filter_by(task_id=task_id).order_by(
            Record.action.desc()).limit(1).one()
        return flask.jsonify(data=one.action, code=200)
    else:
        return flask.jsonify(data=0, code=200)


@api.route("/task-process/<int:task_id>", methods=["GET"])
@login_required
def get_task_process(task_id):
    """
     获取任务进度
    :param task_id: 任务id
    """
    if Record.query.filter_by(task_id=task_id).count() > 0:
        all = Record.query.filter_by(task_id=task_id).order_by(Record.action.desc()).all()
        return flask.jsonify(data=record_schemas.dump(all).data, code=200)

    return flask.jsonify(data=[], code=200)
