# -*- coding: UTF-8 -*-

import os

import flask
from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_required


from eve import app

mod = Blueprint('main', __name__)


@mod.route('/')
@login_required
def index():
    '''
    首页自动跳转
    '''
    return redirect(url_for('task.online_orders'))


@mod.route('/micro-services-list/')
@login_required
def microservice_list():
    '''
    微服务页面
    '''
    return render_template('microservice_list.html')


@mod.route('/app-version-list/')
@login_required
def app_version_list():
    '''
    微服务页面
    '''
    return render_template('app_version_list.html')
