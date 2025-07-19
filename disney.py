import re
import asyncio
from typing import Any
from bs4 import BeautifulSoup
import requests
from playwright.async_api import async_playwright

def extract_price(html: str) -> list[dict[str, Any]]:
    soup = BeautifulSoup(html, 'html.parser')
    all_tables = soup.find_all('table') # 查找所有表格
    all_plans = []

    if not all_tables:
        return []

    for table in all_tables: # 遍历每个表格
        # 在这里可以添加一些判断，检查这个 table 是否是需要的价格表
        # 例如： if "Price" not in str(table.find('tr')): continue

        plans_in_table = []
        try: # 增加错误处理，防止某个表格结构不符合预期导致整个函数失败
            for row in table.find_all('tr')[1:]: # 对当前表格应用解析逻辑
                cols = row.find_all('td')
                # 可能需要根据不同表格调整这里的列数判断和索引
                if len(cols) >= 3: # 或者更灵活的判断
                    plan = cols[0].get_text(strip=True)
                    # 价格列的索引也可能变化
                    price = ' '.join(cols[2].get_text(separator=' ', strip=True).split())
                    # 避免添加空的 plan 或 price
                    if plan and price:
                         plans_in_table.append({'plan': plan, 'price': price})
                # 可以考虑添加 elif len(cols) == X: 来处理其他结构的表格
        except Exception as e:
             print(f"解析某个表格时出错: {e}") # 打印错误信息，继续处理下一个表格

        all_plans.extend(plans_in_table) # 将当前表格解析出的套餐加入总列表

    return all_plans


def get_request_json(article_id: str, selected_meta: str, country: str) -> dict:
    return {
        "namespace": "",
        "classname": "@udd/01p5f00000ebl3g",
        "method": "loadArticle",
        "isContinuation": False,
        "params": {
            "articleId": article_id,
            "brand": "Disney",
            "country": country,
            "selectedMeta": selected_meta,
            "isPreview": False
        },
        "cacheable": False
    }


def get_price_json(article_id: str, selected_meta: str, country: str, localeCode: str) -> dict:
    url = f'https://help.disneyplus.com/{localeCode}/webruntime/api/apex/execute'
    resp = requests.post(url, json=get_request_json(article_id, selected_meta, country))
    resp.raise_for_status()
    return resp.json()


def get_country_language_localization() -> dict[str, Any]:
    # 默认使用德语接口获取，但后续会优先选取 en-* locale
    url = (
        'https://help.disneyplus.com/de/webruntime/api/apex/execute'
        '?cacheable=true&classname=%40udd%2F01p5f00000e1rTi'
        '&isContinuation=false&method=getCountryLanguageLocalization'
        '&namespace=&params=%7B%22brand%22%3A%22Disney%22%2C%22selectedLanguage%22%3A%22de%22%7D'
        '&language=de&asGuest=true&htmlEncode=false'
    )
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()['returnValue']


async def fetch_record_id(browser, locale_code: str) -> str:
    page = await browser.new_page()
    try:
        await page.goto(
            f'https://help.disneyplus.com/{locale_code}/article/disneyplus-price',
            wait_until='domcontentloaded'
        )
        html = await page.content()
        matches = re.findall(r'\{"recordId":"(.*?)"\}', html)
        if not matches:
            raise ValueError(f"No recordId found for locale {locale_code}")
        return matches[0]
    finally:
        await page.close()


async def main():
    loc_map = get_country_language_localization()
    results: dict[str, Any] = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for country_code, info in loc_map.items():
            # 所有可用语言选项
            lan_entries = info.get('lanInfo', [])
            # 优先选择以 en- 开头的 English locale
            en_entries = [l for l in lan_entries if l.get('localeCode', '').startswith('en-')]
            if en_entries:
                lan = en_entries[0]
            else:
                lan = lan_entries[0]

            locale_code = lan['localeCode']
            master_label = lan['masterLabel']
            try:
                # 获取 recordId
                record_id = await fetch_record_id(browser, locale_code)
                # 请求文章 JSON
                price_json = get_price_json(record_id, master_label, country_code, locale_code)

                # 提取 HTML 片段和 LastPublishedDate
                html_fragment = price_json['returnValue']['HowTo_Details__c']
                last_published_date = price_json['returnValue'].get('LastPublishedDate')

                # 解析套餐信息
                plans = extract_price(html_fragment)
                # 将 LastPublishedDate 加入每个套餐字典中
                for plan in plans:
                    plan['last_published_date'] = last_published_date

                results[country_code] = plans
                print(f"[{country_code}] 使用 {locale_code} 抓取到 {len(plans)} 个套餐，发布日期: {last_published_date}")
            except Exception as e:
                print(f"[{country_code}] 失败：{e}")

        await browser.close()

    return results


def extract_year_from_timestamp(timestamp: str) -> str:
    """从时间戳中提取年份"""
    try:
        # 时间戳格式: YYYYMMDD_HHMMSS
        if len(timestamp) >= 4:
            return timestamp[:4]
        else:
            # 如果解析失败，返回当前年份
            return time.strftime('%Y')
    except:
        return time.strftime('%Y')

def create_archive_directory_structure(archive_dir: str, timestamp: str) -> str:
    """根据时间戳创建按年份组织的归档目录结构"""
    year = extract_year_from_timestamp(timestamp)
    year_dir = os.path.join(archive_dir, year)
    if not os.path.exists(year_dir):
        os.makedirs(year_dir)
        print(f"📁 创建年份目录: {year_dir}")
    return year_dir

def migrate_existing_archive_files(archive_dir: str):
    """将现有的归档文件迁移到按年份组织的目录结构中"""
    if not os.path.exists(archive_dir):
        return
    
    migrated_count = 0
    
    # 查找根目录下的归档文件
    for filename in os.listdir(archive_dir):
        if filename.startswith('disneyplus_prices_') and filename.endswith('.json'):
            file_path = os.path.join(archive_dir, filename)
            
            # 确保是文件而不是目录
            if os.path.isfile(file_path):
                # 从文件名提取时间戳
                try:
                    # 文件名格式: disneyplus_prices_YYYYMMDD_HHMMSS.json
                    timestamp_part = filename.replace('disneyplus_prices_', '').replace('.json', '')
                    year = extract_year_from_timestamp(timestamp_part)
                    
                    # 创建年份目录
                    year_dir = create_archive_directory_structure(archive_dir, timestamp_part)
                    
                    # 移动文件
                    new_path = os.path.join(year_dir, filename)
                    if not os.path.exists(new_path):  # 避免重复移动
                        shutil.move(file_path, new_path)
                        print(f"📦 迁移文件: {filename} → {year}/")
                        migrated_count += 1
                except Exception as e:
                    print(f"⚠️  迁移文件失败 {filename}: {e}")
    
    if migrated_count > 0:
        print(f"✅ 成功迁移 {migrated_count} 个归档文件到年份目录")
    else:
        print("📂 没有需要迁移的归档文件")

def get_archive_statistics(archive_dir: str) -> dict:
    """获取归档文件统计信息"""
    if not os.path.exists(archive_dir):
        return {"total_files": 0, "years": {}}
    
    stats = {"total_files": 0, "years": {}}
    
    # 遍历所有年份目录
    for item in os.listdir(archive_dir):
        item_path = os.path.join(archive_dir, item)
        if os.path.isdir(item_path) and item.isdigit() and len(item) == 4:
            year = item
            year_files = []
            
            # 统计该年份的文件
            for filename in os.listdir(item_path):
                if filename.startswith('disneyplus_prices_') and filename.endswith('.json'):
                    filepath = os.path.join(item_path, filename)
                    mtime = os.path.getmtime(filepath)
                    year_files.append((filepath, mtime, filename))
            
            # 按时间排序
            year_files.sort(key=lambda x: x[1], reverse=True)
            stats["years"][year] = {
                "count": len(year_files),
                "files": year_files
            }
            stats["total_files"] += len(year_files)
    
    return stats


import json
import time
import os
import shutil

def extract_year_from_timestamp(timestamp: str) -> str:
    """从时间戳中提取年份"""
    try:
        # 时间戳格式: YYYYMMDD_HHMMSS
        if len(timestamp) >= 4:
            return timestamp[:4]
        else:
            # 如果解析失败，返回当前年份
            return time.strftime('%Y')
    except:
        return time.strftime('%Y')

def create_archive_directory_structure(archive_dir: str, timestamp: str) -> str:
    """根据时间戳创建按年份组织的归档目录结构"""
    year = extract_year_from_timestamp(timestamp)
    year_dir = os.path.join(archive_dir, year)
    if not os.path.exists(year_dir):
        os.makedirs(year_dir)
        print(f"📁 创建年份目录: {year_dir}")
    return year_dir

def migrate_existing_archive_files(archive_dir: str):
    """将现有的归档文件迁移到按年份组织的目录结构中"""
    if not os.path.exists(archive_dir):
        return
    
    migrated_count = 0
    
    # 查找根目录下的归档文件
    for filename in os.listdir(archive_dir):
        if filename.startswith('disneyplus_prices_') and filename.endswith('.json'):
            file_path = os.path.join(archive_dir, filename)
            
            # 确保是文件而不是目录
            if os.path.isfile(file_path):
                # 从文件名提取时间戳
                try:
                    # 文件名格式: disneyplus_prices_YYYYMMDD_HHMMSS.json
                    timestamp_part = filename.replace('disneyplus_prices_', '').replace('.json', '')
                    year = extract_year_from_timestamp(timestamp_part)
                    
                    # 创建年份目录
                    year_dir = create_archive_directory_structure(archive_dir, timestamp_part)
                    
                    # 移动文件
                    new_path = os.path.join(year_dir, filename)
                    if not os.path.exists(new_path):  # 避免重复移动
                        shutil.move(file_path, new_path)
                        print(f"📦 迁移文件: {filename} → {year}/")
                        migrated_count += 1
                except Exception as e:
                    print(f"⚠️  迁移文件失败 {filename}: {e}")
    
    if migrated_count > 0:
        print(f"✅ 成功迁移 {migrated_count} 个归档文件到年份目录")
    else:
        print("📂 没有需要迁移的归档文件")

def get_archive_statistics(archive_dir: str) -> dict:
    """获取归档文件统计信息"""
    if not os.path.exists(archive_dir):
        return {"total_files": 0, "years": {}}
    
    stats = {"total_files": 0, "years": {}}
    
    # 遍历所有年份目录
    for item in os.listdir(archive_dir):
        item_path = os.path.join(archive_dir, item)
        if os.path.isdir(item_path) and item.isdigit() and len(item) == 4:
            year = item
            year_files = []
            
            # 统计该年份的文件
            for filename in os.listdir(item_path):
                if filename.startswith('disneyplus_prices_') and filename.endswith('.json'):
                    filepath = os.path.join(item_path, filename)
                    mtime = os.path.getmtime(filepath)
                    year_files.append((filepath, mtime, filename))
            
            # 按时间排序
            year_files.sort(key=lambda x: x[1], reverse=True)
            stats["years"][year] = {
                "count": len(year_files),
                "files": year_files
            }
            stats["total_files"] += len(year_files)
    
    return stats

if __name__ == '__main__':
    all_prices = asyncio.run(main())
    
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    output_file = f'disneyplus_prices_{timestamp}.json'
    output_file_latest = 'disneyplus_prices.json'
    
    # 确保归档目录结构存在
    archive_dir = 'archive'
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)
        
    # 检查并迁移现有的归档文件到年份目录
    migrate_existing_archive_files(archive_dir)
    
    # 根据时间戳创建年份子目录
    year_archive_dir = create_archive_directory_structure(archive_dir, timestamp)
    
    # 保存带时间戳的版本到对应年份归档目录
    archive_file = os.path.join(year_archive_dir, output_file)
    with open(archive_file, 'w', encoding='utf-8') as f:
        json.dump(all_prices, f, ensure_ascii=False, indent=2)
        
    # 保存最新版本（供转换器使用）
    with open(output_file_latest, 'w', encoding='utf-8') as f:
        json.dump(all_prices, f, ensure_ascii=False, indent=2)
        
    print(f"已写入 {output_file_latest} 和 {archive_file}")
