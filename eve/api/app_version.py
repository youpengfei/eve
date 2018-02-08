# -*- coding: UTF-8 -*-

import flask
from flask import Blueprint, request
from flask_login import login_required, current_user, abort

from eve import app, db
import ios_utils
from eve.models import AppVersion
from eve.schema import app_version_schemas, app_version_schema

api = Blueprint('app-version-api', __name__)


@api.route("/app-versions", methods=['GET'])
@login_required
def get_app_versions():
    """
    获取到版本列表可以查询之前发布的版本
    """
    page = int(request.args.get('page', 1))
    client_type = request.args.get("client_type", None)
    query = AppVersion.query

    if client_type:
        query = query.filter_by(client_type=client_type)

    total_count = query.count()
    app_versions = query.order_by(AppVersion.flag.desc(),
                                  AppVersion.created_date.desc())\
        .limit(10).offset((page - 1) * 10).all()
    dump_data = app_version_schemas.dump(app_versions).data
    return flask.jsonify(data=dump_data, total_count=total_count)


@api.route("/app-versions/<client_type>", methods=['GET'])
def get_app_version(client_type):
    """
    获取到指定客户端的app
    """
    app_version = AppVersion.query.filter(
        AppVersion.client_type == client_type,
        AppVersion.flag == 1,
        AppVersion.state == 2).one()
    dump_data = {}
    dump_obj = app_version_schema.dump(app_version).data
    for arg in dump_obj:
        dump_data[underline_to_camel(arg)] = dump_obj[arg]
    return flask.jsonify(dump_data)


def underline_to_camel(underline_format):
    '''
        下划线命名格式驼峰命名格式
    '''
    camel_format = ''
    if isinstance(underline_format, str):
        i = 0
        for _s_ in underline_format.split('_'):
            if i > 0:
                camel_format += _s_.capitalize()
            else:
                camel_format += _s_
            i = i + 1

    return camel_format


@api.route("/app-versions", methods=['POST'])
@login_required
def create_app_version():
    """
    创建一个发布版本
    """
    app_version_web = request.json
    app_version = AppVersion()
    for arg in app_version_web:
        app_version.__setattr__(arg, app_version_web.get(arg))

    app_version.created_by = current_user.email
    app_version.last_modified_by = current_user.email
    app_version.flag = '1'
    app_version.state = '1'
    db.session.add(app_version)
    db.session.commit()
    return 'app'


@api.route("/app-versions/<int:app_version_id>", methods=['DELETE'])
@login_required
def delete_app_version(app_version_id):
    """
    创建一个发布版本
    """
    app_version = AppVersion.query.filter_by(id=app_version_id).one()
    app_version.flag = '0'
    db.session.add(app_version)
    db.session.commit()
    return flask.jsonify(data="删除成功", code=200)


@api.route("/app-versions/state", methods=['PUT'])
@login_required
def update_app_version_state():
    """
    更新发布任务
    """
    app_version_web = request.json
    if not app_version_web['id']:
        abort(406)
    app_version = AppVersion.query.\
        filter_by(id=int(app_version_web['id'])).one()
    if not app_version:
        return flask.jsonify(data="没有这个id", code=200)
    if app_version_web['state']:
        app_version.state = app_version_web['state']
    AppVersion.query.filter(AppVersion.client_type == app_version.client_type,
                            AppVersion.id != app_version.id
                            )\
        .update(dict(flag='0'))

    if app_version.client_type == 'ios' and app_version.state == 2:
        if ios_utils.get_version() != app_version.app_version:
            return flask.jsonify(
                data='更新失败，itunes版本是%s，更新版本是%s' %
                (ios_utils.get_version(), app_version.app_version), code=500)

    db.session.add(app_version)
    db.session.commit()

    return flask.jsonify(data="更新成功", code=200)
