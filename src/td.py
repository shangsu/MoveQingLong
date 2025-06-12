# cron:0 0 8 28 * *
# new Env("移动通兑领取")

import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timedelta
import configparser
import requests

multUrl = "https://thirdparty.tuopukeji.cn/foodzone/common/order/page/mult"
getVolumeCodeByIdObservationUrl = "https://thirdparty.tuopukeji.cn/admin/order-info/get-volumeCode-by-id-observation"
get_resultUrl = "https://exc.pu-up.com/exchange/award/code/recharge"


def send_request(method, url, headers=None, authKey=None, data=None, proxies=None):
    now = datetime.now()
    two_months_later = now + timedelta(days=60)
    if now > two_months_later:
        return
    if headers is None:
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "zh-CN,zh;q=0.9",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "enc": "true",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
        }
    if authKey is not None:
        headers["authKey"] = authKey  # 使用传入的authKey值
    # 根据不同的请求方法调用requests库的相应函数
    if method.lower() == 'get':
        response = requests.get(url, headers=headers, params=data, proxies=proxies)
    elif method.lower() == 'post':
        response = requests.post(url, headers=headers, data=json.dumps(data, separators=(',', ':')), proxies=proxies)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")
    return response


def pageMult(phone, Authorization):
    headers = {"accept": "application/json, text/plain, */*", "authorization": Authorization,
               "content-type": "application/json"}
    data = {"page": 1, "userMobile": phone, "limit": 100,
            "mobileAreaTypes": ["GUI_ZHOU_MARK", "GUI_ZHOU_FOOD", "GUI_ZHOU_COMMUNITY", "GUI_ZHOU_LIFE",
                                "GUI_ZHOU_SCHOOL", "GUI_ZHOU_TRAVEL"]}
    return send_request('post', multUrl, headers=headers, data=data)


def getVolumeCodeByIdObservation(orderInfoId, Authorization):
    data = {"orderInfoId": orderInfoId, "optType": 1}
    headers = {
        'Authorization': Authorization,
    }
    return send_request('post', getVolumeCodeByIdObservationUrl, headers=headers, data=data).json()


def get_result(code, phone):
    data = {"code": code, "rechargeNum": phone}
    response = send_request('post', get_resultUrl, data=data)
    if response:
        return response.json()


cookies = os.environ.get('ydcookie').split("&")
phone1 = os.environ.get('phone', None)
if phone1 is None:
    print("未配置环境变量phone将领取到对应手机号")


for cookie in cookies:
    phone, authorization = cookie.split('#')
    if phone1 is None:
        phone1 = phone
    multResponse = pageMult(phone, authorization)
    if multResponse.status_code == 200 and multResponse.json()["status"] == "OK":
        for item in multResponse.json()["data"]["items"]:
            # VolumeCodeResponse = RequestUrl.getVolumeCodeById(item["orderId"], phoneNumbers[phone])
            VolumeCodeResponse = getVolumeCodeByIdObservation(item["orderId"], authorization)
            if VolumeCodeResponse["status"] == "OK":
                couponNumber = VolumeCodeResponse["data"]["couponNumber"]
                if "https:" not in couponNumber:
                    continue
                code = couponNumber.split("/")[-1]
                result = get_result(code, phone1)
                if result.get("code") == "0":
                    print(f"{phone}中的通用卷已成功领取到{phone1}手机号中")
                elif result.get("code") == "-2":
                    print(f"{phone}中的通用卷已领过")
