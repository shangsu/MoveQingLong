# cron:0 0 8 10 * *
# new Env("移动立减金领取")

import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timedelta
import configparser
from time import sleep

import requests

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.backends import default_backend
import re
import base64
import rsa

# 设置加密参数
key = b'4h7j2k5d1g3f4l6q'
public_key = ('MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCFCsHBe'
              '/lTjbWav43ISrFhlq3YFGb3nDO7MFPdeCFR6xumd8gFcxxLtruAUrPeuKmllBCqidF3l'
              '/YaKnhEdOqkqbpjbjfrULKkmfFSanVsmdrw9VPpV6dCfifDYgW8cbH5sKy31J36pSc7f3m1+rHLlGEVQ/CAkNIoQqtGUl9mWQIDAQAB')
iv = b'9e8r4j7k9l0i3h5w'

getListUrl = "https://thirdparty.tuopukeji.cn/admin/h5/equity-order/page-phone-conceal"
exchangeUrl = "https://thirdparty.tuopukeji.cn/h5/equity/common/exchange"
pageByBrandUrl = "https://thirdparty.tuopukeji.cn/foodzone/common/query/pageByBrand"
equityOrderDetailUrl = "https://thirdparty.tuopukeji.cn/admin/equity-order/equityOrderDetail"
getVolumeCodeByIdUrl2 = "https://thirdparty.tuopukeji.cn/admin/h5/equity-order/get-volume-code-by-id"
get_resultUrl2 = "https://exc.pu-up.com/exchange/award/code/recharge"


# ase加密
def aesEncrypt(plainText):
    # print("加密：" + plainText)
    # 创建 AES 加密器
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # 对明文进行 PKCS7 填充
    padder = PKCS7(algorithms.AES.block_size).padder()
    padded_plaintext = padder.update(plainText.encode('utf-8')) + padder.finalize()

    # 执行加密
    ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()

    # 将加密结果转换为 base64 编码的 UTF-8 字符串
    encrypted = base64.b64encode(ciphertext).decode('utf-8')
    # print("加密结果" + encrypted)
    return encrypted


# ase解密
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


def _str2key(s):
    # 对字符串解码
    b_str = base64.b64decode(s)

    if len(b_str) < 162:
        return False

    hex_str = ''

    # 按位转换成16进制
    for x in b_str:
        h = hex(x)[2:]
        h = h.rjust(2, '0')
        hex_str += h

    # 找到模数和指数的开头结束位置
    m_start = 29 * 2
    e_start = 159 * 2
    m_len = 128 * 2
    e_len = 3 * 2

    modulus = hex_str[m_start:m_start + m_len]
    exponent = hex_str[e_start:e_start + e_len]

    return modulus, exponent


# rsa加密
def rsa_encrypt(s, pubkey_str):
    """
    rsa加密
    :param s:
    :param pubkey_str:公钥
    :return:
    """
    key = _str2key(pubkey_str)
    modulus = int(key[0], 16)
    exponent = int(key[1], 16)
    pubkey = rsa.PublicKey(modulus, exponent)
    return base64.b64encode(rsa.encrypt(s.encode(), pubkey)).decode()


def getCode(phone):
    # print("加密：" + phone)
    return rsa_encrypt(phone, public_key)


# ase加密
def aesEncrypt(plainText):
    # print("加密：" + plainText)
    # 创建 AES 加密器
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()

    # 对明文进行 PKCS7 填充
    padder = PKCS7(algorithms.AES.block_size).padder()
    padded_plaintext = padder.update(plainText.encode('utf-8')) + padder.finalize()

    # 执行加密
    ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()

    # 将加密结果转换为 base64 编码的 UTF-8 字符串
    encrypted = base64.b64encode(ciphertext).decode('utf-8')
    # print("加密结果" + encrypted)
    return encrypted


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


def get_list(Authorization):
    current_date = datetime.now()
    # 提取年份和月份
    year = current_date.year
    month = current_date.month
    str = ('{"page":1,"limit":500,"orders":[{"asc":false,"column":"id"}],"orderStatus":"SUCCESS","isHistory":false,'
           '"businessType":"RECEIVE","orderMonth":"2407"}')
    data = json.loads(str)
    data["orderMonth"] = f"{year}{month:02d}"
    parm = json.dumps(data)
    data = {"reqEnc": aesEncrypt(parm)}
    headers = {"Enc": "true", "Content-Type": "application/json", "Authorization": Authorization}
    response = send_request('post', getListUrl, headers=headers, data=data)
    deParm = aesDecrypt(response.json()["resEnc"])
    return json.loads(deParm)


def exchange(Authorization, phone, writeCode, dataId):
    parm = f'{{"userPhone": "{phone}", "volumeCode": "{writeCode}", "id": "{dataId}"}}'
    data = {"reqEnc": aesEncrypt(parm)}
    headers = {"Enc": "true", "Content-Type": "application/json", "Authorization": Authorization}
    response = send_request('post', exchangeUrl, headers=headers, data=data)
    deParm = aesDecrypt(response.json()["resEnc"])
    return json.loads(deParm)


def equityOrderDetail(Authorization, orderId):
    data = {"id": orderId}
    headers = {
        'Authorization': Authorization,

    }
    data = (send_request('post', equityOrderDetailUrl, headers=headers, data=data).json())
    # data = send_request('post', equityOrderDetailUrl, headers=headers, data=data).text
    return data


def getVolumeCodeById2(Authorization, orderId):
    data = {"id": orderId}
    headers = {
        'Authorization': Authorization,
    }
    data = send_request('post', getVolumeCodeByIdUrl2, headers=headers, data=data).json()
    return data


def get_result2(code, phone):
    data = {"code": code, "rechargeNum": phone}
    response = send_request('post', get_resultUrl2, data=data)
    if response:
        return response.json()


cookies = os.environ.get('ydcookie').split("&")
if len(cookies) < 1:
    print("未配置环境变量")
    pass
phone1 = os.environ.get('phone', None)
if phone1 is None:
    print("未配置环境变量phone暂不领取配置的业务")

for cookie in cookies:
    sleep(1)
    phone, authorization = cookie.split('#')
    data = get_list(authorization)
    if data is not None:
        print("领取账号：" + phone)
        if data["data"]["total"] > 0:
            items = data["data"]["items"]
            for item in items:
                if item["equityType"] == "API_RECHARGE":
                    result = exchange(authorization, phone, item.get("writeCode", {}),
                                      item.get("id", {}))
                    if "ERROR" not in result.get("status"):
                        print("领取成功：" + item.get("writeCode"))
                    else:
                        print("领取失败：" + result.get("errorMsg"))
                elif item["equityType"] == "REAL_API_URL" and phone1 is not None:
                    # else:
                    data = equityOrderDetail(authorization, item["id"]).get("data")
                    #     couponNumber = item["id"]
                    VolumeCodeResponse = getVolumeCodeById2(authorization, item["id"])
                    if VolumeCodeResponse["status"] == "OK":
                        couponNumber = VolumeCodeResponse["data"]["volumeCode"]
                        # couponNumber = data["volumeCode"]
                        if "https:" not in couponNumber:
                            continue
                        code = couponNumber.split("/")[-1]
                        result = get_result2(code, phone1)
                        if result.get("code") == "0":
                            print(f"{phone}中的通用卷已成功领取到{phone1}手机号中")
                        elif result.get("code") == "-2":
                            print(f"{phone}中的通用卷已领过")
                        else:
                            print(f"出错了")
