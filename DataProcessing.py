# cron:0 50 23 * * ?
# new Env("数据预处理")
import ast
import threading
import time
from cryptography.hazmat.primitives.ciphers import Cipher
import configparser
import os
from collections import Counter
import requests
import json
from cryptography.hazmat.primitives.ciphers import algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.backends import default_backend
import re
import base64

filePath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.ini")
cookies = os.environ.get('ydcookie').split("&")
config = configparser.ConfigParser()
volumeUrl = 'https://thirdparty.tuopukeji.cn/foodzone/common/order/add-volume'
vouchersUrl = 'https://thirdparty.tuopukeji.cn/foodzone/common/order/getFoodVoucherByPhone/new'
pageByBrandUrl = "https://thirdparty.tuopukeji.cn/foodzone/common/query/pageByBrand"
key = b'4h7j2k5d1g3f4l6q'
iv = b'9e8r4j7k9l0i3h5w'


def send_request(method, url, headers=None, authKey=None, data=None, proxies=None):
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


def schedule_purchase(headers, data, phone):
    retries = 10
    for attempt in range(int(retries)):
        respond = send_request("post", url=volumeUrl, headers=headers, data=data)
        if respond.status_code != 200:
            print("网络被墙，请更换网络\n")
        result = respond.json()
        if result['status'] == 'ERROR':
            print(f"{phone}领取失败: {result['errorMsg']} (重试 {attempt + 1}/{retries})\n", )
            time.sleep(0.5)  # 可以选择性添加等待时间以避免过快重试
        else:
            print(f"{phone}: 领取成功\n")
            # account_purchases[phone] += 1
            break  # 成功后跳出重试循环


def schedule_purchase2(headers, dataList, phone):
    for data in dataList:
        respond = send_request("post", url=volumeUrl, headers=headers, data=data)
        if respond.status_code != 200:
            print("网络被墙，请更换网络\n")
        result = respond.json()
        if result['status'] == 'ERROR':
            print(f"{phone}领取失败: {result['errorMsg']}")


def getDataAndHeaders(auth_phone_number, product_id, specifications_id, voucher_code, authorization,
                      product_type="URL_PRODUCT", food_zone_product_type="PLUS_FOOD", brand_id="1691428476935487491",
                      mobile_area_type="GUI_ZHOU_SCHOOL"):
    headers = {
        'content-type': 'application/json',
        'accept-language': 'zh-CN,zh;q=0.9',
        'authorization': authorization,
        "cache-control": "no-cache",
        "origin": "https://mpf.tuopukeji.cn",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://mpf.tuopukeji.cn/",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Mobile/15E148 Safari/604.1"
    }
    data = {
        "orderInfoAddParam": {"contactPhone": auth_phone_number, "contactName": auth_phone_number, "products": [{
            "orderType": "URL_PRODUCT", "productId": product_id, "specificationsId": specifications_id,
            "quantity": 1,
            "storeId": None}]}, "vouchers": [voucher_code], "productType": product_type,
        "foodZoneProductType": food_zone_product_type, "authPhoneNumber": auth_phone_number, "brandId": brand_id,
        "mobileAreaType": mobile_area_type}
    return data, headers


def sunVouchers(Authorization, phone):
    headers = {'content-type': 'application/json', 'authorization': Authorization}
    data = {"authPhoneNumber": phone, "mobileAreaType": "GUI_ZHOU", "usableFoodzone": ["GUI_ZHOU_SCHOOL"]}
    # data = {"authPhoneNumber": phone, "mobileAreaType": "GUI_ZHOU", }

    try:
        response = send_request('post', vouchersUrl, headers=headers, data=data)
        response_data = response.json()
        # 处理响应
        if response_data['status'] == 'OK':
            unavailable_vouchers = response_data['data']['unavailableVoucher']
            unusedVouchers = [voucher for voucher in unavailable_vouchers if not voucher['isUsed']]
            # 统计各金额券的数量
            # print(unusedVouchers)
            voucherSummary = len(unusedVouchers)
            # 统计每种未使用券的数量
            vouch_name_counter = Counter(voucher['vouchName'] for voucher in unusedVouchers)
            print(phone)
            # print("总劵数：" + str(voucher_summaryvoucher_summary))
            for vouch_name, count in vouch_name_counter.items():
                print(f"{vouch_name}: {count}")

            return voucherSummary, unusedVouchers
        else:
            return 0, response_data["errorMsg"]
    except Exception as e:
        return 0, "网络错误，获取列表失败"


def aesDecrypt(plainText):
    # print("加密：" + plainText)
    plainText = re.sub(r'\s+', '', plainText)
    # 将 base64 编码的密文解码为字节串
    ciphertext_bytes = base64.b64decode(plainText.encode('utf-8'))

    # 创建 AES 解密器
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    # 执行解密
    padded_plaintext = decryptor.update(ciphertext_bytes) + decryptor.finalize()

    # 去除 PKCS7 填充
    unpadder = PKCS7(algorithms.AES.block_size).unpadder()
    plainText = unpadder.update(padded_plaintext) + unpadder.finalize()
    # print("解密结果：" + plainText.decode('utf-8'))
    return plainText.decode('utf-8')


def getProductInfo(brandId="1691428476935487491", mobileAreaType="GUI_ZHOU_SCHOOL"):
    data = {"brandId": brandId, "mobileAreaType": mobileAreaType}
    # print(send_request('post', pageByBrandUrl, data=data).json())
    return aesDecrypt(send_request('post', pageByBrandUrl, data=data).json()["resEnc"])


def Scramble(flag=1):
    try:
        for cookie in cookies:
            phone = cookie.split("#")[0]
            config.read(filePath)
            headerList = ast.literal_eval((config.get(phone, 'header_list')))
            dataList = ast.literal_eval(config.get(phone, 'data_list'))
            if flag == 1:
                for data in dataList:
                    threading.Thread(target=schedule_purchase, args=(headerList[0], data, phone)).start()
            else:
                threading.Thread(target=schedule_purchase2, args=(headerList[0], dataList, phone)).start()
    except Exception as e:
        print(f"ip被强了，请开代理\n")


def DataProcessing():
    try:
        for cookie in cookies:
            headerList = []
            dataList = []
            five = ""
            ten = ""
            twenty = ""
            result = json.loads(getProductInfo())
            if "#" not in cookie:
                pass
            for item in result["data"]["items"][0]["productList"]:
                if "5" in item["productName"]:
                    five = f"{item['productId']}-{item['specificationsId']}"
                elif "10" in item["productName"]:
                    ten = f"{item['productId']}-{item['specificationsId']}"
                elif "20" in item["productName"]:
                    twenty = f"{item['productId']}-{item['specificationsId']}"
            phone, authorization = cookie.split('#')
            print(f"{phone}:配正在读取配置\n")
            voucherSummary, unused_vouchers = sunVouchers(authorization, phone)
            print(f"{phone}: 配置读取成功\n")
            if voucherSummary > 0:
                for voucher in unused_vouchers:
                    # 根据券的名称执行对应的兑换操作
                    data = headers = None
                    if five is not None:
                        if '5元' in voucher['vouchName']:
                            data, headers = getDataAndHeaders(phone, five.split("-")[0], five.split("-")[1],
                                                              voucher['code'],
                                                              authorization)
                    if ten is not None:
                        if '10元' in voucher['vouchName'] or '120元' in voucher['vouchName']:
                            data, headers = getDataAndHeaders(phone, ten.split("-")[0], ten.split("-")[1],
                                                              voucher['code'],
                                                              authorization)
                    if twenty is not None:
                        if '20元' in voucher['vouchName'] or '30元' in voucher['vouchName'] or '40元' in voucher[
                            'vouchName']:
                            data, headers = getDataAndHeaders(phone, twenty.split("-")[0], twenty.split("-")[1],
                                                              voucher['code'],
                                                              authorization)
                    if data is not None and headers is not None:
                        headerList.append(headers)
                        dataList.append(data)

                    config[phone] = {
                        "header_list": str(headerList),
                        "data_list": str(dataList)
                    }
        # 将配置写入文件
        with open(filePath, 'w') as configfile:
            config.write(configfile)

    except Exception as e:
        print(f"ip被强了，请开代理\n")


if __name__ == '__main__':
    DataProcessing()
# Scramble()
