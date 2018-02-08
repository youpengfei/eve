# coding=utf-8

import datetime
import subprocess
import time

from flask import jsonify
from flask.ext.login import current_user
from flask.ext.mail import Message

import git_utils
import utils
from eve import db, gl, mail, app
from eve.constant import DeployEnv, TASK_PROGRESS, TaskStatus
from eve.models import Task, Record


def start_deploy(task_id):
    if not task_id:
        return jsonify(code=401, message='taskId必须填写')

    task = Task.query.filter_by(id=task_id).one()

    if task.user_id != current_user.id:
        return jsonify(code=403, message="这个任务不属于你")

    # 任务失败或者审核通过时可发起上线
    if not (1, 4).__contains__(task.status):
        return jsonify(code=500, message="任务不是失败或者审核通过状态")

    # 清除历史记录
    Record.query.filter_by(task_id=task_id).delete()

    task.status = TaskStatus.PROCESSING.value
    db.session.add(task)
    db.session.commit()

    app.logger.info("task id:[%d],msg:task start" % (task_id))

    if task.action == 0:
        make_version(task)
        init_ret = init_workspace(task)

        if init_ret[0] != 0:
            app.logger.error("task id:[%d],error:%s" % (task_id, init_ret[1]))
            task.status = TaskStatus.FAILED.value
            db.session.add(task)
            db.session.commit()
            return jsonify(message="init_workspace_error", code=500)
        app.logger.info("task id:[%d],msg:%s",
                        task.id, "init_workspace finished")
        pre_deploy_ret = pre_deploy(task)
        if pre_deploy_ret[0] != 0:
            app.logger.error("task id:[%d],error:%s" %
                             (task_id, pre_deploy_ret[1]))
            task.status = TaskStatus.FAILED.value
            db.session.add(task)
            db.session.commit()
            return jsonify(message="pre_deploy_error", code=500)
        app.logger.info("task id:[%d],msg:%s", task.id, "pre_deploy finished")
        get_sourcecode_ret = get_sourcecode(task)
        if get_sourcecode_ret[0] != 0:
            app.logger.error("task id:[%d],error:%s" %
                             (task_id, get_sourcecode_ret[1]))
            task.status = TaskStatus.FAILED.value
            db.session.add(task)
            db.session.commit()
            return jsonify(message="get_sourcecode_error", code=500)
        app.logger.info("task id:[%d],msg:%s",
                        task.id, "get_sourcecode finished")
        post_deploy_ret = post_deploy(task)
        if post_deploy_ret[0] != 0:
            app.logger.error("task id:[%d],error:%s" %
                             (task_id, post_deploy_ret[1]))
            task.status = TaskStatus.FAILED.value
            db.session.add(task)
            db.session.commit()
            return jsonify(message="post_deploy_error%s" % post_deploy_ret[1], code=500)
        try:
            transmission(task)
        except Exception as e:
            app.logger.error(e)
            app.logger.error("task id:[%d],error:%s" % (task_id, e))
            task.status = TaskStatus.FAILED.value
            db.session.add(task)
            db.session.commit()
            return jsonify(message="transmission_error", code=500)
        app.logger.info("task id:[%d],msg:%s",
                        task.id, "transmission finished")
        update_remote_server_ret = update_remote_server(task)
        if update_remote_server_ret[0] != 0:
            error_msg = update_remote_server_ret[1]
            app.logger.error("task id:[%d],error:%s" % (task_id, error_msg))
            task.status = TaskStatus.FAILED.value
            db.session.add(task)
            db.session.commit()
            return jsonify(message="update_remote_server_error", code=500)
        app.logger.info("task id:[%d],msg: update_server finished", task.id)
        clean_remote_server(task)
        clean_local(task)
        app.logger.info("task id:[%d],msg:%s", task.id, "clean_local finished")
        # 更新任务状态
        task.status = TaskStatus.FINISHED.value
        task.ex_link_id = task.project.version
        project = task.project
        project.version = task.link_id
        db.session.add(project)
        db.session.add(task)
    else:
        update_remote_server(task)
        task.status = TaskStatus.FINISHED.value
        project = task.project
        project.version = task.link_id
        db.session.add(project)
        db.session.add(task)
    db.session.commit()
    msg = Message('项目发布成功', sender='eva@notice.baokeyun.com',
                  recipients=[current_user.email])
    msg.body = ''
    msg.html = '<b>%s恭喜你上线成功了!</b> ' % project.name
    mail.send(msg)
    return jsonify(message="成功", code=0)


def make_version(task):
    version = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    task.link_id = version
    db.session.add(task)
    db.session.commit()


def init_workspace(task):
    """
    初始化工作目录 本地和远程的
    :param task: 发布任务
    :return: Void
    """
    from_time = int(1000 * time.time())
    project = task.project
    project_name = git_utils.get_project_name(project.repo_url)
    build_path = get_build_path(project, project_name, task)
    command = ['mkdir -p  %s' % build_path]
    p_open = subprocess.Popen('mkdir -p  %s' % build_path,
                              stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    p_open.wait()
    return_code = p_open.returncode
    if return_code != 0:
        return return_code, ''.join(p_open.stderr.readlines())

    # 拷贝本地文件

    memo = [''.join(v.decode("utf-8") for v in p_open.stdout.readlines())]

    # 拷贝远程文件
    for host in project.hosts.split('\n'):
        version = '%s/%s/%s' % (project.release_library,
                                project_name, task.link_id)
        port = 22 if host.find(':') == -1 else int(host[host.rfind(":") + 1:])
        host = host if host.find(':') == -1 else str(host[:host.rfind(":")])
        remote_cmd = 'mkdir -p %s' % version
        result, error_msg = utils.command_with_result(hostname=host,
                                                      username=project.release_user,
                                                      port=port,
                                                      command=remote_cmd)
        memo.append('r:%s' % result)
        command.append('r: %s' % remote_cmd)

    record = Record(
        user_id=current_user.id,
        task_id=task.id,
        action=TASK_PROGRESS[0],
        command=' && '.join(command),
        memo=''.join(memo),
        step=1,
        duration=int(1000 * time.time()) - from_time)
    db.session.add(record)
    db.session.commit()
    return 0, record.memo


def pre_deploy(task):
    """
    发布前置准备 安装npm maven之类
    :param task:
    :return: Void
    """
    project = task.project
    from_time = int(1000 * time.time())
    pre_deploy_split = task.project.pre_deploy.split('\n')
    if pre_deploy_split is None:
        return

    cmd = ['. /etc/profile', 'cd %s' %
           project.get_deploy_workspace(task.link_id)]

    for pre_deploy_cmd in pre_deploy_split:
        if len(pre_deploy_cmd.strip('\r').strip('\n').strip(' ')) > 0:
            cmd.append(pre_deploy_cmd)

    command = ' && '.join(cmd)
    p_open = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p_open.wait()
    memo = ''.join(v.decode("utf-8") for v in p_open.stdout.readlines())
    return_code = p_open.returncode != 0
    if return_code:
        return p_open.returncode, ''.join(v.decode("utf-8") for v in p_open.stderr.readlines()) + memo

    record = Record(user_id=current_user.id,
                    task_id=task.id,
                    action=TASK_PROGRESS[1],
                    memo=memo,
                    duration=int(1000 * time.time()) - from_time,
                    step=2,
                    command=command)
    db.session.add(record)
    db.session.commit()
    return 0, memo


def get_sourcecode(task):
    """
    下载最新源代码
    :param task:
    :return:
    """
    from_time = int(1000 * time.time())
    project = task.project
    project_name = git_utils.get_project_name(project.repo_url)
    build_path = get_build_path(project, project_name, task)

    project_gitlab = gl.projects.get(
        git_utils.get_project_full_name(project.repo_url))
    # 从gitlab下载指定分支的源代码
    if project.level == DeployEnv.DEV.value:
        rc = project_gitlab.branches.get(task.branch)
        commit_id = rc.commit['id']
    else:
        tag = project_gitlab.tags.get(task.branch)
        commit_id = tag.commit.id

    tgz = project_gitlab.repository_archive(sha=commit_id)
    zip_file_name = '%s/source.tar.gz' % build_path
    with open(zip_file_name, 'wb') as t:
        t.write(tgz)
    commit_file_name = "%s/%s-%s-%s" % (
        build_path, git_utils.get_project_name(project.repo_url), commit_id, commit_id)
    cmd = ['tar -xf  %s -C %s' % (zip_file_name, build_path),
           'rsync -a  %s/  %s && rm -rf %s && rm -rf %s' % (
               commit_file_name, build_path, commit_file_name, zip_file_name)]
    command = ' && '.join(cmd)

    p_open = subprocess.Popen(
        command, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    p_open.wait()
    return_code = p_open.returncode
    if return_code != 0:
        return return_code, ''.join(p_open.stderr.readlines())
    else:
        record = Record(
            user_id=current_user.id,
            task_id=task.id,
            action=TASK_PROGRESS[2],
            command=command,
            memo=''.join(v.decode("utf-8") for v in p_open.stdout.readlines()),
            step=3,
            duration=int(1000 * time.time()) - from_time)
        db.session.add(record)
        db.session.commit()
        return 0, record.memo


def post_deploy(task):
    """
    打包命令
    """
    from_time = int(1000 * time.time())
    project = task.project
    tasks = project.post_deploy.split('\n')

    # 本地可能要做一些依赖环境变量的命令操作
    cmd = ['. /etc/profile']
    workspace = project.get_deploy_workspace(task.link_id)

    cmd.append("cd %s" % workspace)

    for task_command in tasks:
        if task_command:
            cmd.append(task_command.strip('\n').strip('\r'))

    command = ' && '.join(cmd)
    p_open = subprocess.Popen(
        command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p_open.wait()
    return_code = p_open.returncode
    memo = ''.join(v.decode("utf-8") for v in p_open.stdout.readlines())
    if return_code != 0:
        return return_code, ''.join(v.decode("utf-8") for v in p_open.stderr.readlines()) + memo

    record = Record(user_id=current_user.id,
                    task_id=task.id,
                    action=64,
                    duration=int(1000 * time.time()) - from_time,
                    memo=memo,
                    step=4,
                    command=command)
    db.session.add(record)
    db.session.commit()
    return 0, ''


def transmission(task):
    from_time = int(1000 * time.time())
    project = task.project
    package_file_full_name = package_file(task)
    remote_file_name = get_release_file(project, task)

    for host in project.hosts.split('\n'):
        port = 22 if host.find(':') == -1 else int(host[host.rfind(":") + 1:])
        host = host if host.find(':') == -1 else str(host[:host.rfind(":")])
        utils.trans_data(hostname=host,
                         remote_path=remote_file_name,
                         local_path=package_file_full_name,
                         port=port,
                         username=project.release_user)

    un_package_file(task)

    record = Record(user_id=current_user.id,
                    task_id=task.id,
                    action=78,
                    duration=int(1000 * time.time()) - from_time,
                    step=5,
                    command='scp %s to %s:%s' % (package_file_full_name, project.hosts, remote_file_name))
    db.session.add(record)
    db.session.commit()


def update_remote_server(task):
    project = task.project
    cmd = [get_remote_command(project.pre_release, task.link_id, project),
           get_linked_command(task),
           get_remote_command(project.post_release, task.link_id, project)]
    from_time = int(1000 * time.time())
    command = ' && '.join(cmd)
    memo = []
    for host in project.hosts.split('\n'):
        port = 22 if host.find(':') == -1 else int(host[host.rfind(":") + 1:])
        host = host if host.find(':') == -1 else str(host[:host.rfind(":")])
        result, error = utils.command_with_result(hostname=host, username=project.release_user, command=command,
                                                  port=port)
        if error:
            return 1, "%s\t%s" % (error, result)
        memo.append(result)

    record = Record(user_id=current_user.id,
                    task_id=task.id,
                    action=100,
                    memo=''.join(memo),
                    duration=int(1000 * time.time()) - from_time,
                    step=6,
                    command=command)

    db.session.add(record)
    db.session.commit()
    return 0, memo


def clean_remote_server(task):
    """

    """
    project = task.project
    from_time = int(1000 * time.time())
    cmd = ['cd %s/%s' % (project.release_library, git_utils.get_project_name(project.repo_url)),
           'rm -f %s/%s/*.tar.gz' % (
               project.release_library, git_utils.get_project_name(project.repo_url)),
           'ls -lt| awk "FNR > %d  {print $1;}" | xargs rm -rf ' % (
               project.keep_version_num + 1)
           ]
    command = ' && '.join(cmd)
    for host in project.hosts.split('\n'):
        port = 22 if host.find(':') == -1 else int(host[host.rfind(":") + 1:])
        host = host if host.find(':') == -1 else str(host[:host.rfind(":")])
        result, error = utils.command_with_result(hostname=host, username=project.release_user, command=command,
                                                  port=port)
        if error:
            return 1, "%s\t%s" % (error, result)

    record = Record(user_id=current_user.id,
                    task_id=task.id,
                    action=100,
                    memo=''.join(command),
                    duration=int(1000 * time.time()) - from_time,
                    step=7,
                    command=command)
    db.session.add(record)
    db.session.commit()
    app.logger.info("task id:[%d],msg:clean_server finished", task.id)


def clean_local(task):
    project = task.project
    from_time = int(1000 * time.time())
    cmd = 'rm -rf %s*' % project.get_deploy_workspace(task.link_id)
    subprocess.Popen(cmd, shell=True).wait()
    record = Record(user_id=current_user.id,
                    task_id=task.id,
                    action=100,
                    memo=''.join(cmd),
                    duration=int(1000 * time.time()) - from_time,
                    step=7,
                    command=cmd)

    db.session.add(record)
    db.session.commit()
    return


def get_release_file(project, task):
    return '%s/%s/%s.tar.gz' % (project.release_library, git_utils.get_project_name(project.repo_url), task.link_id)


def get_excludes(excludes):
    """
    获取到忽略文件
    """
    excludes_cmd = ''

    # 无论是否填写排除.git和.svn, 这两个目录都不会发布
    excludes.append('.git')
    excludes.append('.svn')

    for exclude in excludes:
        excludes_cmd += "--exclude=%s " % exclude.strip(' \r\n')

    return excludes_cmd


def package_file(task):
    """
    压缩文件
    """
    project = task.project
    version = task.link_id
    files = task.get_deploy_files()
    excludes = project.excludes.split('\r\n')
    package_path = '%s.tar.gz' % project.get_deploy_workspace(version)
    package_command = 'cd %s/ && tar -p %s -cz -f %s %s' % \
                      (project.get_deploy_workspace(version),
                       get_excludes(excludes), package_path, files)

    popen = subprocess.Popen(package_command, shell=True,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    popen.wait()
    app.logger.info(popen.stderr.readlines())
    if popen.returncode != 0:
        return popen.returncode, ''.join(v.decode("utf-8") for v in popen.stderr.readlines())
    return package_path


def un_package_file(task):
    """
    解压文件
    """
    project = task.project
    version = task.link_id
    release_file = get_release_file(project, task)
    web_root_path = project.release_to
    release_path = '%s/%s/%s' % (project.release_library,
                                 git_utils.get_project_name(project.repo_url), version)
    cmd = []
    if task.file_transmission_mode == 2:
        cmd.append('cp -a %s/. %s' % web_root_path % release_path)

    cmd.append(
        'cd %s$s && tar --no-same-owner -pm -C %s$s -xz -f %s$s' % (release_path, release_path, release_file))
    command = ' && '.join(cmd)
    for host in project.hosts.split('\n'):
        port = 22 if host.find(':') == -1 else int(host[host.rfind(":") + 1:])
        host = host if host.find(':') == -1 else str(host[:host.rfind(":")])
        resutl, error_msg = utils.command_with_result(hostname=host, username=project.release_user, command=command,
                                                      port=port)
        # 如果远端出现异常直接退出
        if error_msg:
            app.logger.error(error_msg)
            return 1, error_msg


def get_remote_command(task, version, project):
    task_split = task.split('\n')
    cmd = ['. /etc/profile']
    version1 = '%s/%s/%s' % (project.release_library,
                             git_utils.get_project_name(project.repo_url), version)

    cmd.append('cd %s' % version1)

    for task in task_split:
        if task:
            cmd.append(task.strip('\r\n'))

    return ' && '.join(cmd)


def get_linked_command(task):
    project = task.project
    release_user = project.release_user
    project_name = git_utils.get_project_name(project.repo_url)
    current_tmp = '%s/%s/current-%s.tmp' % (
        project.release_library, project_name, project_name)
    linked_from = '%s/%s/%s' % (project.release_library,
                                project_name, task.link_id)
    cmd = ['ln -sfn %s %s' % (linked_from, current_tmp),
           'chown -h %s %s' % (release_user, current_tmp),
           'mv -fT %s %s' % (current_tmp, project.release_to)]
    return ' && '.join(cmd)


def get_build_path(project, project_name, task):
    return "%s/%s-%s-%s" % (project.deploy_from, project_name, project.level, task.link_id)
