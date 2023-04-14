"""
func: 从VenusEye威胁情报中心获取IP/domain/URL的标签、分类、家族
频繁调用也会出现滑块验证
"""
import random
import time
import requests
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains


headers = {
    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "accept": "application/json, text/javascript, */*; q=0.01",
    "referer": "https://www.venuseye.com.cn/ip/",
    "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Mobile Safari/537.36"
}


def get_track(distance, t):  # distance为传入的总距离，a为加速度
    track = []
    current = 0
    mid = distance * t / (t + 1)
    v = 0
    while current < distance:
        if current < mid:
            a = 2
        else:
            a = -1
        v0 = v
        v = v0 + a * t
        move = v0 * t + 1 / 2 * a * t * t
        current += move
        track.append(round(move))
    return track


def slider_verification_windows(url="https://www.venuseye.com.cn/ip/"):
    """
    func:
        解决频繁访问出现的滑块验证
    """
    print("in slider_verification_windows")
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])  # 防止反爬
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')  # 避免webdriver检测
    # chrome_options.add_argument('--headless')
    chrome_options.add_argument(
        "user-agent='Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.60 Mobile Safari/537.36'"
    )  # 使用这个设置可以避免网站检测到你使用的是无界模式进行反抓取
    # chrome_options.add_argument('--proxy-server=http://127.0.0.1:10809')  # 利用v2ray配置代理

    driver = webdriver.Chrome(options=chrome_options)
    # driver.set_page_load_timeout(300)
    driver.maximize_window()  # 仅仅适配到当前显示屏大小，数据偶尔还是不完整，需要下滑鼠标

    try:
        driver.get(url)
        wait_obj = WebDriverWait(driver, 600)  # 创建显示等待对象, 设置等待条件

        wait_obj.until(expected_conditions.visibility_of_element_located(  # 判断Ip数据是否出现
            (By.XPATH, "//span[@class='nc_iconfont btn_slide']")))

        slider = driver.find_element(by=By.XPATH, value="//span[@class='nc_iconfont btn_slide']")
        if slider.is_displayed():   # 判断滑块是否可见
            action = ActionChains(driver)  # 动作链
            action.click_and_hold(on_element=slider).perform()  # 点击并且不松开鼠标
            # action.move_by_offset(xoffset=293, yoffset=0).perform()  # 往右边移动258个位置，速度快易被反爬
            tracks = get_track(293, random.choice([3]))
            for x in tracks:
                action.move_by_offset(xoffset=x, yoffset=0).perform()  # 控制速率移动
            time.sleep(0.5)
            action.pause(1).release().perform()  # 松开鼠标

            cookie = driver.get_cookies()
            cookie_dict = {}
            cookie_list = []
            for item in cookie:
                if item["name"] != "_uab_collina":
                    cookie_dict[item["name"]] = item["value"]
                    cookie_list.append(item["name"] + "=" + item["value"])

            cookie_str = '; '.join(item for item in cookie_list)  # 获取到登录cookie,就可以关闭窗口了

            print("cookie_str:%s" % cookie_str)  # Hm_lvt_efa6afa67fd33f485307e3a8f373bbb4=1681459941; Hm_lpvt_efa6afa67fd33f485307e3a8f373bbb4=1681459941
            # print("cookie_dict:%s" % cookie_dict)

            headers.update({'cookie': cookie_str})

    except:
        print(traceback.print_exc())
    finally:
        driver.close()


def get_ip_ioc(data):
    print("in get ip ioc")
    ioc_url = "https://www.venuseye.com.cn/ve/ip/ioc"
    ioc_req = requests.post(url=ioc_url, headers=headers, data=data, timeout=60)

    if ioc_req.status_code == 200:
        json_data_ioc = ioc_req.json()
        data_ioc = json_data_ioc.get("data", {})
        ioc_list = data_ioc.get("ioc", [])
        status_code_ioc = json_data_ioc["status_code"]

        return status_code_ioc, ioc_list


def get_ip_info(data):
    print("in get ip info")
    url = "https://www.venuseye.com.cn/ve/ip"
    req = requests.post(url=url, headers=headers, data=data, timeout=60)
    if req.status_code == 200:
        json_data = req.json()
        status_code = json_data["status_code"]
        data = json_data.get("data", {})

        return status_code, data



def get_ipinfo_from_enuseye(clue):
    """
    clue: ip/domain/url
    """
    ip_info_dict = {}

    data = {"target": clue}

    status_code_ioc, ioc_list = get_ip_ioc(data)
    if status_code_ioc == 409:
        slider_verification_windows()
        time.sleep(1)
        status_code, ioc_list = get_ip_ioc(data)

    all_categories_list, all_families_list, all_organizations_list = [], [], []
    for ioc in ioc_list:
        categories_list = ioc.get("categories", [])  # 分类
        families_list = ioc.get("families", [])  # 家族
        organizations_list = ioc.get("organizations", [])  # 组织

        all_categories_list.extend(categories_list)
        all_families_list.extend(families_list)
        all_organizations_list.extend(organizations_list)

    ip_info_dict["categories"] = list(set(all_categories_list))
    ip_info_dict["families"] = list(set(all_families_list))
    ip_info_dict["organizations"] = list(set(all_organizations_list))

    status_code, data = get_ip_info(data)
    if status_code == 409:
        slider_verification_windows()
        time.sleep(1)
        status_code, data = get_ip_info(data)

    open_port_list = data.get("ports", [])
    tags_list = data.get("tags", [])
    # search_hot = data.get("search_hot", None)
    threat_score = data.get("threat_score", None)

    ip_info_dict["open_port"] = open_port_list
    ip_info_dict["tags"] = tags_list
    ip_info_dict["threat_score"] = threat_score

    print("The clue %s information on the venuseye website is %s" % (clue, ip_info_dict))
    return ip_info_dict


if __name__ == "__main__":
    get_ipinfo_from_enuseye("5.236.171.222")