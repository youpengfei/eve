# -*- coding: UTF-8 -*-
"""
上线任务审计
"""
import flask
from flask import Blueprint, request
from flask_login import current_user, login_required
from werkzeug.exceptions import abort

from eve import app, db, deploy
from eve.constant import TaskStatus
from eve.models import (Record, Task, TaskAudit, task_audit_schemas,
                        task_schema, task_schemas)

api = Blueprint('api_task_audit', __name__)


@api.route('/tasks/audits', methods=['GET'])
@login_required
def audit_list():
    """
    任务审核
    :return: 返回任务列表
    """
    if current_user.role != 2:
        abort(403)

    page = int(request.args.get('page', 1))
    kw = request.args.get('kw', '')
    param = [Task.title.like("%" + kw + "%")]
    if request.args.get('status'):
        param.append(Task.status == request.args.get('status'))

    query = TaskAudit.query.join(
        Task, Task.id == TaskAudit.task_id).filter(*param)

    count = query.count()
    task_audit_list = []
    if count > 0:
        task_audit_list = query.limit(10).offset((page - 1) * 10).all()

    return flask.jsonify(data=task_audit_schemas.dump(task_audit_list).data,
                         total_count=count, code=200)


@api.route('/tasks/audits', methods=['POST'])
@login_required
def add_audit():
    """
    发起审核
    :return: 返回任务列表
    """

    task_audit_web = request.json
    task_id = task_audit_web['task_id']
    task_query = Task.query.filter_by(id=task_id)
    if task_query.count() == 1:
        task = task_query.one()
        project = task.project
        task_audit = TaskAudit()
        task_audit.assign_user_id = task_audit_web['assign_user_id']
        task_audit.request_user_id = current_user.id
        task_audit.task_id = task_id
        task_audit.deploy_reason = task_audit_web['deploy_reason']
        task_audit.project_id = project.id
        db.session.add(task_audit)
        # content_msg = "%s项目要上线,上线理由是：%s" % (project.name, task_audit.deploy_reason)
        # dingtalk_send.sendLinkMsg("http://127.0.0.1:5000/task/audit_list", content_msg)
        db.session.commit()
    else:
        return flask.jsonify(data="任务不存在", code=500)

    return flask.jsonify(data="任务创建成功", code=200)


@api.route('/tasks/audits/<int:audit_id>', methods=['DELETE'])
@login_required
def delete_audit(audit_id):
    """
    删除审核
    :return: 删除审计任务
    """
    query_filter = TaskAudit.query.filter(
        TaskAudit.id == audit_id, TaskAudit.assign_user_id == current_user.id)
    if query_filter.count() == 0:
        abort(404)

    query_filter.delete()
    db.session.commit()
    return flask.jsonify(data="删除成功", code=200)


@api.route('/tasks/<int:task_id>/audits/<int:audit_id>', methods=['PUT'])
@login_required
def audit_task(task_id, audit_id):
    """
    审核任务
    :return:
    不是管理员返回 {code:403,message:"没有权限"}
    任务不存在     {code:404,message:"任务不存在"}
    """
    if current_user.role != 2:
        return flask.jsonify(code=403, message="没有权限")
    status = request.form.get('status')
    if task_id is None:
        return flask.jsonify(code=404, message="任务不存在")
    task = Task.query.filter_by(id=int(task_id)).one()
    task.status = int(status)
    db.session.add(task)
    db.session.commit()

    if status == '2':
        task_audit_query = TaskAudit.query.filter(
            TaskAudit.task_id == task_id, TaskAudit.flag == 0)
        if task_audit_query.count() > 0:
            one = task_audit_query.one()
            one.flag = '1'
            one.reject_reason = request.form.get("reject_reason")
            db.session.add(one)
            db.session.commit()
    else:
        task_audit_query = TaskAudit.query.filter(
            TaskAudit.task_id == task_id, TaskAudit.flag == 0)

        if task_audit_query.count() > 0:
            one = task_audit_query.one()
            one.flag = '1'
            db.session.add(one)
            db.session.commit()

    return flask.jsonify(status="审核通过" if task.status == 1 else "审核拒绝", code=0)
