# 股票数据分析系统

## 功能模块

1. 数据浏览模块
   - 展示板块列表和个股信息
   - 支持板块名称搜索
   - 显示个股涨跌幅和成交额
   - 展示板块成分股的涨跌分布

2. 数据维护模块
   - 历史数据更新
   - 板块信息管理
   - 成分股管理
   - 基本面数据更新
     * 财务数据更新
     * 每日指标更新

3. 板块寻龙模块
   - 左侧展示板块列表
   - 右侧展示成分股详细信息
   - 包含股票代码、名称、总市值、财务指标等
   - 支持多维度排序和筛选
   - 自动获取最新财报数据

## 技术栈

- 后端：Flask + SQLite + Tushare
- 前端：Bootstrap + ECharts
- 数据源：Tushare Pro API

## 项目结构

```
stock_graph/
├── app.py              # 主应用程序
├── data_updater.py     # 数据更新模块（包含基本面数据更新）
├── stock_top20.py      # 板块分析模块
├── static/             # 静态文件目录
│   ├── js/
│   │   ├── update.js
│   │   ├── echarts.min.js
│   │   └── bootstrap.bundle.min.js
│   └── css/
│       └── bootstrap.min.css
├── templates/          # 模板目录
│   └── index.html
└── example.db         # SQLite数据库