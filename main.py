from src.router import route_query

def main():
    while True:
        query = input("请输入你的问题（输入 exit 退出）: ")
        if query.lower() == "exit":
            print("程序已退出。")
            break

        result = route_query(query)
        print(result)
        print("-" * 30)

if __name__ == "__main__":
    main()