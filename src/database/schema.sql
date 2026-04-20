-- Text-to-SQL 营养数据库 Schema

-- 1. 食物基础表（每种食物的营养成分）
CREATE TABLE IF NOT EXISTS food (
    id INTEGER,
    name VARCHAR(50),        -- 食物名称
    calorie DECIMAL(6,2),   -- 每100g热量(kcal)
    protein DECIMAL(6,2),   -- 每100g蛋白质(g)
    fat DECIMAL(6,2),       -- 每100g脂肪(g)
    carb DECIMAL(6,2),      -- 每100g碳水(g)
    PRIMARY KEY (id)
);

-- 2. 日记录表（每天的整体摄入）
CREATE TABLE IF NOT EXISTS daily_record (
    id INTEGER PRIMARY KEY,
    date DATE,
    total_calorie DECIMAL(8,2),   -- 当日总热量
    total_protein DECIMAL(6,2),   -- 当日总蛋白质
    target_calorie DECIMAL(6,2),  -- 目标热量
    target_protein DECIMAL(6,2)   -- 目标蛋白质
);

-- 3. 餐次记录表（每餐吃了什么）
CREATE TABLE IF NOT EXISTS meal_record (
    id INTEGER PRIMARY KEY,
    daily_id INTEGER,       -- 关联daily_record
    meal_type VARCHAR(10), -- 早餐/午餐/晚餐/加餐
    food_id INTEGER,        -- 关联food
    weight_g INTEGER        -- 吃了多少克
);
