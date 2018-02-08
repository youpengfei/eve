# -*- coding: UTF-8 -*-
"""
ECS服务器列表及相关信息
"""

from flask import Blueprint
from flask_login import login_required
import ecs_utils
from flask import jsonify
import flask

api = Blueprint('aliyun_ecs', __name__)

@api.route('/ecs',methods=['GET'])
@login_required
def get_all_ecs():
    ecslist = ecs_utils.ecs_list()
    return jsonify(data=list(ecslist))


@api.route('/ecs/detail/<string:ip>',methods=['GET'])
@login_required
def get_more_ecs_info(ip):
    mem = ecs_utils.getMemOfIp(ip)
    disk = ecs_utils.getDiskOfIp(ip)
    return flask.jsonify(mem=mem,disk=disk)
