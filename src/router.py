from src.tools import get_current_time, get_weather, get_exchange_rate

def route_query(query: str) -> str:
    print(f"收到问题: {query}")

    if "时间" in query or "几点" in query:
        print("路由到: 时间工具")
        return get_current_time()

    elif "天气" in query:
        print("路由到: 天气工具")
        return get_weather()

    elif "汇率" in query or "美元" in query or "人民币" in query:
        print("路由到: 汇率工具")
        return get_exchange_rate()

    else:
        print("路由失败: 未识别问题")
        return "暂时无法识别你的问题，请尝试输入与时间、天气或汇率相关的问题。"