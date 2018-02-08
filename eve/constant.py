# -*- coding: UTF-8 -*-

from enum import Enum, unique


@unique
class DeployEnv(Enum):
    """
     定义发布环境 分别是： 测试环境 预发布环境 线上环境
    """
    DEV = 1
    PRERELEASE = 2
    PROD = 3


@unique
class TaskStatus(Enum):
    """
     '状态0：新建提交，1审核通过，2审核拒绝，3上线完成，4上线失败,5正在上线',
    """
    NEW = 0
    APPROVED = 1
    REJECTED = 2
    FINISHED = 3
    FAILED = 4
    PROCESSING = 5


TASK_PROGRESS = (24, 40, 53, 64, 78, 100)
