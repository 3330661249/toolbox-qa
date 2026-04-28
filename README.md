# ToolBox-QA

轻量级多工具问答助手，基于关键词路由到不同工具并返回结果。

## 功能
- 关键词工具路由（时间 / 天气 / 汇率）
- 真实 API 接入
- 环境变量管理
- 交互式循环问答
- Fallback 兜底逻辑

## 技术栈
Python / requests / python-dotenv / datetime

## 项目结构
```
toolbox-qa/
├── main.py
├── requirements.txt
├── .env.example
├── README.md
└── src/
    ├── router.py
    └── tools.py
```
