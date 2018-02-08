#!/usr/bin/python
# coding=utf-8

import os, subprocess

# 加载依赖
subprocess.call(['virtualenv', 'eve-env'])
subprocess.call([os.path.join('eve-env', 'bin', 'pip'), 'install', '-r', 'requirements.txt'])
