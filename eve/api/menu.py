# -*- coding: UTF-8 -*-

import flask
from flask import Blueprint
from flask_login import current_user, login_required

from eve.models import Menu
from eve.schema import menu_schemas

api = Blueprint('menu-api', __name__)


@api.route("/menu/current-user")
@login_required
def current_user_menus():
    if current_user.role == 2:
        role__all = Menu.query.all()
    else:
        role__all = Menu.query.filter_by(role=current_user.role).all()
    return flask.jsonify(data=menu_schemas.dump(role__all).data, code=200)
