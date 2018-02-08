# -*- coding: UTF-8 -*-

import xmlrpc.client

def get_supervisor_url(serverip):
    # proxy = xmlrpc.client.ServerProxy("http://baoke:SuperBaokeRpc2017@"+serverip+":9001/RPC2")
    proxy = xmlrpc.client.ServerProxy("http://baoke:SuperBaokeRpc2017@" + serverip + ":9001/RPC2")
    return proxy

def get_server_list():
    # git_dict = [{'value': "192.168.1.124", 'label': "192.168.1.124"}]
    # test_dict = [{'value': "192.168.1.126", 'label': "192.168.1.126"}]
    # sc_dict = [{'value': "192.168.2.186", 'label': "192.168.2.186"}]
    # pro_dict = [{'value': "192.168.2.187", 'label': "192.168.2.187"}]
    # pro_ms_dict = [{'value': "192.168.2.191", 'label': "192.168.2.191"}]
    # ms_dict = [{'value': "192.168.1.131", 'label': "192.168.1.131"}]
    # gitserver = {'label': "git服务器", 'options': git_dict}
    # testserver = {'label': "测试服务器", 'options': test_dict}
    # scserver = {'label': "sc服务器", 'options': sc_dict}
    # proserver = {'label': "生产服务器", 'options': pro_dict}
    # promsserver = {'label': "生产ms服务器", 'options': pro_ms_dict}
    # msserver = {'label': "ms服务器", 'options': ms_dict}
    # servers = {'options3': [gitserver, testserver,scserver,proserver,promsserver,msserver]}
    local1_dict = [{'value': "192.168.1.152", 'label': "192.168.1.152"}]
    local1server = {'label': "测试服务器1", 'options': local1_dict}
    # local_dict = [{'value': "192.168.117.128", 'label': "192.168.117.128"}]
    # localserver = {'label': "本地测试服务器", 'options': local_dict}
    servers = {'options3': [local1server]}
    return servers
