# Text-to-SQL 多 Agent 项目任务拆分

## 技术栈

| 项目 | 选择 |
|------|------|
| 编程语言 | Python |
| 数据库 | DuckDB（关系型，文件形式，分析能力强） |
| Agent 框架 | CrewAI |
| 大模型 | MiniMax |

---

## 测试数据库 Schema

三张表，足以支撑所有查询场景：

```sql
-- 1. 食物基础表（每种食物的营养成分）
CREATE TABLE food (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50),        -- 食物名称
    calorie DECIMAL(6,2),   -- 每100g热量(kcal)
    protein DECIMAL(6,2),   -- 每100g蛋白质(g)
    fat DECIMAL(6,2),       -- 每100g脂肪(g)
    carb DECIMAL(6,2)       -- 每100g碳水(g)
);

-- 2. 日记录表（每天的整体摄入）
CREATE TABLE daily_record (
    id INTEGER PRIMARY KEY,
    date DATE,
    total_calorie DECIMAL(8,2),   -- 当日总热量
    total_protein DECIMAL(6,2),   -- 当日总蛋白质
    target_calorie DECIMAL(6,2),  -- 目标热量
    target_protein DECIMAL(6,2)   -- 目标蛋白质
);

-- 3. 餐次记录表（每餐吃了什么）
CREATE TABLE meal_record (
    id INTEGER PRIMARY KEY,
    daily_id INTEGER,       -- 关联daily_record
    meal_type VARCHAR(10), -- 早餐/午餐/晚餐/加餐
    food_id INTEGER,        -- 关联food
    weight_g INTEGER        -- 吃了多少克
);
```

**能支持的查询类型：**

- "今天我吃了多少热量？" → 查 daily_record
- "这周每天蛋白质摄入多少？" → 聚合查询
- "我今天吃的蛋白质够不够？" → 关联查 + 对比
- "午餐吃了哪些食物？" → 条件查询 + JOIN

---

## 项目初始化

- 目录结构设计、模块划分
- 依赖管理（crewai、duckdb、langchain 等）
- Git 初始化、README 编写
- API Key 配置（MiniMax）

---

## Agent 角色定义

### Agent 1：意图理解 Agent

**目标：** 把用户自然语言问题转成结构化的查询意图

**输入：** 用户原始问题（如："我这周每天吃了多少蛋白质？"）

**输出：** 结构化的查询需求，包含：
- 查询目标（热量/蛋白质/脂肪/碳水）
- 时间范围（今天/本周/本月/自定义）
- 聚合方式（求和/平均/最大/最小）
- 是否和目标对比
- 其他筛选条件

**Prompt 设计要点：**
- 需要识别用户说的是哪天/哪周/哪月
- 需要判断是要查单一数值还是趋势
- 需要判断是否需要和目标做对比

---

### Agent 2：Schema 检索 Agent

**目标：** 根据意图理解 Agent 输出的查询目标，从数据库中找到相关的表和字段

**输入：** 结构化的查询需求（意图理解 Agent 的输出）

**输出：** 相关的表名 + 字段名 + 字段含义 + 对应的值示例

**Prompt 设计要点：**
- 需要判断查哪张表（food / daily_record / meal_record）
- 需要判断是否需要 JOIN
- 输出要有字段描述，方便下一个 Agent 理解字段含义
- 可以直接读数据库的 DDL 信息

---

### Agent 3：SQL 生成 Agent

**目标：** 根据意图 + Schema 信息生成可执行的 SQL

**输入：** 结构化意图 + Schema 信息

**输出：** 一条可执行的 SQL 语句

**Prompt 设计要点：**
- 需要参考 Schema 信息确定表和字段
- 需要根据意图确定 WHERE 条件、GROUP BY、聚合函数
- 生成的 SQL 必须是 DuckDB 兼容的语法
- 如果查询跨度大，需要处理 JOIN 逻辑

---

### Agent 4：SQL 审查 Agent

**目标：** 检查生成的 SQL 是否正确、合理

**输入：** SQL 语句 + Schema 信息

**输出：** 审查结果（通过/不通过）+ 不通过原因 + 修正建议

**审查维度：**
- 语法正确性（字段名、表名是否正确）
- 逻辑正确性（查询逻辑是否符合意图）
- 性能检查（是否有潜在的全表扫描）
- 安全性（是否有注入风险，恒成立/永假的WHERE条件）

**Prompt 设计要点：**
- 如果发现问题，要给出具体的修正建议
- 设置通过/不通过的判断标准

---

## 编排层

### 主流程串联

用户提问 → 意图理解 → Schema 检索 → SQL 生成 → 审查 → 输出结果

各 Agent 的输出格式要统一，方便下个 Agent 接住。

### 回退机制

SQL 审查不通过时，返回 SQL 生成 Agent 重新生成。

### 迭代次数

最多允许重新生成 3 次，超过次数输出错误信息或输出原始 SQL 附带警告。

---

## 测试验收

能正确回答用户问题即算通过。

准备 10-20 个不同类型的问答用例，覆盖：
- 热量查询
- 蛋白质查询
- 趋势分析（每日/每周）
- 目标对比

---

## 部署

- Docker 容器化部署
- Web/CLI 交互界面（至少有一个可用）
- 输出格式：SQL + 自然语言回答
