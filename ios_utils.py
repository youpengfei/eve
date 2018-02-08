# encoding=utf-8

"""
关于ios的一些操作
"""

import requests
from bs4 import BeautifulSoup


def get_version():
    """
    获取到当前itunes上面版本号（通过抓取html解析获取）
    """
    itunes_html = requests.get(
        'https://itunes.apple.com/cn/app/id1018838753').text
    select_item = BeautifulSoup(itunes_html, "html.parser").find_all(
        attrs={'itemprop': 'softwareVersion'})
    if len(select_item) > 0:
        return select_item[0].get_text()
    else:
        return ''
