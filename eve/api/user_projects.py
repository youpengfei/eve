# -*- coding: UTF-8 -*-

import flask
from flask import Blueprint, request
from flask_login import login_required, current_user

from eve import db, app
from eve.models import Project, User, user_schema

api = Blueprint('user-project-api', __name__)


@api.route("/user/<int:user_id>/projects", methods=['POST'])
@login_required
def update_relation_projects(user_id):
    if current_user.role != 2:
        return flask.jsonify(data="只有管理员拥有这项技能", code="403")

    json = request.json
    user = User.query.filter_by(id=user_id).one()
    if len(json) > 0:
        count = Project.query.filter(Project.name.in_(json)).count()
        if count > 0:
            project = Project.query.filter(Project.name.in_(json)).all()
            user.projects = project
            db.session.add(user)
            db.session.commit()

    else:
        user.projects = []

    db.session.add(user)
    db.session.commit()

    return flask.jsonify(data=user_schema.dump(user).data)
