# -*- coding: UTF-8 -*-

from aliyunsdkcore import client
from aliyunsdkecs.request.v20140526.DescribeInstancesRequest import DescribeInstancesRequest
import json
from eve import app
import utils


clt = client.AcsClient("LTAILP3AFVtD2wms","J1n8VBvC6m45CPKeZ4XQIw4Dko1E3A","cn-beijing")

def ecs_list():
    request = DescribeInstancesRequest()
    response = _send_request(request)
    if response is not None:
        instance_list = response.get('Instances').get('Instance')
        return instance_list

def _send_request(request):
    request.set_accept_format('json')
    try:
        response_str = clt.do_action_with_exception(request)
        response_detail = json.loads(response_str)
        return response_detail
    except Exception as e:
        app.logger.error(e)

def getMemOfIp(ip):
    if ip != "101.200.196.229":
        result, error_msg = utils.command_with_result(hostname=ip, username="admin", port=22,command="free -m")
        if error_msg:
            app.logger.error(error_msg)
        return result
    else:
        result, error_msg = utils.command_with_result(hostname="101.200.196.229", username="root", port=49720, command="free -m")
        if error_msg:
            app.logger.error(error_msg)
        return result

def getDiskOfIp(ip):
    if ip != "101.200.196.229":
        result, error_msg = utils.command_with_result(hostname=ip, username="admin", port=22,command="df -h")
        if error_msg:
            app.logger.error(error_msg)
        return result
    else:
        result, error_msg = utils.command_with_result(hostname='101.200.196.229', username="root", port=49720,command="df -h")
        if error_msg:
            app.logger.error(error_msg)
        return result







