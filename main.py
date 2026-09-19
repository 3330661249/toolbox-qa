from src.router import route_query


def main():
    while True:
        try:
            query = input("请输入你的问题（输入 exit 退出）: ").strip()
            if query.lower() == "exit":
                print("程序已退出。")
                break

            result = route_query(query)
            print(result)
            print("-" * 30)
        except (EOFError, KeyboardInterrupt):
            print("\n程序已退出。")
            break


if __name__ == "__main__":
    main()
