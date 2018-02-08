# -*- coding: UTF-8 -*-

import requests
from flask import json
from eve import app


def sendLinkMsg(linked_url, content):
    payload = {
        "msgtype": "link",
        "link": {
            "text": "项目发布",
            "title": content,
            "picUrl": "https://eve.baokeyunguanjia.com/static/eva.jpg",
            "messageUrl": linked_url
        }
    }
    headers = {'Content-Type': 'application/json'}
    post = requests.post(
        "https://oapi.dingtalk.com/robot/send?access_token=bf360958f83703adac59d7d1b645dcddf3847aa0dbeb9975fe235ce9738231a5",
        data=json.dumps(payload),
        headers=headers
    )
    app.logger.info("post,%s" % post)
