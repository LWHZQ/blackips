# 开源项目https://github.com/jhao104/proxy_pool

import requests
import random
from common.constant import USER_AGENTS


class ProxiesSpider(object):
    """
    func:
        https://github.com/jhao104/proxy_pool   ProxyPool 爬虫代理IP池
    """
    def __init__(self):
        self.proxy = None

    def get_proxy(self):
        flag = False
        while not flag:    # 找到一个可用的代理
            proxy = requests.get("http://192.168.11.135:5010/get/").json().get("proxy")
            flag = self.verification(proxy)

        print("valid proxy:%s" % proxy)
        return proxy

    def get_https_proxy(self):
        proxy = requests.get("http://192.168.11.135:5010/get/?type=https").json().get("proxy")
        print("valid proxy:%s" % proxy)
        return proxy

    def delete_proxy(self):
        requests.get("http://192.168.11.135:5010/delete/?proxy={}".format(self.proxy))

    def verification(self, proxy_ip_port):
        """
        func：
            验证代理是否可用
        params：
            proxy: 代理，结构为ip:port
        """
        ip, port = proxy_ip_port.split(":")
        proxy = {
            'http': 'http://{}'.format(proxy_ip_port),
            'https': 'https://{}'.format(proxy_ip_port)
        }
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Connection': 'keep-alive'
        }
        print(proxy)

        p = requests.get('http://icanhazip.com', headers=headers, proxies=proxy, timeout=500)
        if p.status_code == 200:   # 返回200都不一定代表可用，还得判断输出内容是否等于使用的代理IP
            if ip == str(p.text.strip()):
                return True
        return False


if __name__ == "__main__":
    obj = ProxiesSpider()
    proxy = obj.get_https_proxy()