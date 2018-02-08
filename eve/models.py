# -*- coding: UTF-8 -*-

import bcrypt
from flask.ext.login import UserMixin
from marshmallow import fields
from marshmallow_sqlalchemy import field_for
from sqlalchemy import ForeignKey
from sqlalchemy import func
from sqlalchemy.orm import relationship

import git_utils
from . import db, ma, app

__author__ = 'youpengfei'


class Project(db.Model):
    __tablename__ = 'project'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    user_id = db.Column(db.Integer)
    level = db.Column(db.Integer)
    status = db.Column(db.Integer)
    version = db.Column(db.String(32))
    repo_url = db.Column(db.String(200))
    repo_username = db.Column(db.String(50))
    repo_password = db.Column(db.String(100))
    repo_mode = db.Column(db.String(50))
    repo_type = db.Column(db.String(10))
    deploy_from = db.Column(db.String(200))
    excludes = db.Column(db.Text)
    release_user = db.Column(db.String(50))
    release_to = db.Column(db.String(200))
    release_library = db.Column(db.String(200))
    hosts = db.Column(db.Text)
    pre_deploy = db.Column(db.Text)
    post_deploy = db.Column(db.Text)
    pre_release = db.Column(db.Text)
    post_release = db.Column(db.Text)
    post_release_delay = db.Column(db.Integer)
    audit = db.Column(db.Integer)
    ansible = db.Column(db.Integer, default=0)
    keep_version_num = db.Column(db.Integer)
    created_at = db.Column(db.Date)
    updated_at = db.Column(db.Date)
    tasks = relationship("Task", back_populates="project")

    def get_deploy_workspace(self, version=''):
        deploy_from = self.deploy_from
        level = self.level
        project_name = git_utils.get_project_name(self.repo_url)
        return "%s/%s-%s-%s" % (deploy_from, project_name, level, version)

    def __repr__(self, *args, **kwargs):
        return super().__repr__(*args, **kwargs)


projects = db.Table('group',
                    db.Column('user_id',
                              db.Integer,
                              db.ForeignKey('user.id')),
                    db.Column('project_id',
                              db.Integer,
                              db.ForeignKey('project.id')))


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    is_email_verified = db.Column(db.Integer)
    auth_key = db.Column(db.String(32))
    password_hash = db.Column(db.String(255))
    email_confirmation_token = db.Column(db.String(255))
    email = db.Column(db.String(255))
    avatar = db.Column(db.String(100), default='default.jpg')
    role = db.Column(db.Integer, default=1)
    status = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now())
    realname = db.Column(db.String(32))
    tasks = relationship("Task", back_populates="user")
    projects = db.relationship('Project', secondary=projects,
                               backref=db.backref('users', lazy='dynamic'))

    def verify_password(self, password):
        _password = password.encode('utf-8')
        _password_hash = self.password_hash.encode('utf-8')
        return bcrypt.hashpw(_password, _password_hash) == _password_hash


class Group(db.Model):
    __tablename__ = 'group'
    __table_args__ = {"useexisting": True}
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    type = db.Column(db.Integer)


class Task(db.Model):
    __tablename__ = 'task'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('user.id'))
    project_id = db.Column(db.Integer, ForeignKey('project.id'))
    action = db.Column(db.Integer, default=0)
    status = db.Column(db.SmallInteger)
    title = db.Column(db.String(100))
    link_id = db.Column(db.String(20))
    ex_link_id = db.Column(db.String(20))
    commit_id = db.Column(db.String(100))
    branch = db.Column(db.String(100))
    file_transmission_mode = db.Column(db.SmallInteger)
    file_list = db.Column(db.Text)
    enable_rollback = db.Column(db.SmallInteger, default=1)
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now())
    user = relationship("User", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
    taskAudits = relationship("TaskAudit", back_populates="task")

    def get_deploy_files(self):
        if self.file_transmission_mode == 1:
            return '.'
        elif self.file_transmission_mode == 2 and self.file_list:
            return ' '.join(self.file_list.split('\n')).strip(" ")
        else:
            return None


class TaskAudit(db.Model):
    """
    任务审核功能
    """
    __tablename__ = 'task_audit'
    id = db.Column(db.Integer, primary_key=True)
    request_user_id = db.Column(db.Integer, ForeignKey('user.id'), doc="发起人")
    assign_user_id = db.Column(db.Integer, ForeignKey('user.id'), doc="审核人")
    project_id = db.Column(db.Integer, ForeignKey('project.id'))
    task_id = db.Column(db.Integer, ForeignKey('task.id'))
    deploy_reason = db.Column(db.String(100))
    reject_reason = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=func.now())
    flag = db.Column(db.String(1), default='0')
    task = relationship("Task")


class Record(db.Model):
    __tablename__ = 'record'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    task_id = db.Column(db.Integer)
    status = db.Column(db.SmallInteger, default=1)
    action = db.Column(db.SmallInteger)
    command = db.Column(db.Text)
    duration = db.Column(db.Integer)
    memo = db.Column(db.Text)
    step = db.Column(db.Integer)
    created_at = db.Column(db.Integer)


class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    code = db.Column(db.String(20))
    created_at = db.Column(db.Integer)


class Menu(db.Model):
    __tablename__ = 'menu'
    id = db.Column(db.Integer, primary_key=True)
    index = db.Column(db.String(10))
    title = db.Column(db.String(50))
    route = db.Column(db.String(100))
    role = db.Column(db.Integer)
    icon = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=func.now())
    updated_at = db.Column(db.DateTime, default=func.now())


class AppVersion(db.Model):
    __tablename__ = 'app_version'
    id = db.Column(db.Integer, primary_key=True)
    app_name = db.Column(db.String(45))
    app_version = db.Column(db.String(45))
    update_desc = db.Column(db.String(200))
    download_url = db.Column(db.String(200))
    file_size = db.Column(db.String(11))
    client_type = db.Column(db.String(10))
    update_mode = db.Column(db.String(1))
    update_notice = db.Column(db.String(100))
    created_by = db.Column(db.String(45))
    created_date = db.Column(db.DateTime, default=func.now())
    last_modified_date = db.Column(db.DateTime, default=func.now())
    last_modified_by = db.Column(db.String(45))
    state = db.Column(db.String(1))
    flag = db.Column(db.String(1))


class UserInfoSchema(ma.ModelSchema):
    class Meta:
        model = User
        fields = ('id', 'email')
        dateformat = '%Y-%m-%d %H:%M:%S'


class TaskSchema(ma.ModelSchema):
    class Meta:
        model = Task


class ProjectSchema(ma.ModelSchema):
    users = ma.Nested(UserInfoSchema, many=True)

    class Meta:
        model = Project
        dateformat = '%Y-%m-%d %H:%M:%S'


class ProjectInfoSchema(ma.ModelSchema):
    class Meta:
        model = Project
        fields = ('name', 'id', 'level')


class UserSchema(ma.ModelSchema):
    projects = ma.Nested(ProjectInfoSchema, many=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'projects', 'status', 'realname', 'role')


class TaskAuditInfoSchema(ma.ModelSchema):
    class Meta:
        model = TaskAudit
        dateformat = '%Y-%m-%d %H:%M:%S'


class TaskSchema(ma.ModelSchema):
    user = ma.Nested(UserSchema)
    project = ma.Nested(ProjectInfoSchema)
    taskAudits = ma.Nested(TaskAuditInfoSchema, many=True)

    class Meta:
        model = Task
        dateformat = '%Y-%m-%d %H:%M:%S'


class TaskAuditSchema(ma.ModelSchema):
    user = ma.Nested(UserSchema)
    project = ma.Nested(ProjectInfoSchema)
    task = ma.Nested(TaskSchema)

    class Meta:
        model = TaskAudit
        dateformat = '%Y-%m-%d %H:%M:%S'


class RecordSchema(ma.ModelSchema):
    class Meta:
        model = Record
        dateformat = '%Y-%m-%d %H:%M:%S'


task_schema = TaskSchema()
task_schemas = TaskSchema(many=True)

task_audit_schema = TaskAuditSchema()
task_audit_schemas = TaskAuditSchema(many=True)

user_schema = UserSchema()
user_schemas = UserSchema(many=True)

project_schema = ProjectSchema()
project_schemas = ProjectSchema(many=True, only=('id', 'name'))
project_list_schemas = ProjectSchema(many=True)

record_schema = RecordSchema()
record_schemas = RecordSchema(many=True)
