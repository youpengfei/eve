# -*- coding: UTF-8 -*-

import os

basedir = os.path.abspath(os.path.dirname(__file__))

CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{}:{}@{}:{}/{}'.format(
    'summer', 'summer', '127.0.0.1', 3306, 'summer')

# 'mysql://summer:summer@127.0.0.1/summer'

#SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://{}:{}@{}:{}/{}'.format('stewardtest', 'stewardtest@1118', '192.168.1.152', 3306, 'summer')

SQLALCHEMY_ECHO = True
PASSWORD_SALT = "you-will-never-guess"

MAIL_SERVER = 'smtpdm.aliyun.com'
MAIL_PORT = '465'  # 电子邮件服务器的端口
MAIL_USE_SSL = True  # 启用传输层安全
MAIL_USE_TSL = True  # 启用传输层安全
MAIL_USERNAME = 'eva@notice.baokeyun.com'  # 邮件账户用户名
MAIL_PASSWORD = ''  # 邮件账户的密码

ALLOW_CROSS_DOMAIN = "*"

DEFAULT_USER = 'admin'
RSA_FILE = '/Users/youpengfei/.ssh/id_rsa'



OSS_BASE_URL = ''
OSS_BUCKET_NAME = ''
OSS_ACCESS_KEY = ''
OSS_ACCESS_KEY_SECRET = ''
