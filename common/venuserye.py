"""
func: 从VenusEye威胁情报中心获取IP/domain/URL的标签、分类、家族
频繁调用也会出现滑块验证
"""
import requests
import time


def get_ipinfo_from_enuseye(clue):
    """
    clue: ip/domain/url
    """
    ip_info_dict = {}

    head = {
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "referer": "https://www.venuseye.com.cn/ip/",
        "x-requested-with": "XMLHttpRequest",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
    }
    data = {'target': clue}

    ioc_url = "https://www.venuseye.com.cn/ve/ip/ioc"
    ioc_req = requests.post(url=ioc_url, headers=head, data=data, timeout=60)
    if ioc_req.status_code == 200:
        json_data_ioc = ioc_req.json()
        if json_data_ioc["status_code"] == 200:
            data_ioc = json_data_ioc["data"]
            ioc_list = data_ioc["ioc"]

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

    url = "https://www.venuseye.com.cn/ve/ip"
    req = requests.post(url=url, headers=head, data=data, timeout=60)
    if req.status_code == 200:
        json_data = req.json()
        if json_data["status_code"] == 200:
            data = json_data["data"]
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
    get_ipinfo_from_enuseye('5.236.171.222')