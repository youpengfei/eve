#!/usr/bin/python

# -*- coding: UTF-8 -*-


import paramiko

from eve import app

DEFAULT_USERNAME = app.config['DEFAULT_USER']
DEFAULT_KEY_FILE = app.config['RSA_FILE']


def trans_data(hostname,
               key_file=DEFAULT_KEY_FILE,
               remote_path=None,
               local_path=None,
               port=22,
               username=DEFAULT_USERNAME ):

    with paramiko.Transport(hostname, port) as t:
        key = paramiko.RSAKey.from_private_key_file(key_file)
        t.connect(username=username, pkey=key)
        sftp = paramiko.SFTPClient.from_transport(t)
        sftp.put(localpath=local_path, remotepath=remote_path)







def command_with_result(hostname, command, key_file=DEFAULT_KEY_FILE, username=DEFAULT_USERNAME, port=22):
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname, port, username, key_filename=key_file)
        stdin, stdout, stderr = ssh.exec_command(command)
        return ''.join(stdout.readlines()), ''.join(stderr.readlines())


def escape_shell_arg(arg):
    return "\\'".join("'" + p + "'" for p in arg.split("'"))
