
# encoding=utf-8

"""
关于阿里云oss的一些操作
"""

import oss2
import flask
from eve import app
auth = oss2.Auth(app.config['OSS_ACCESS_KEY'],
                 app.config['OSS_ACCESS_KEY_SECRET'])
bucket = oss2.Bucket(auth, 'oss-cn-beijing.aliyuncs.com',
                     app.config['OSS_BUCKET_NAME'])
BASE_URL = app.config['OSS_BASE_URL'] + 'app/'


def upload_apk_to_oss(file):
    bucket.put_object('app/' + file.filename, file)
    ret = bucket.get_object_meta('app/' + file.filename)
    return BASE_URL + file.filename, ret.content_length


def delete_apk_of_oss(file_name):
    bucket.delete_object('app/' + file_name)
    return BASE_URL + file_name
