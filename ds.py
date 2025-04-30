import re
import asyncio
from typing import Any
from bs4 import BeautifulSoup
import requests
from playwright.async_api import async_playwright


def extract_price(html: str) -> list[dict[str, Any]]:
    """
    从 HowTo_Details__c 字段的 HTML 中解析出 plan/price 列表
    """
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    if not table:
        return []
    plans = []
    for row in table.find_all('tr')[1:]:
        cols = row.find_all('td')
        if len(cols) != 3:
            continue
        plan = cols[0].get_text(strip=True)
        # 提取价格文本，并规范空格
        price = ' '.join(cols[2].get_text(separator=' ', strip=True).split())
        plans.append({'plan': plan, 'price': price})
    return plans


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


if __name__ == '__main__':
    all_prices = asyncio.run(main())
    import json
    with open('disneyplus_prices.json', 'w', encoding='utf-8') as f:
        json.dump(all_prices, f, ensure_ascii=False, indent=2)
    print("已写入 disneyplus_prices.json")
