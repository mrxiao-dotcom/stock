# 股票信息管理系统 - 部署配置指南

## 1. 环境准备

### 1.1 Python环境
1. 下载并安装 Python 3.8+
   - 访问 [Python官网](https://www.python.org/downloads/)
   - 下载 Windows 安装包
   - 安装时勾选 "Add Python to PATH"

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

### 1.2 环境变量配置
1. 在项目根目录创建 config.env 文件
2. 添加以下配置：
   ```
   TUSHARE_TOKEN=your_token_here
   ```
   将 your_token_here 替换为您的 Tushare API token

### 1.3 数据库配置
...