# -*- coding: UTF-8 -*-

import flask
from flask import Blueprint, request
from flask_login import login_required
from gitlab import GitlabGetError

import git_utils
from eve import gl, app
from eve.constant import DeployEnv
from eve.models import Project, project_schemas

api = Blueprint('branch-api', __name__)


@api.route("/branchs")
@login_required
def project_list():
    level = int(request.args.get("level", 0))
    project_id = int(request.args.get("project_id", 0))
    project = Project.query.filter_by(id=project_id).one()
    project_full_name = git_utils.get_project_full_name(project.repo_url)

    if level == DeployEnv.PROD.value or level == DeployEnv.PRERELEASE.value:
        try:
            tags_list = gl.projects.get(project_full_name).tags.list()
            # 获取一个根据日期排序的tag，然后取出前五条作为上线依据
            branch_list = list(
                map(lambda x: {"name": x.name},
                    sorted(tags_list, key=lambda x: x.commit.committed_date, reverse=True)[:5]))
        except GitlabGetError as e:
            app.logger.error(e)
            return flask.jsonify(data=e.error_message, code=500)
    elif level == DeployEnv.DEV.value:
        branch_list = list(map(lambda x: {"name": x.name},
                               filter(lambda x: x.name.startswith('hotfix/'),
                                      gl.projects.get(project_full_name).branches.list())))
        branch_list.append({"name": "canary"})
        branch_list.append({'name': "rc"})

    return flask.jsonify(data=branch_list, code=200)
