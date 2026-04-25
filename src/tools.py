from datetime import datetime
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_current_time() -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"当前时间是：{now}"

def get_weather() -> str:
    return "今天天气晴，气温 26℃。这是一个模拟天气结果。"

def get_exchange_rate() -> str:
    api_key = os.getenv("EXCHANGE_API_KEY")

    if not api_key:
        return "未检测到汇率 API Key，当前返回模拟数据：美元兑人民币约为 7.20。"

    try:
        url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest/USD"
        response = requests.get(url, timeout=10)
        data = response.json()

        if data.get("result") == "success":
            cny_rate = data["conversion_rates"].get("CNY")
            return f"当前美元兑人民币汇率约为：{cny_rate}"
        else:
            return "汇率接口调用失败，返回模拟数据：美元兑人民币约为 7.20。"
    except Exception as e:
        return f"汇率接口调用异常：{e}"