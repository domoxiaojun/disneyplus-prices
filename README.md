# Disney+ 价格爬虫与汇率转换器

这个项目自动抓取各国Disney+订阅价格，并转换为人民币进行比较分析。支持GitHub Actions自动化运行，每周更新数据。

## 🌟 功能特性

- 🌍 **全球价格抓取**: 自动抓取全球多个国家的Disney+价格
- 💰 **实时汇率转换**: 实时汇率转换，将所有价格转换为人民币
- 🤖 **自动化运行**: GitHub Actions每周自动运行
- 🔐 **安全管理**: 使用GitHub Secrets安全管理API密钥
- 📁 **详细报告**: 生成详细的JSON报告和统计信息
- 🗂️ **历史归档**: 自动归档历史数据，按年份组织，保留所有运行结果
- 🔄 **价格变化检测**: 自动对比价格变化，生成详细的变化报告
- 📋 **CHANGELOG生成**: 自动生成人类可读的价格变化记录
- 🗂️ **月度归档**: 自动归档历史变化记录，保持文件结构清晰

## 📂 项目结构

```
├── disney.py                           # 主爬虫脚本
├── disney_rate_converter.py            # 汇率转换器
├── disney_price_change_detector.py     # 价格变化检测器
├── disney_changelog_archiver.py        # CHANGELOG归档器
├── requirements.txt                     # Python依赖
├── .env.example                         # 环境变量示例
├── .gitignore                           # Git忽略文件
├── CHANGELOG.md                         # 价格变化记录
├── archive/                             # 历史数据归档目录
│   ├── 2025/                          # 2025年数据
│   └── ...
├── changelog_archive/                   # CHANGELOG历史归档
│   ├── disney_changelog_2025-07.md    # 2025年7月变化记录
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
# 完整流程：爬取数据 → 转换汇率 → 检测变化
python disney.py
python disney_rate_converter.py
python disney_price_change_detector.py

# 或者单独运行各个组件
python disney.py                           # 仅爬取数据
python disney_rate_converter.py           # 仅转换汇率
python disney_price_change_detector.py    # 仅检测价格变化
python disney_changelog_archiver.py       # 仅归档CHANGELOG (每月运行)
```

## 🤖 GitHub Actions 自动化

### 自动化工作流

项目包含一个GitHub Actions工作流：

#### **Weekly Disney Scraper** (每周自动运行)
- **时间**: 每周日UTC时间0点（北京时间周日上午8点）
- **功能**: 
  - 自动爬取Disney+价格数据
  - 转换汇率为人民币
  - 检测价格变化并更新CHANGELOG
  - 归档历史数据
  - 自动提交更新到GitHub
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

- **`disney_prices_all_countries.json`**: 完整的价格数据，包含所有国家和套餐的详细信息
- **`disney_prices_cny_sorted.json`**: 按人民币价格排序的简化数据，便于快速查看最便宜的套餐
- **`CHANGELOG.md`**: 记录所有价格变化，包括新增、删除和价格调整
- **`archive/YYYY/`**: 按年份归档的历史数据文件
- **`changelog_archive/`**: 按月份归档的价格变化记录

## 📊 CHANGELOG功能

### 自动价格变化检测
- 每次运行后自动对比价格变化
- 检测新增套餐、删除套餐和价格调整
- 生成人类可读的变化记录

### 变化记录格式
```markdown
## 2025-01-15 - Disney+价格变化检测

### 📊 本次检测统计
- 新增: 2个套餐
- 删除: 1个套餐  
- 价格变化: 3个套餐

### ➕ 新增套餐
**🇺🇸 美国 - Disney+ Standard**
- 价格: $12.99/月 (约 ¥93.45)

### ❌ 删除的套餐
**🇬🇧 英国 - Disney+ Basic**
- 原价格: £6.99/月 (约 ¥63.21)

### 💰 价格变化
**🇨🇦 加拿大 - Disney+ Premium**
- 原价格: CAD $13.99/月 (约 ¥73.42) 
- 新价格: CAD $14.99/月 (约 ¥78.67)
- 变化: +CAD $1.00 (+¥5.25, +7.14%)
```

### 月度归档
- 每月自动归档当月的价格变化记录
- 保持主CHANGELOG文件的清洁
- 归档文件命名格式：`disney_changelog_YYYY-MM.md`

## ⚙️ 技术特性

- **异步爬虫**: 使用Playwright进行高效的并发爬取
- **GitHub Actions支持**: 完全支持Playwright在云端运行
- **汇率精度**: 使用Decimal确保价格计算精度
- **智能变化检测**: 基于国家-套餐组合的精确价格对比
- **自动化归档**: 智能的历史数据和变化记录管理
- **GitHub Integration**: 与GitHub Actions无缝集成，支持自动化工作流

## 📈 监控和报告

### 价格趋势追踪
- 完整的历史价格数据保存在`archive/`目录
- 价格变化趋势记录在CHANGELOG中
- 支持按时间段查看价格变化情况

### 自动化报告
- 每次检测到价格变化时自动生成报告
- GitHub Actions运行日志提供详细的执行信息
- 支持在GitHub界面查看所有历史运行记录

## 📄 许可证

本项目仅用于学习和研究目的。
