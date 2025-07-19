# Disney+ 价格爬虫与汇率转换器

这个项目自动抓取各国Disney+订阅价格，并转换为人民币进行比较分析。支持GitHub Actions自动化运行，每周更新数据。

## 🌟 功能特性

- 🌍 **全球价格抓取**: 自动抓取全球多个国家的Disney+价格
- 💰 **实时汇率转换**: 实时汇率转换，将所有价格转换为人民币
- 🤖 **自动化运行**: GitHub Actions每周自动运行
- 🔐 **安全管理**: 使用GitHub Secrets安全管理API密钥
- 📁 **详细报告**: 生成详细的JSON报告和统计信息
- 🗂️ **历史归档**: 自动归档历史数据，按年份组织，保留所有运行结果

## 📂 项目结构

```
├── disney.py                           # 主爬虫脚本
├── disney_rate_converter.py            # 汇率转换器
├── requirements.txt                      # Python依赖
├── .env.example                         # 环境变量示例
├── .gitignore                           # Git忽略文件
├── archive/                             # 历史数据归档目录
│   ├── 2025/                          # 2025年数据
│   └── ...
├── .github/workflows/
│   └── weekly-disney-scraper.yml       # 主自动化工作流
└── README.md                            # 项目文档
```

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <your-repo-url>
cd disneyplus-prices
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
playwright install
```

### 3. 配置API密钥（必需！）
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，添加你的API密钥
API_KEY=你的API密钥
```

**重要**: 现在必须设置API密钥才能运行。获取免费API密钥：
1. 访问 [OpenExchangeRates](https://openexchangerates.org/)
2. 注册免费账户（每月1000次请求）
3. 获取你的API密钥

### 4. 手动运行
```bash
# 运行爬虫
python disney.py

# 转换汇率
python disney_rate_converter.py
```

## 🤖 GitHub Actions 自动化

### 自动化工作流

项目包含一个GitHub Actions工作流：

#### **Weekly Disney Scraper** (每周自动运行)
- **时间**: 每周日UTC时间0点（北京时间周日上午8点）
- **功能**: 自动爬取价格、转换汇率、提交数据
- **支持**: 手动触发运行

### 🔐 GitHub Secrets 配置（重要！）

为了安全使用汇率API，需要在GitHub仓库中设置secrets：

#### 设置步骤：
1. 进入GitHub仓库 → **Settings** → **Secrets and variables** → **Actions**
2. 点击 **New repository secret** 添加以下密钥：

| Secret Name | Description |
|-------------|-------------|
| `API_KEY` | 你的OpenExchangeRates API密钥 |

## 📁 输出文件

- **`disneyplus_prices.json`**: 原始爬取数据
- **`disneyplus_prices_cny_sorted.json`**: 转换为人民币并排序的数据

## ⚙️ 技术特性

- **异步爬虫**: 使用Playwright进行高效的并发爬取
- **GitHub Actions支持**: 完全支持Playwright在云端运行
- **汇率精度**: 使用Decimal确保价格计算精度

## 📄 许可证

本项目仅用于学习和研究目的。
