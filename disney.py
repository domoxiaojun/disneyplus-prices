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


import json
import time
import os
import shutil

if __name__ == '__main__':
    all_prices = asyncio.run(main())
    
    output_file_latest = 'disneyplus_prices.json'
    
    # 保存最新版本（供转换器使用）
    with open(output_file_latest, 'w', encoding='utf-8') as f:
        json.dump(all_prices, f, ensure_ascii=False, indent=2)
        
    print(f"已写入 {output_file_latest}")
