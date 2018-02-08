# -*- coding: UTF-8 -*-

from flask import jsonify
import flask
from flask import Blueprint
from eve import app
import supervisor_utils
from flask_login import login_required
import utils

api = Blueprint('monitor_supervisord', __name__)

@api.route('/monitor')
@login_required
def show_monitor_list():
    #获取主机下拉列表
    server = supervisor_utils.get_server_list()
    #获取主机监控列表
    proInfo = supervisor_utils.get_supervisor_url(server['options3'][0]['options'][0]['value']).supervisor.getAllProcessInfo()
    return jsonify(data=list(proInfo),servers=server,initSelect=server['options3'][0]['options'][0]['value'])

@api.route('/monitor/ip/<string:server_ip>')
@login_required
def get_monitor_list(server_ip):
    server = supervisor_utils.get_server_list()
    proInfo = supervisor_utils.get_supervisor_url(server_ip).supervisor.getAllProcessInfo()
    return jsonify(data=list(proInfo),servers=server)


@api.route('/monitor/servername/<string:service_name>/operation/<string:operation_num>/ip/<string:server_ip>', methods=["GET"])
@login_required
def startOrStopService(service_name,operation_num,server_ip):
    try:
        # 启动服务
        if operation_num == "start":
            resultstart = supervisor_utils.get_supervisor_url(server_ip).supervisor.startProcess(service_name)
            return flask.jsonify(data=resultstart)
        # 停止服务
        elif operation_num == "stop":
            resultstop = supervisor_utils.get_supervisor_url(server_ip).supervisor.stopProcess(service_name)
            return flask.jsonify(data=resultstop)
        # 停止服务
        elif operation_num == "restart":
            stepstop = supervisor_utils.get_supervisor_url(server_ip).supervisor.stopProcess(service_name)
            stepstart = supervisor_utils.get_supervisor_url(server_ip).supervisor.startProcess(service_name)
            if stepstop is True and stepstart is True:
                return flask.jsonify(data=True)
            else:
                return flask.jsonify(data=False)
        else:
            result = "未知参数,非法操作!"
            return flask.jsonify(data=result)
    except Exception as e:
        app.logger.error(e)
        return flask.jsonify(data=False)

@api.route('/monitor/serverlog/servername/<string:service_name>/ip/<string:server_ip>', methods=["GET"])
@login_required
def getLogOfServiceName(service_name,server_ip):
    proInfoTotal = supervisor_utils.get_supervisor_url(server_ip).supervisor.readProcessStdoutLog(service_name, 0, 0)
    return flask.jsonify(data=proInfoTotal)
