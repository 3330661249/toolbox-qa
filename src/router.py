"""Small deterministic rules, with an explicit USD-to-CNY request boundary."""

import re

from src.tools import get_current_time, get_exchange_rate, get_weather


_CURRENCY_TOPIC = re.compile(
    r"汇率|换算|兑换|美元|人民币|欧元|日元|英镑|港币|澳元|加元|韩元|瑞郎|"
    r"(?<![A-Za-z0-9])(?:USD|CNY|RMB|EUR|JPY|GBP|HKD|AUD|CAD|CHF|KRW)(?![A-Za-z0-9])",
    re.IGNORECASE,
)
_USD_CNY_REQUEST = re.compile(
    r"(?:请)?(?:查询|查看|查一下|查|告诉我)?(?:现在|当前|最新)?"
    r"(?:美元|usd)(?:兑换|兑|对|/|->|→|到)(?:人民币|cny|rmb)"
    r"(?:的)?(?:汇率)?(?:是多少|多少|呢)?"
)
_HELP = "请输入单个问题：本机时间、演示天气，或明确的 USD/CNY 汇率查询。"
_RATE_SCOPE = (
    "仅支持明确的 USD→CNY 单位汇率查询；不支持其他币种、反向或金额换算。"
    "示例：美元兑人民币汇率，或 USD/CNY。"
)


def route_query(query: str) -> str:
    query = query.strip()
    if not query:
        return _HELP

    wants_time = "时间" in query or "几点" in query
    wants_weather = "天气" in query
    wants_rate = bool(_CURRENCY_TOPIC.search(query))
    if sum((wants_time, wants_weather, wants_rate)) > 1:
        return "检测到多个工具请求，请拆成单个问题后分别查询。"

    if wants_time:
        return get_current_time()
    if wants_weather:
        return get_weather()
    if wants_rate:
        normalized = re.sub(r"\s+", "", query).lower().rstrip("?？。.!！")
        if not _USD_CNY_REQUEST.fullmatch(normalized):
            return _RATE_SCOPE
        return get_exchange_rate()
    return _HELP
