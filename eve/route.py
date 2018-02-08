# -*- coding: UTF-8 -*-
"""
所有请求的路由都在这里配置
"""
from eve import app
from .views import main, user, task, project_config, \
    redirect_monitor_supervisord,ecs
from .api import users, projects, user_projects, tasks, branchs, task_audit,\
    menu, monitor_supervisord, micro_service, app_version, apk_file,aliyun_ecs

app.register_blueprint(project_config.mod, url_prefix='/project/config')
app.register_blueprint(task.mod, url_prefix='/task')
app.register_blueprint(tasks.api, url_prefix='/api')
app.register_blueprint(users.api, url_prefix='/api')
app.register_blueprint(projects.api, url_prefix='/api')
app.register_blueprint(user_projects.api, url_prefix='/api')
app.register_blueprint(branchs.api, url_prefix='/api')
app.register_blueprint(task_audit.api, url_prefix='/api')
app.register_blueprint(menu.api, url_prefix='/api')
app.register_blueprint(micro_service.api, url_prefix='/api')
app.register_blueprint(app_version.api, url_prefix='/api')
app.register_blueprint(apk_file.api, url_prefix='/api')
app.register_blueprint(main.mod)
app.register_blueprint(user.mod)
# 应用服务器进程监控
app.register_blueprint(monitor_supervisord.api, url_prefix='/api')
app.register_blueprint(redirect_monitor_supervisord.mod,
                       url_prefix='/monitorredirect')
#ecs服务器监控
app.register_blueprint(aliyun_ecs.api, url_prefix='/api')
app.register_blueprint(ecs.mod,url_prefix='/ecs')