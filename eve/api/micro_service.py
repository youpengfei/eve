# -*- coding: UTF-8 -*-
"""
微服务列表和运行情况列表
"""

import requests
from flask import jsonify
from flask import json
from flask import request
import flask
from flask import Blueprint
from eve import app
import supervisor_utils
from flask_login import login_required

api = Blueprint('micro-service', __name__)

micro_server_config = {
    '1': {
        'label': 'test',
        'ip': 'http://gaia.baokeyunguanjia.com',
        'token': 'Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJhZG1pbiIsImF1dGgiOiJST0xFX0FETUlOLFJPTEVfVVNFUiIsImV4cCI6MTUwNTM1ODk2OX0.XF2AQU20II1elAswc2ChY_yudfKfqv1fSzlJCK7alGzbESew-Xw6bsHDr4P-Sm7uZJKpVijVmgx-yA4JQyH5Bw'
    },
    '2': {
        'label': 'prod',
        'ip': 'https://gaia.baokeyun.com',
        'token': 'Bearer eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiJhZG1pbiIsImF1dGgiOiJST0xFX0FETUlOLFJPTEVfVVNFUiIsImV4cCI6MTUwNTYyNTI3NX0.MNPft6MeAAuUeShOalhTSiG2Zva5LsQKOb7v-rb_dah_qS0-M6FNWnTA04OLYAOt2g6S1HrLyY439icomg1zYg'
    }
}


@api.route("/micro-services", methods=["GET"])
@login_required
def get_all_service():

    label_id = request.args.get('label', '1')
    app.logger.info(label_id)
    profile = micro_server_config.get(label_id)
    # micro_server_config.get()

    headers = {'Authorization': profile.get('token')}
    get = requests.get(
        profile.get('ip') + "/api/eureka/applications",
        headers=headers
    )
    # 获取到所有应用的名字
    app_names = list(map(lambda x: x['name'], get.json()['applications']))

    return flask.jsonify(applications=get.json()['applications'], app_names=app_names)
