# -*- coding: UTF-8 -*-
import uuid

import bcrypt
import flask
import gitlab
from flask import Blueprint, request
from flask_login import login_required, current_user
from flask_mail import Message
from sqlalchemy import or_

from eve import mail, app
from eve.models import Project, User, user_schema, user_schemas, TaskAudit
from .. import db, gl

api = Blueprint('user-api', __name__)


@api.route("/users")
@login_required
def user_list():
    if current_user.role != 2:
        return flask.jsonify(data="只有管理员拥有这项技能", code="403")
    kw = request.args.get('kw')
    query = User.query
    page = int(request.args.get('page', "1"))

    if kw:
        query = query.filter(or_(User.username.like(
            '%' + kw + '%'), User.email.like('%' + kw + '%')))

    users = query.limit(10).offset((page - 1) * 10).all()
    total_count = query.count()

    return flask.jsonify(data=user_schemas.dump(users).data, total_count=total_count)


@api.route("/users/<int:user_id>/status/<int:status>", methods=["PUT"])
@login_required
def update_status(user_id, status):
    """
    更新用户状态，主要用于用户冻结和解冻。冻结和解冻都关联gitlab
    :param user_id: 用户id int
    :param status: 状态 int
    :return: 成功提示消息
    """
    if current_user.role != 2:
        return flask.jsonify(data="只有管理员拥有这项技能", code="403")
    user = User.query.filter_by(id=user_id).one()
    user.status = status
    db.session.add(user)

    if request.args.get('gitlab') and status == 2:
        ser = None
        try:
            ser = gl.users.get_by_username(user.username)
        except Exception as e:
            app.logger.error(e)

        if ser:
            ser.block()

    if status == 1:
        ser = None
        try:
            ser = gl.users.get_by_username(user.username)
        except Exception as e:
            app.logger.error(e)

        if ser:
            ser.unblock()

    db.session.commit()
    return flask.jsonify(data="成功")


@api.route("/users", methods=["POST"])
@login_required
def add_user():
    """
    新增用户，可以绑定项目，绑定gitlab，发送密码给被创建人
    :return: 正常提示成功
    """
    if current_user.role != 2:
        return flask.jsonify(data="只有管理员拥有这项技能", code="403")

    user_web = request.json
    user = User.query.filter_by(email=user_web['email'])
    if not user:
        return flask.jsonify(data="用户已经存在", code="500")
    else:
        user = User()

    for arg in user_web:
        if (arg == 'projects'):
            continue
        user.__setattr__(arg, user_web.get(arg))

    random_passwd = uuid.uuid1().__str__()
    user.is_email_verified = 1
    user.password_hash = bcrypt.hashpw(
        random_passwd.encode('utf-8'), bcrypt.gensalt())
    user.auth_key = ''

    if user_web['gitlab']:
        try:
            # 创建gitlab用户
            gl_user = gl.users.create({'email': user.email,
                                       'username': user.username,
                                       'password': random_passwd,
                                       'name': user.username})
            # 绑定RD组的开发权限给当前用户
            gl.groups.get('RD').members.create(
                {'user_id': gl_user.id, 'access_level': gitlab.DEVELOPER_ACCESS})
        except gitlab.GitlabCreateError as ex:
            return flask.jsonify(data="gitlab账号创建失败，原因为:%s" % ex.error_message, code="500")

    # 绑定当前projects
    projects_ = user_web['projects']

    if not projects_:
        return flask.jsonify(data="设置绑定项目不然没有意义", code="500")

    count = Project.query.filter(Project.id.in_(projects_)).count()
    if count > 0:
        project = Project.query.filter(Project.id.in_(projects_)).all()
        user.projects = project
    else:
        return flask.jsonify(data="绑定的项目不存在", code=500)

    # 创建完成后需要发邮件给用户告诉他密码
    msg = Message('账号已经开通', sender='eva@notice.baokeyun.com', recipients=[user.email])
    msg.body = ''
    msg.html = '<p>恭喜你账号已经开通，用户名为你的邮箱，密码为：%s。(切记不要告诉任何人)!</p> ' % random_passwd
    if user_web['gitlab']:
        msg.html += "<p>恭喜你gitlab账号已开通，用户名为你的邮箱，密码为:%s。(切记不要告诉任何人)!</p> " % random_passwd
    mail.send(msg)

    # 提交事务
    db.session.add(user)
    db.session.commit()

    return flask.jsonify(data=user_schema.dump(user).data, code=200)


@api.route("/current-user")
@login_required
def get_current_user():
    return flask.jsonify(data=user_schema.dump(current_user).data, code=200)


@api.route("/users/admins")
@login_required
def admin_list():
    admin_list = User.query.filter(User.role == 2, User.status != 2).all()
    return flask.jsonify(data=user_schemas.dump(admin_list).data, code=200)


@api.route("/user/current-user", methods=['PUT'])
@login_required
def modify_current_user():
    """
    修改当前用户的密码，传入参数必须包含 密码和确认密码 ，必须是json格式的数据
    :return:  返回一个成功的消息
    """
    current_user_modified = request.json

    if not current_user_modified:
        flask.jsonify(data="必须传json格式的数据", code=406)

    if not current_user_modified['password_confirm']:
        flask.jsonify(data="确认密码为必填项", code=406)

    if not current_user_modified['password']:
        flask.jsonify(data="密码为必填项", code=406)

    if current_user_modified['password_confirm'] != current_user_modified['password']:
        flask.jsonify(data="密码和确认密码不同", code=406)

    # 获取到当前的用户id
    current_user_id = current_user.id
    current_user_active = User.query.filter_by(id=current_user_id).one()
    current_user_active.password_hash = bcrypt.hashpw(current_user_modified['password'].encode('utf-8'),
                                                      bcrypt.gensalt())
    db.session.add(current_user_active)
    db.session.commit()
    return flask.jsonify(data="修改成功", code=200)
