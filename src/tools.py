from datetime import datetime
import math
import os

import requests
from dotenv import load_dotenv

load_dotenv()

def get_current_time() -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"本机时间（运行电脑的本地时区）：{now}"


def get_weather() -> str:
    return (
        "【演示天气】固定样例：晴，26℃。"
        "未查询任何城市、日期或实时天气，不能用来回答指定地点或日期的天气。"
    )


def get_exchange_rate() -> str:
    api_key = os.getenv("EXCHANGE_API_KEY", "").strip()
    unavailable = "未获取汇率：接口暂不可用，请稍后重试；没有返回模拟报价。"
    invalid_data = "未获取汇率：接口数据不完整或无效；没有返回模拟报价。"

    if not api_key:
        return "未获取汇率：未配置 EXCHANGE_API_KEY。时间与演示天气仍可使用。"

    try:
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/USD"
        response = requests.get(url, timeout=10, allow_redirects=False)
        response.raise_for_status()
        if response.status_code != 200:
            return unavailable
    except requests.RequestException:
        # Request exceptions can contain the URL, which embeds the API key.
        return unavailable

    try:
        data = response.json()
    except ValueError:
        return invalid_data

    if not isinstance(data, dict) or data.get("result") != "success":
        return invalid_data
    rates = data.get("conversion_rates")
    if data.get("base_code") != "USD" or not isinstance(rates, dict):
        return invalid_data
    rate = rates.get("CNY")
    if isinstance(rate, bool) or not isinstance(rate, (int, float)):
        return invalid_data
    try:
        if rate <= 0 or not math.isfinite(rate):
            return invalid_data
    except OverflowError:
        return invalid_data
    return f"接口返回：1 USD = {rate} CNY（来源：ExchangeRate-API；供应商参考汇率）。"
