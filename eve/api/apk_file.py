# -*- coding: UTF-8 -*-

import flask
from flask import Blueprint, request
from flask_login import login_required

import oss_util
from eve import app
from eve.models import AppVersion
from eve.schema import app_version_schema, app_version_schemas

api = Blueprint('apk-file-apk', __name__)


@api.route('/apk', methods=['POST'])
@login_required
def upload_apk():
    '''
    上传apk文件
    '''
    app.logger.info(request.files)
    file = request.files['file']
    app.logger.info(file.filename)
    download_url_and_size = oss_util.upload_apk_to_oss(file)
    return flask.jsonify(download_url=download_url_and_size[0],
                         file_size=float(download_url_and_size[1])/1000)


@api.route('/apk/<file_name>', methods=['DELETE'])
@login_required
def delete_apk(file_name):
    '''
    上传apk文件
    '''
    oss_util.delete_apk_of_oss(file_name)
    return flask.jsonify(data="删除成功", code=200)
