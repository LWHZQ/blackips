# -*- coding: utf-8 -*-
#!/usr/bin/python3
import random
import time
import argparse
import traceback
import requests
from urllib.request import urlretrieve
requests.packages.urllib3.disable_warnings()
from lxml import etree
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from common.constant import USER_AGENTS, country
from common.mongodb import mongo_collection
from common.util import cbk, unzip
from common.linux_venuserye import get_ipinfo_from_enuseye
"""
使用方式：
    python3 black_ip.py -A # 一次性获取所有的blackip
    python3 black_ip.py -U # 添加最近10天的的blackip
若要添加定时任务，使用crontab -e：
    0 1 * * * python3 /home/blackip/black_ip.py -U
"""


def get_ip_details(ip):
    """从www.vedbex.com获取IP详细信息,包括
    主机名、ISP网络服务提供商（organization）、domain、isp type（类）、ASN（归属地）、国家、city、经纬度、zip code（美国邮编）

    但因为页面是通过js动态渲染的，使用该方法部分数据不全，慎用
    There is issue with token. please send email to contact@admin.com and let them know.
    """
    url = "https://www.vedbex.com/geoip/%s" % ip
    headers = {
        'referfer': 'https://www.vedbex.com/geoip',
        'user-agent': random.choice(USER_AGENTS)
    }

    response = requests.get(url=url, headers=headers, verify=False, timeout=180)
    response.encoding = 'UTF-8'
    html = etree.HTML(response.text)

    ISP, Domain, ISP_Type, ASN, CIDR = None, None, None, None, None
    Country, Region, City, Zip_Code = None, None, None, None
    Latitude, Longitude = None, None
    tr_list = html.xpath("//table[@class='table table-bordered']//tr")

    for item in tr_list[1:]:
        data_type = item.xpath("./td[1]/b/text()")[0]
        data = item.xpath("./td[2]/text()")[0]
        print("data_type:%s, data:%s" % (data_type, data))

        if data_type == "ISP":
            ISP = data
        if data_type == "ISP Domain":
            Domain = data
        if data_type == "ISP Type":
            ISP_Type = data
        if data_type == "ASN":
            ASN = data
        if data_type == "CIDR":
            CIDR = data
        if data_type == "Country":
            Country = data
        if data_type == "Region":
            Region = data
        if data_type == "City":
            City = data
        if data_type == "Zip Code":
            Zip_Code = data
        if data_type == "Latitude":
            Latitude = data
        if data_type == "Longitude":
            Longitude = data

    print(ISP, Domain, ISP_Type, ASN, CIDR, Country, Region, City, Zip_Code, Latitude, Longitude)
    return ISP, Domain, ISP_Type, ASN, CIDR, Country, Region, City, Zip_Code, Latitude, Longitude


def suspondWindowHandler(browser):
    """广告页面弹窗处理"""
    try:
        suspondWindow = browser.find_element(by=By.XPATH, value="//button[@class='close']")
        suspondWindow.click()
        print("advertisement is close")
    except Exception as e:
        print("there is no advertisement or can not find element")


def save_national_flag(browser, img_url):
    print("img_url:%s" % img_url)
    if img_url:
        imag_path_dir = Path.cwd().joinpath(*["national_flag"])
        imag_path_dir.mkdir(parents=True, exist_ok=True)
        image_name = imag_path_dir.joinpath(*[Path(img_url).name])
        if not image_name.exists():
            # item.find_element(by=By.XPATH, value="./td[2]/img").screenshot(str(image_name))  # 图片会失真
            try:
                browser.get(img_url)
                browser.find_element(by=By.XPATH, value="//img").screenshot(str(image_name))
                print("save national flag ok")
            except Exception as e:
                print("save national flag fail, %s" % e)


def get_ip_details_selenium(ip):
    """从www.vedbex.com获取IP详细信息,包括
    主机名、ISP网络服务提供商（organization）、domain、isp type（类）、ASN（归属地）、国家、city、经纬度、zip code（美国邮编）
    """
    chrome_options = webdriver.ChromeOptions()  # 或者 chrome_options = Options()
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])  # 防止反爬
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # 避免webdriver检测
    chrome_options.add_argument("--remote-debugging-port=9222")  # 解决报错 WebDriverException: Message: unknown error: DevToolsActivePort file doesn't exist
    chrome_options.add_argument('--no-sandbox')  # 直接把sandbox禁用了，–-no-sandbox参数是让Chrome在root权限下跑
    chrome_options.add_argument('--disable-dev-shm-usage')  # 大量渲染时候写入/tmp而非/dev/shm
    chrome_options.add_argument('--headless')  # 无头模式，传递此参数浏览器不会显示界面，程序在后台运行
    chrome_options.add_argument('--disable-gpu')  # 禁用GPU加速
    chrome_options.add_argument("user-agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36'")
    # chrome_options.add_argument('--proxy-server=http://127.0.0.1:10809')  # 利用v2ray配置代理

    driver = webdriver.Chrome(options=chrome_options, service=Service('/usr/local/bin/chromedriver'))
    # driver.set_page_load_timeout(300)
    driver.maximize_window()  # 仅仅适配到当前显示屏大小，数据偶尔还是不完整，需要下滑鼠标

    ISP, Domain, ISP_Type, ASN, CIDR = None, None, None, None, None
    Country, Region, City, Zip_Code = None, None, None, None
    Latitude, Longitude = None, None

    url = "https://www.vedbex.com/geoip/%s" % ip

    try:
        driver.get(url)
        wait_obj = WebDriverWait(driver, 600)  # 创建显示等待对象, 设置等待条件

        driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')  # 下滑鼠标，不可少，不然无法关闭广告弹窗
        wait_obj.until(expected_conditions.visibility_of_element_located(  # 判断Ip数据是否出现
            (By.XPATH, "//table[@class='table table-bordered']//tr[13]/td[2]")))
    except Exception as e:
        print("ip data not found, %s" % e)
    else:
        time.sleep(1)
        # 可能会有弹框
        suspondWindowHandler(driver)
        time.sleep(1)

        img_url = None
        tr_list = driver.find_elements(by=By.XPATH, value="//table[@class='table table-bordered']//tr")
        for item in tr_list[1:]:
            data_type = item.find_element(by=By.XPATH, value="./td[1]/b").text
            data = item.find_element(by=By.XPATH, value="./td[2]").text
            print("data_type:%s, data:%s" % (data_type, data))

            if data_type == "ISP":
                ISP = data
            if data_type == "ISP Domain":
                Domain = data
            if data_type == "ISP Type":
                ISP_Type = data
            if data_type == "ASN":
                ASN = data
            if data_type == "CIDR":
                CIDR = data
            if data_type == "Country":
                Country = data
                if Country != "- (-)":
                    img_url = item.find_element(by=By.XPATH, value="./td[2]/img").get_attribute('src')
            if data_type == "Region":
                Region = data
            if data_type == "City":
                City = data
            if data_type == "Zip Code":
                Zip_Code = data
            if data_type == "Latitude":
                Latitude = data
            if data_type == "Longitude":
                Longitude = data

        save_national_flag(driver, img_url)
    finally:
        driver.quit()

    print(ISP, Domain, ISP_Type, ASN, CIDR, Country, Region, City, Zip_Code, Latitude, Longitude)
    return ISP, Domain, ISP_Type, ASN, CIDR, Country, Region, City, Zip_Code, Latitude, Longitude


def insert(temp_list):
    ip = temp_list[0]
    print({"_id": ip})
    check = mongo_collection.find_one({"_id": ip})
    print("check:%s" % check)
    if check is None:
        ISP, Domain, ISP_Type, ASN, CIDR, Country, Region, City, Zip_Code, Latitude, Longitude = get_ip_details_selenium(ip)
        if ISP:
            extra_info_dict = get_ipinfo_from_enuseye(ip)
            data = {
                "_id": ip,
                "date": temp_list[2][:-1],
                "host": temp_list[3][:-1],
                "ISP": ISP,
                "Domain": Domain,
                "ISP_Type": ISP_Type,
                "ASN": ASN,
                "CIDR": CIDR,
                "Country": Country,
                # "countryID": country[temp_list[4][:-1]],
                "Region": Region,
                "City": City,
                "Zip_Code": Zip_Code,
                "Latitude": Latitude,
                "Longitude": Longitude,

                "tags": extra_info_dict["tags"],
                "open_port": extra_info_dict["open_port"],
                "categories": extra_info_dict["categories"],
                "families": extra_info_dict["families"],
                "organizations": extra_info_dict["organizations"]
            }
            print("insert data:%s" % data)
            mongo_collection.update_one(filter={"_id": ip}, update={'$set': data}, upsert=True)
            print("insert ok")

            time.sleep(5)  # 等待防止反爬


def get_all_ip(filename="full_blacklist_database.txt"):
    print("in get_all_ip")
    with open(filename, "r") as fd:
        for l in fd:
            try:
                if not (l.startswith("#") or len(l.strip()) == 0):
                    print("line:%s" % l)
                    temp_list = l.split()
                    insert(temp_list)

            except Exception as e:
                print("error:%s" % e)


def _setup_argparser():
    PROGRAM_NAME = "Black IP"
    PROGRAM_VERSION = "1.0"

    parser = argparse.ArgumentParser(description='{} - {}'.format(PROGRAM_NAME, PROGRAM_VERSION))
    parser.add_argument('-V', '--version', action='version', version='{} {}'.format(PROGRAM_NAME, PROGRAM_VERSION))
    parser.add_argument('-A', '--all', action='store_true', default=False, help='get all black ip')
    parser.add_argument('-U', '--update', action='store_true', default=False, help='update black ip')
    parser.add_argument('-C', '--clear', action='store_true', default=False, help='clear black ip')

    return parser.parse_args()


if __name__ == '__main__':
    args = _setup_argparser()
    if args.all:
        print("get all black ips")
        # 所有的Blacklist IP
        full_blacklist_url = "https://myip.ms/files/blacklist/general/full_blacklist_database.zip"
        urlretrieve(full_blacklist_url, "full_blacklist_database.zip", cbk)

        unzip("full_blacklist_database.zip")
        get_all_ip("full_blacklist_database.txt")

        # 最新的10天的Blacklist IP
        latest_blacklist_url = "https://myip.ms/files/blacklist/general/latest_blacklist.txt"
        urlretrieve(latest_blacklist_url, "latest_blacklist.txt", cbk)
        get_all_ip("latest_blacklist.txt")
    elif args.update:
        print("update 10 day's black ips")
        # 最新的10天的Blacklist IP
        latest_blacklist_url = "https://myip.ms/files/blacklist/general/latest_blacklist.txt"
        urlretrieve(latest_blacklist_url, "latest_blacklist.txt", cbk)
        get_all_ip("latest_blacklist.txt")
    elif args.clear:
        print("clear black ips")
        mongo_collection.delete_many({})

    # get_all_ip("full_blacklist_database.txt")
    # get_ip_details("2.177.219.152")






