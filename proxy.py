# coding:utf-8
import requests
from lxml import etree


header = {
    'Referer': 'http://www.xicidaili.com/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
}


def get_proxy():
    req = requests.get('http://www.xicidaili.com/nn', headers=header)
    ip_list = []
    if req.status_code == 200:
        content = etree.HTML(req.text)
        tr = content.xpath('//tr[@class]')
        for item in tr:
            content = item.xpath('td/text()')
            host = content[0]
            port = content[1]
            ip = str(host + ':' + port)
            ip_list.append({"http": ip})
        return ip_list
    else:
        print('Response Error!')
        return None
