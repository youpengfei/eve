# -*- coding: UTF-8 -*-

import gitlab
from flask import Flask
from flask.ext.cors import CORS
from flask.ext.login import LoginManager
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

import log

__author__ = 'youpengfei'

app = Flask(__name__)
app.config.from_object('config')

ma = Marshmallow(app)

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app)

mail = Mail(app)

log.init_log('/var/log/project/eve/')  # 初始化logging.logger

CORS(app)

try:
    gl = gitlab.Gitlab.from_config('baokeyun', ['./gitlab.cfg'])
    gl.auth()

except Exception as e:
    app.logger.error(e)
