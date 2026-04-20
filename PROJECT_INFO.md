# Text-to-SQL Multi-Agent System

## 项目简介

一个基于大语言模型的 Text-to-SQL 系统，可以将自然语言问题转换为 SQL 查询。系统采用多 Agent 协作架构，支持 Web 界面和 CLI 两种交互方式。

## 技术架构

### 技术栈
- **语言**: Python 3.11 + TypeScript
- **数据库**: DuckDB (嵌入式关系型数据库)
- **Agent 框架**: CrewAI
- **大模型**: MiniMax M2.7 (Anthropic 兼容接口)
- **前端**: React 18 + Vite + TailwindCSS
- **后端 API**: FastAPI

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面                              │
│  ┌─────────────────┐        ┌─────────────────────────┐   │
│  │   Web 界面      │        │      CLI 交互模式         │   │
│  │  (React+Vite)  │        │  (python -m src.main)   │   │
│  └────────┬────────┘        └───────────┬─────────────┘   │
└───────────┼─────────────────────────────┼───────────────────┘
            │                             │
            ▼                             ▼
┌─────────────────────────────────────────────────────────────┐
│                      API 层                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              FastAPI Server (:8000)                  │   │
│  │  - POST /query     处理查询请求                      │   │
│  │  - GET  /          健康检查                         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent 编排层                              │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐│
│  │ 意图理解  │──▶│Schema检索│──▶│SQL 生成  │──▶│SQL 审查  ││
│  │  Agent   │   │  Agent   │   │  Agent   │   │  Agent   ││
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘│
│                                            │              │
│                                    审查通过 │              │
│                                     ◀──────┘              │
│                                            │              │
│                                   审查失败 │ 最多3次      │
│                                     ──────▶ [重新生成]     │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      数据层                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              DuckDB (nutrition.db)                  │   │
│  │  - food 表         食物营养成分                      │   │
│  │  - daily_record 表 每日摄入记录                     │   │
│  │  - meal_record 表  餐次记录                         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Agent 详细说明

### Agent 1: 意图理解
**文件**: `src/agents/intent_agent.py`

解析用户问题，提取：
- 查询目标 (calorie/protein/fat/carb)
- 时间范围 (today/this_week/this_month)
- 聚合方式 (sum/avg/max/min)
- 是否需要目标对比
- 其他筛选条件

### Agent 2: Schema 检索
**文件**: `src/agents/schema_agent.py`

根据意图确定：
- 需要查询的表
- 需要查询的字段
- 表之间的 JOIN 关系

### Agent 3: SQL 生成
**文件**: `src/agents/sql_gen_agent.py`

生成 DuckDB 兼容的 SQL 语句

### Agent 4: SQL 审查
**文件**: `src/agents/review_agent.py`

检查维度：
- 语法正确性
- 逻辑正确性
- 性能检查
- 安全性

## 项目文件结构

```
text-to-sql/
├── src/
│   ├── main.py              # CLI 入口
│   ├── config.py            # 配置管理 (从 .env 加载)
│   ├── llm_client.py        # MiniMax LLM 客户端
│   ├── api_server.py        # FastAPI HTTP 服务器
│   ├── database/
│   │   ├── schema.sql       # 数据库 DDL
│   │   └── duckdb_utils.py  # 数据库工具函数
│   ├── agents/
│   │   ├── intent_agent.py     # 意图理解
│   │   ├── schema_agent.py     # Schema 检索
│   │   ├── sql_gen_agent.py    # SQL 生成
│   │   └── review_agent.py     # SQL 审查
│   ├── orchestrator/
│   │   └── pipeline.py         # 主编排流程 + 回退机制
│   └── prompts/
│       └── templates.py        # 各 Agent 的 Prompt 模板
├── frontend/
│   ├── src/
│   │   ├── components/         # React 组件
│   │   │   ├── QueryInput.tsx  # 问题输入组件
│   │   │   └── ResultTable.tsx # 结果表格组件
│   │   ├── services/
│   │   │   └── api.ts          # API 调用服务
│   │   ├── App.tsx             # 主应用组件
│   │   └── main.tsx            # 前端入口
│   ├── package.json
│   ├── vite.config.ts          # Vite 配置 (代理 /api 到后端)
│   └── tailwind.config.js      # Tailwind CSS 配置
├── tests/
│   └── test_pipeline.py         # 流程测试
├── data/
│   └── nutrition.db             # DuckDB 数据库
├── .env                         # 环境配置
├── requirements.txt             # Python 依赖
└── README.md                    # 项目说明
```

## 关键配置

### .env 文件
```env
MINIMAX_API_KEY=<your_api_key>
MINIMAX_BASE_URL=https://api.minimaxi.com/anthropic
MODEL_NAME=MiniMax-M2.7
DATABASE_PATH=./data/nutrition.db
MAX_RETRIES=3
```

### 端口配置
- 后端 API: 8000
- 前端 Dev: 3000
- Vite 代理: /api -> http://localhost:8000

## 启动方式

### 开发模式
```bash
# 终端 1: 后端
python -m src.api_server

# 终端 2: 前端
cd frontend && npm run dev
```

### CLI 模式
```bash
python -m src.main --interactive
python -m src.main "今天吃了多少蛋白质？"
```

### Docker
```bash
docker-compose up --build
```

## 注意事项

1. **API Key**: 需要有效的 MiniMax API Key
2. **数据库**: 首次运行需要初始化 `python -m src.main --init`
3. **模型**: 当前使用 MiniMax-M2.7，需确认 API 支持
4. **回退机制**: SQL 审查失败会自动重试，最多 3 次

## 开发记录

| 日期 | 内容 |
|------|------|
| 2026-04-20 | 初始化项目，实现 4 个 Agent + CLI |
| 2026-04-20 | 添加 FastAPI 服务器和 React 前端 |
| 2026-04-20 | 推送到 GitHub master 分支 |
