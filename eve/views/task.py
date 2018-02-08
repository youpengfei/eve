# -*- coding: UTF-8 -*-
import time
from datetime import datetime

from flask import flash
from flask import redirect, jsonify
from flask import render_template, Blueprint
from flask import request
from flask import url_for
from flask.ext.login import current_user, login_required

import git_utils
from eve import db, gl, app, dingtalk_send
from eve import deploy
from eve.constant import DeployEnv, TaskStatus
from eve.models import Task, Project, Record, TaskAudit

__author__ = 'youpengfei'

mod = Blueprint('task', __name__)


@mod.route('/list')
@login_required
def online_orders():
    user_id = current_user.id
    if request.args.get('page'):
        page = int(request.args.get('page'))
    else:
        page = 1


    all_status = request.args.get('all_status')
    kw = request.args.get('kw', '')
    param = [Task.user_id == user_id, Task.title.like("%" + kw + "%")]
    if not all_status:
        param.append(Task.status.in_([0, 1, 2]))

    query = Task.query.filter(*param)
    count = query.count()
    tasks = query.order_by(Task.created_at.desc()).limit(10).offset((page - 1) * 10).all()
    page_count = int(count / 10 if count % 10 == 0 else int(count / 10) + 1)
    return render_template('task_list.html', tasks=tasks, page_count=page_count, page=page, kw=kw)


@mod.route('/new', methods=['GET'])
@login_required
def add_online_order_page():
    projects = current_user.projects
    dev_projects = list(filter(lambda x: x.level == DeployEnv.DEV.value and x.status == 1, projects))
    pre_release_projects = list(filter(lambda x: x.level == DeployEnv.PRERELEASE.value and x.status == 1, projects))
    prod_projects = list(filter(lambda x: x.level == DeployEnv.PROD.value and x.status == 1, projects))

    return render_template('task_new.html',
                           dev_projects=dev_projects,
                           prod_projects=prod_projects,
                           pre_release_projects=pre_release_projects)


@mod.route('/delete', methods=['GET'])
@login_required
def delete_task():
    task_id = int(request.args.get('taskId'))
    one = Task.query.filter_by(id=task_id).one()
    db.session.delete(one)
    db.session.commit()
    return jsonify(code=200)


@mod.route('/submit/<int:project_id>', methods=['GET'])
@login_required
def submit_task_page(project_id):
    project = Project.query.filter_by(id=project_id).one()
    if project.level != DeployEnv.DEV.value:
        branch_list = map(lambda x: x.name,
                          sorted(gl.projects.get(git_utils.get_project_full_name(project.repo_url)).tags.list(),
                                 key=lambda x: x.commit.committed_date, reverse=True)[:5])
    else:
        branch_list = ['rc', 'canary']

    return render_template('task_submit.html', project=project, branch_list=branch_list, time=int(time.time()))


@mod.route('/submit', methods=['POST'])
@login_required
def add_online_order():
    title = request.form.get('title', None)
    branch = request.form.get('branch', 'rc')
    project_id = int(request.args.get('projectId'))

    project = Project.query.filter(Project.id == project_id, Project.status == 1).one()

    count = Task.query.filter(Task.project_id == project_id, Task.status != TaskStatus.REJECTED.value,
                              Task.status != TaskStatus.FINISHED.value).count()
    if count > 0:
        if project.level != DeployEnv.DEV.value:
            branch_list = map(lambda x: x.name,
                              gl.projects.get(git_utils.get_project_full_name(project.repo_url)).tags.list())
        else:
            branch_list = ['rc', 'canary']
        flash('已经有这个有效任务任务')

        return render_template('task_submit.html', project=project, branch_list=branch_list, time=int(time.time()))

    task = Task()
    task.project_id = project_id
    task.title = title
    task.branch = branch
    task.commit_id = ' '
    task.user_id = current_user.id
    if project.level == 1:
        task.status = 1
    else:
        task.status = 0
    task.link_id = ''
    task.file_transmission_mode = '1'
    db.session.add(task)
    db.session.commit()

    return redirect(url_for('task.online_orders'))


@mod.route('/deploy', methods=['GET'])
@login_required
def deploy_index():
    task_id = int(request.args.get('taskId'))
    task = Task.query.filter_by(id=task_id).one()
    return render_template('task_deploy.html', task=task)


@mod.route('/deploy', methods=['POST'])
@login_required
def deploy_start():
    task_id = int(request.form.get('taskId'))
    try:
        result = deploy.start_deploy(task_id)
        return result
    except Exception as e:
        app.logger.error(e)
        task = Task.query.filter_by(id=task_id).one()
        task.status = 4
        db.session.add(task)
        db.session.commit()
        return jsonify(code=500, message="出现异常请联系管理员")


@mod.route('/get-process', methods=['GET'])
@login_required
def task_process():
    task_id = int(request.args.get('taskId'))
    if Record.query.filter_by(task_id=task_id).count() > 0:
        one = Record.query.filter_by(task_id=task_id).order_by(Record.action.desc()).limit(1).one()
        return jsonify(data={"code": 200, "percent": one.action})
    else:
        return jsonify(data={"code": 200, "percent": 0})


@mod.route('/rollback', methods=['GET'])
@login_required
def rollback_task():
    task_id = int(request.args.get('taskId'))
    task = Task.query.filter_by(id=task_id).one()
    if not task:
        return jsonify(code=404, message="任务不存在")

    if task.enable_rollback == 0:
        return jsonify(code=403, message="这个任务不能回滚")

    if task.user_id != current_user.id:
        return jsonify(code=403, message="这个不是你的任务")

    if task.link_id == task.ex_link_id:
        return jsonify(code=500, message="不可以回滚两次")

    project = task.project
    status = 1 if project.audit == 0 else 0
    rollback_task_model = Task()
    rollback_task_model.status = status
    rollback_task_model.action = 1
    rollback_task_model.link_id = task.ex_link_id
    rollback_task_model.title = task.title + '-回滚'
    rollback_task_model.user_id = current_user.id
    rollback_task_model.project_id = task.project.id
    rollback_task_model.file_transmission_mode = task.file_transmission_mode
    rollback_task_model.commit_id = task.commit_id
    rollback_task_model.branch = task.branch
    rollback_task_model.created_at = datetime.now()
    rollback_task_model.updated_at = datetime.now()
    rollback_task_model.enable_rollback = 0
    db.session.add(rollback_task_model)
    db.session.commit()
    url = '/task/' if project.audit == 1 else '/task/deploy?taskId=%d' % rollback_task_model.id
    return jsonify(data={"url": url})


@mod.route('/audit', methods=['POST'])
@login_required
def task_audit():
    """
    任务审核
    :return: 返回任务列表
    """
    task_id = int(request.form.get('task_id'))
    task_query = Task.query.filter_by(id=task_id)
    if task_query.count() == 1:
        task = task_query.one()
        project = task.project
        task_audit = TaskAudit()
        task_audit.assign_user_id = request.form.get('assign_user_id')
        task_audit.request_user_id = current_user.id
        task_audit.task_id = task_id
        task_audit.deploy_reason = request.form.get('deploy_reason')
        task_audit.project_id = project.id
        db.session.add(task_audit)
        # content_msg = "%s项目要上线,上线理由是：%s" % (project.name, task_audit.deploy_reason)
        # dingtalk_send.sendLinkMsg("http://127.0.0.1:5000/task/audit_list", content_msg)
        db.session.commit()
    else:
        flash("这个任务不存在")

    return redirect(url_for('task.online_orders'))


@mod.route('/audit_list', methods=['GET'])
@login_required
def audit_list():
    """
    任务审核
    :return: 返回任务列表
    """
    query = TaskAudit.query.filter(TaskAudit.assign_user_id == current_user.id)
    all_task = query.all()
    count = query.count()
    page_count = int(count / 10 if count % 10 == 0 else int(count / 10) + 1)

    return render_template('audit_list.html', all_task=all_task, page_count=page_count, page=1, active='task_audit')


@mod.route('/audit_count', methods=['GET'])
@login_required
def audit_count():
    """
    任务审核
    :return: 返回任务列表
    """
    count = TaskAudit.query.join(Task, Task.id == TaskAudit.task_id) \
        .filter(TaskAudit.assign_user_id == current_user.id,
                Task.status == 0,
                TaskAudit.flag == 0).count()

    return jsonify(count=count, code=200)


@mod.route('/audit', methods=['GET'])
@login_required
def audit_task():
    """
    审核任务
    :return:
    不是管理员返回 {code:403,message:"没有权限"}
    任务不存在     {code:404,message:"任务不存在"}
    """
    if current_user.role != 2:
        return jsonify(code=403, message="没有权限")
    task_id = request.args.get('id')
    status = request.args.get('status')
    if task_id is None:
        return jsonify(code=404, message="任务不存在")
    task = Task.query.filter_by(id=int(task_id)).one()
    task.status = int(status)
    db.session.add(task)
    db.session.commit()

    if status == '2':
        task_audit_query = TaskAudit.query.filter(TaskAudit.task_id == task_id, TaskAudit.flag == 0)

        if task_audit_query.count() > 0:
            one = task_audit_query.one()
            one.flag = '1'
            one.reject_reason = request.args.get("reject_reason")
            db.session.add(one)
            db.session.commit()
    else:
        task_audit_query = TaskAudit.query.filter(TaskAudit.task_id == task_id, TaskAudit.flag == 0)

        if task_audit_query.count() > 0:
            one = task_audit_query.one()
            one.flag = '1'
            db.session.add(one)
            db.session.commit()

    return jsonify(status="审核通过" if task.status == 1 else "审核拒绝", code=0)
