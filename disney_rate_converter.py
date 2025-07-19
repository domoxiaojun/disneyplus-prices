import json
import requests
import re
import time
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

import os

# --- Configuration ---

# 尝试加载 .env 文件（如果存在）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv 不是必需的依赖
    pass

# 从环境变量获取API密钥，如果没有则使用默认值（仅用于本地测试）
API_KEYS = []

# 读取API密钥
api_key = os.getenv('API_KEY')
if api_key:
    API_KEYS.append(api_key)

# 如果没有环境变量，使用默认密钥（仅用于本地开发测试）
if not API_KEYS:
    print("错误：未找到API密钥！")
    print("请设置环境变量 API_KEY 或在 .env 文件中配置")
    print("获取免费API密钥: https://openexchangerates.org/")
    exit(1)
API_URL_TEMPLATE = "https://openexchangerates.org/api/latest.json?app_id={}"
INPUT_JSON_PATH = 'disneyplus_prices.json' # Input JSON file path
OUTPUT_JSON_PATH = 'disneyplus_prices_processed.json' # New output file path

# Static Country Information (Using the detailed map provided previously)
COUNTRY_INFO = {
    "ME": {"name_en": "Montenegro","name_cn": "黑山","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "GD": {"name_en": "Grenada","name_cn": "格林纳达","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "LC": {"name_en": "Saint Lucia","name_cn": "圣卢西亚","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "CO": {"name_en": "Colombia","name_cn": "哥伦比亚","currency": "COP","symbol": "COP","decimal": ",","thousand": "."},
    "VC": {"name_en": "Saint Vincent and the Grenadines","name_cn": "圣文森特和格林纳丁斯","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "NO": {"name_en": "Norway","name_cn": "挪威","currency": "NOK","symbol": "NOK","decimal": ".","thousand": ","},
    "IS": {"name_en": "Iceland","name_cn": "冰岛","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "AD": {"name_en": "Andorra","name_cn": "安道尔","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "NI": {"name_en": "Nicaragua","name_cn": "尼加拉瓜","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "SK": {"name_en": "Slovakia","name_cn": "斯洛伐克","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "LV": {"name_en": "Latvia","name_cn": "拉脱维亚","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "RS": {"name_en": "Serbia","name_cn": "塞尔维亚","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "PY": {"name_en": "Paraguay","name_cn": "巴拉圭","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "JM": {"name_en": "Jamaica","name_cn": "牙买加","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "FI": {"name_en": "Finland","name_cn": "芬兰","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "EE": {"name_en": "Estonia","name_cn": "爱沙尼亚","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "CR": {"name_en": "Costa Rica","name_cn": "哥斯达黎加","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "TT": {"name_en": "Trinidad and Tobago","name_cn": "特立尼达和多巴哥","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "BA": {"name_en": "Bosnia and Herzegovina","name_cn": "波斯尼亚和黑塞哥维那","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "HU": {"name_en": "Hungary","name_cn": "匈牙利","currency": "HUF","symbol": "HUF","decimal": ".","thousand": ","},
    "MK": {"name_en": "North Macedonia","name_cn": "北马其顿","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "CL": {"name_en": "Chile","name_cn": "智利","currency": "CLP","symbol": "CLP","decimal": ",","thousand": "."},
    "KR": {"name_en": "South Korea","name_cn": "韩国","currency": "KRW","symbol": "KRW","decimal": ".","thousand": ","},
    "SR": {"name_en": "Suriname","name_cn": "苏里南","currency": "USD","symbol": "$","decimal": ",","thousand": "."},
    "UY": {"name_en": "Uruguay","name_cn": "乌拉圭","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "US": {"name_en": "United States","name_cn": "美国","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "BO": {"name_en": "Bolivia","name_cn": "玻利维亚","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "CA": {"name_en": "Canada","name_cn": "加拿大","currency": "CAD","symbol": "CA$","decimal": ".","thousand": ","},
    "UK": {"name_en": "United Kingdom","name_cn": "英国","currency": "GBP","symbol": "£","decimal": ".","thousand": ","},
    "GI": {"name_en": "Gibraltar","name_cn": "直布罗陀","currency": "GBP","symbol": "£","decimal": ".","thousand": ","},
    "SG": {"name_en": "Singapore","name_cn": "新加坡","currency": "SGD","symbol": "S$","decimal": ".","thousand": ","},
    "TR": {"name_en": "Turkey","name_cn": "土耳其","currency": "TRY","symbol": "TL","decimal": ".","thousand": ","},
    "BZ": {"name_en": "Belize","name_cn": "伯利兹","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "AG": {"name_en": "Antigua and Barbuda","name_cn": "安提瓜和巴布达","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "MX": {"name_en": "Mexico","name_cn": "墨西哥","currency": "MXN","symbol": "MX$","decimal": ".","thousand": ","},
    "FR": {"name_en": "France","name_cn": "法国","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "LU": {"name_en": "Luxembourg","name_cn": "卢森堡","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "AU": {"name_en": "Australia","name_cn": "澳大利亚","currency": "AUD","symbol": "A$","decimal": ".","thousand": ","},
    "BS": {"name_en": "Bahamas","name_cn": "巴哈马","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "SI": {"name_en": "Slovenia","name_cn": "斯洛文尼亚","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "LI": {"name_en": "Liechtenstein","name_cn": "列支敦士登","currency": "CHF","symbol": "CHF","decimal": ".","thousand": ","},
    "AR": {"name_en": "Argentina","name_cn": "阿根廷","currency": "ARS","symbol": "ARS","decimal": ",","thousand": "."},
    "PL": {"name_en": "Poland","name_cn": "波兰","currency": "PLN","symbol": "zł","decimal": ".","thousand": ","},
    "EC": {"name_en": "Ecuador","name_cn": "厄瓜多尔","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "VE": {"name_en": "Venezuela","name_cn": "委内瑞拉","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "BG": {"name_en": "Bulgaria","name_cn": "保加利亚","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "BE": {"name_en": "Belgium","name_cn": "比利时","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "BR": {"name_en": "Brazil","name_cn": "巴西","currency": "BRL","symbol": "R$","decimal": ",","thousand": "."},
    "AT": {"name_en": "Austria","name_cn": "奥地利","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "PE": {"name_en": "Peru","name_cn": "秘鲁","currency": "PEN","symbol": "PEN","decimal": ".","thousand": ","},
    "GR": {"name_en": "Greece","name_cn": "希腊","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "RO": {"name_en": "Romania","name_cn": "罗马尼亚","currency": "RON","symbol": "Lei","decimal": ".","thousand": ","},
    "PA": {"name_en": "Panama","name_cn": "巴拿马","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "MT": {"name_en": "Malta","name_cn": "马耳他","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "IE": {"name_en": "Ireland","name_cn": "爱尔兰","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "NL": {"name_en": "Netherlands","name_cn": "荷兰","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "GT": {"name_en": "Guatemala","name_cn": "危地马拉","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "ES": {"name_en": "Spain","name_cn": "西班牙","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "CZ": {"name_en": "Czech Republic","name_cn": "捷克","currency": "CZK","symbol": "CZK","decimal": ".","thousand": ","},
    "PT": {"name_en": "Portugal","name_cn": "葡萄牙","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "AL": {"name_en": "Albania","name_cn": "阿尔巴尼亚","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "DO": {"name_en": "Dominican Republic","name_cn": "多米尼加共和国","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "LT": {"name_en": "Lithuania","name_cn": "立陶宛","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "DE": {"name_en": "Germany","name_cn": "德国","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "DK": {"name_en": "Denmark","name_cn": "丹麦","currency": "DKK","symbol": "kr","decimal": ".","thousand": ","},
    "SE": {"name_en": "Sweden","name_cn": "瑞典","currency": "SEK","symbol": "SEK","decimal": ".","thousand": ","},
    "BB": {"name_en": "Barbados","name_cn": "巴巴多斯","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "NZ": {"name_en": "New Zealand","name_cn": "新西兰","currency": "NZD","symbol": "NZ$","decimal": ".","thousand": ","},
    "KN": {"name_en": "Saint Kitts and Nevis","name_cn": "圣基茨和尼维斯","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "DM": {"name_en": "Dominica","name_cn": "多米尼克","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "MC": {"name_en": "Monaco","name_cn": "摩纳哥","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "HN": {"name_en": "Honduras","name_cn": "洪都拉斯","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "IT": {"name_en": "Italy","name_cn": "意大利","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "CH": {"name_en": "Switzerland","name_cn": "瑞士","currency": "CHF","symbol": "CHF","decimal": ".","thousand": ","},
    "HR": {"name_en": "Croatia","name_cn": "克罗地亚","currency": "EUR","symbol": "€","decimal": ".","thousand": ","},
    "GY": {"name_en": "Guyana","name_cn": "圭亚那","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "TW": {"name_en": "Taiwan","name_cn": "中国台湾","currency": "TWD","symbol": "NTD","decimal": ".","thousand": ","},
    "HT": {"name_en": "Haiti","name_cn": "海地","currency": "USD","symbol": "$","decimal": ",","thousand": "."},
    "SV": {"name_en": "El Salvador","name_cn": "萨尔瓦多","currency": "USD","symbol": "$","decimal": ".","thousand": ","},
    "JP": {"name_en": "Japan","name_cn": "日本","currency": "JPY","symbol": "¥","decimal": ".","thousand": ","},
    "HK": {"name_en": "Hong Kong","name_cn": "中国香港","currency": "HKD","symbol": "HK$","decimal": ".","thousand": ","}
}


# Plan Name Standardization Mappings
PLAN_NAME_MAP = {
    # Spanish
    "disney+ estándar con anuncios": "Disney+ Standard with Ads", "disney+ estándar": "Disney+ Standard",
    "disney+ premium": "Disney+ Premium", "miembro extra": "Extra Member",
    # Portuguese
    "disney+ padrão com anúncios": "Disney+ Standard with Ads", "disney+ padrão": "Disney+ Standard",
    "membro extra": "Extra Member",
    # French
    "disney+ standard avec pub": "Disney+ Standard with Ads", "abonné supplémentaire": "Extra Member",
     # Turkish
    "disney+ with ads": "Disney+ Standard with Ads", "disney+ without ads": "Disney+ Premium",
    # Generic
    "disney+ basic": "Disney+ Basic"
}

# Currency Symbols/Codes to Standard API Codes (e.g., TWD)
# Ensure specific symbols like HK$, S$ are present and mapped correctly
CURRENCY_SYMBOLS_TO_CODES = {
    '€': 'EUR', '£': 'GBP', 'usd': 'USD', 'cad': 'CAD', 'ars': 'ARS', 'aud': 'AUD',
    'brl': 'BRL', 'clp': 'CLP', 'cop': 'COP', 'czk': 'CZK', 'dkk': 'DKK', 'hkd': 'HKD',
    'huf': 'HUF', 'jpy': 'JPY', 'mxn': 'MXN', 'nok': 'NOK', 'nzd': 'NZD', 'pen': 'PEN',
    'pln': 'PLN', 'ron': 'RON', 'sek': 'SEK', 'sgd': 'SGD', 'chf': 'CHF', 'twd': 'TWD',
    'try': 'TRY', 'krw': 'KRW',
    'lei': 'RON', 'kr': 'DKK', 'tl': 'TRY', 'zł': 'PLN', 'r$': 'BRL', 'ca$': 'CAD',
    'a$': 'AUD', 'hk$': 'HKD', 's$': 'SGD', 'mx$': 'MXN', 'nz$': 'NZD',
    'ntd': 'TWD', # Special mapping for Taiwan Dollar
    '¥': 'JPY',
    '$': 'USD'    # Keep generic $ mapping, but logic will prioritize specifics
    # Add more mappings if needed, longer/specific keys checked first due to sorting
}


# --- Functions ---

def get_exchange_rates(api_keys, url_template):
    """Fetches exchange rates using a list of API keys."""
    # (Function remains the same as V4)
    rates = None
    for key in api_keys:
        url = url_template.format(key)
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            if 'rates' in data:
                print(f"成功使用 API 密钥 ...{key[-4:]} 获取汇率")
                rates = data['rates']
                if 'USD' not in rates: rates['USD'] = 1.0
                return rates
            else:
                print(f"API 密钥 ...{key[-4:]} 可能无效或受限: {data.get('description')}")
        except requests.exceptions.RequestException as e:
            print(f"使用密钥 ...{key[-4:]} 获取汇率时出错: {e}")
        except json.JSONDecodeError:
             print(f"使用密钥 ...{key[-4:]} 解码 JSON 响应时出错")
    print("无法使用所有提供的 API 密钥获取汇率。")
    return None

def standardize_plan_name(original_name):
    """Standardizes plan names to English using the PLAN_NAME_MAP."""
    # (Function remains the same as V4)
    name_lower = original_name.lower().strip()
    if name_lower in PLAN_NAME_MAP:
        return PLAN_NAME_MAP[name_lower]
    return ' '.join(original_name.strip().split()).title()


def clean_and_convert_price(raw_amount_str, country_formatting):
    """Cleans price string based on country formatting and converts to Decimal."""
    # (Function remains the same as V4)
    if not raw_amount_str: return None
    decimal_separator = country_formatting.get('decimal', '.')
    thousand_separator = country_formatting.get('thousand', ',')
    amount_str = re.sub(r'(?:[€£$¥]|(?:[A-Z]{2,3}\$?))\s*', '', raw_amount_str, flags=re.IGNORECASE).strip()
    amount_str = re.sub(r'\s*(?:[€£$¥]|(?:[A-Z]{2,3}\$?))', '', amount_str, flags=re.IGNORECASE).strip()
    if thousand_separator: amount_str = amount_str.replace(thousand_separator, '')
    if decimal_separator != '.': amount_str = amount_str.replace(decimal_separator, '.')
    if amount_str.count('.') > 1:
        parts = amount_str.split('.')
        amount_str = parts[0] + '.' + ''.join(parts[1:])
    try:
        if not amount_str: return None
        return Decimal(amount_str)
    except InvalidOperation:
         original_cleaned = re.sub(r'\s', '', raw_amount_str)
         only_digits_and_thousand = all(c.isdigit() or c == thousand_separator for c in original_cleaned if not c.isalpha() and c not in ['€','£','$','¥'])
         if only_digits_and_thousand and thousand_separator:
             try:
                  int_str = original_cleaned.replace(thousand_separator, '')
                  if int_str: return Decimal(int_str)
             except InvalidOperation: pass
         print(f"警告：无法将清理后的字符串 '{amount_str}' (来自 '{raw_amount_str}') 转换为 Decimal。")
         return None
    except Exception as e:
        print(f"警告：转换价格时发生意外错误 '{amount_str}' (来自 '{raw_amount_str}'). 错误: {e}")
        return None


def extract_prices_and_currency(price_text, country_details):
    """Extracts monthly/annual prices and determines currency, using country formatting and refined symbol logic."""
    prices = {}
    default_currency_code = country_details.get('currency')
    default_symbol = country_details.get('symbol')
    country_formatting = {
        'decimal': country_details.get('decimal', '.'),
        'thousand': country_details.get('thousand', ',')
    }

    # --- Refined Currency Detection ---
    detected_code = default_currency_code # Start with default

    # 1. Check for explicit 3-letter codes first
    code_match = re.search(r'\b([A-Z]{3})\b', price_text)
    if code_match:
        explicit_code = code_match.group(1)
        # Check if this code is known in our map or default
        if explicit_code in CURRENCY_SYMBOLS_TO_CODES.values() or explicit_code == default_currency_code:
             if explicit_code != detected_code:
                  print(f"  注意：检测到明确代码 '{explicit_code}'，与默认 '{detected_code}' 不同。使用 '{explicit_code}'。")
                  detected_code = explicit_code
        #else: # Optional: Warn about unknown 3-letter codes?

    # 2. If no overriding code found yet, check for specific symbols (longest first)
    if detected_code == default_currency_code:
        # Sort symbols by length desc to match longer/specific ones first (e.g., 'HK$' before '$')
        sorted_symbols = sorted(CURRENCY_SYMBOLS_TO_CODES.keys(), key=len, reverse=True)
        found_symbol_code = None
        specific_symbol_matched = False

        for symbol_key in sorted_symbols:
             # Use word boundaries for letter-based symbols/codes
             pattern = r'\b' + re.escape(symbol_key) + r'\b' if symbol_key.isalpha() else re.escape(symbol_key)
             # Use case-insensitivity for matching
             if re.search(pattern, price_text, re.IGNORECASE):
                 potential_code = CURRENCY_SYMBOLS_TO_CODES[symbol_key.lower()]

                 # *** Prioritization Logic ***
                 # A. If this symbol matches the default country's specific symbol, strongly prefer it.
                 if default_symbol and symbol_key.lower() == default_symbol.lower():
                      found_symbol_code = potential_code
                      specific_symbol_matched = True
                      print(f"  调试：匹配到默认符号 '{symbol_key}' -> '{potential_code}'。")
                      break # Found the most specific match for this country

                 # B. If it's not the default symbol, but is a specific symbol (not generic '$'), store it.
                 elif symbol_key != '$':
                      if found_symbol_code is None: # Store the first specific non-'$' match
                           found_symbol_code = potential_code
                           print(f"  调试：匹配到特定符号 '{symbol_key}' -> '{potential_code}'。")
                           # Don't break yet, maybe a longer specific one exists

                 # C. If it's the generic '$'
                 elif symbol_key == '$':
                      # Only consider '$' if no other specific symbol was found yet
                      if found_symbol_code is None:
                            # If the default currency is already USD/CAD/AUD etc., '$' confirms it.
                           if default_currency_code in ['USD', 'CAD', 'AUD', 'NZD', 'MXN', 'SGD', 'HKD']: # Currencies that might use '$' or variant
                                found_symbol_code = potential_code # Map '$' to USD by default here
                                print(f"  调试：匹配到通用 '$'，默认货币 ({default_currency_code}) 使用 '$'，映射到 '{potential_code}'。")
                           else:
                                # Default currency DOES NOT use '$'. Finding '$' is ambiguous.
                                # Do not override the default unless explicit 'USD' text is found later.
                                print(f"  调试：匹配到通用 '$'，但默认货币 ({default_currency_code}) 不使用。暂时忽略。")
                                pass # Stick with the default_currency_code for now.

        # Use the found code if it's specific or confirms the default
        if found_symbol_code and (specific_symbol_matched or found_symbol_code != 'USD' or default_currency_code in ['USD', 'CAD', 'AUD', 'NZD', 'MXN', 'SGD', 'HKD']):
             if found_symbol_code != detected_code:
                  print(f"  注意：检测到符号代码 '{found_symbol_code}'，与默认 '{detected_code}' 不同。使用 '{found_symbol_code}'。")
                  detected_code = found_symbol_code

    # --- Final Currency Code ---
    final_currency_code = detected_code
    if not final_currency_code:
        print(f"警告：国家/地区 {country_details.get('name_en')} 最终无法确定货币代码。")
        return {}, None

    # --- Price Extraction (remains the same as V4) ---
    patterns = {
        'monthly': r'(?:monthly|mensual|mensuel|maandelijks|monatlich|month|/month)\s*:?\s*([€£$¥]?\s?[\d.,]+(?:\s?[A-Z]{3}\$?)?)',
        'annual':  r'(?:annual|anual|annuel|jaarlijks|jährlich|year|/year)\s*:?\s*([€£$¥]?\s?[\d.,]+(?:\s?[A-Z]{3}\$?)?)'
    }
    cleaned_text = price_text.replace('\n', ' ').strip()
    for period, pattern in patterns.items():
        matches = re.findall(pattern, cleaned_text, re.IGNORECASE)
        if matches:
            raw_amount = matches[-1].strip()
            decimal_price = clean_and_convert_price(raw_amount, country_formatting)
            if decimal_price is not None: prices[period] = decimal_price

    # Fallback for formats like "HK$81/month or HK$810/year"
    if not prices or len(prices) < 2:
         simple_matches = re.findall(r'([A-Z]{2,3}\$?|[€£$¥])\s?([\d.,]+)\s?/(month|year)', cleaned_text, re.IGNORECASE)
         if len(simple_matches) >= 1 :
             for curr_sym, amount_str, period_str in simple_matches:
                 period_key = 'monthly' if 'month' in period_str.lower() else 'annual'
                 if period_key not in prices:
                     decimal_price = clean_and_convert_price(amount_str, country_formatting)
                     if decimal_price is not None: prices[period_key] = decimal_price

    # Fallback for single price entries
    if not prices:
        single_price_match = re.search(r'(?:[A-Z]{2,3}\$?|[€£$¥])\s*([\d.,]+)|([\d.,]+)\s*(?:[A-Z]{2,3}\$?|[€£$¥])', cleaned_text, re.IGNORECASE)
        raw_amount = None
        if single_price_match: raw_amount = single_price_match.group(1) or single_price_match.group(2)
        else:
             numeric_match = re.search(r'([\d.,]+)', cleaned_text)
             if numeric_match: raw_amount = numeric_match.group(1)
        if raw_amount:
            decimal_price = clean_and_convert_price(raw_amount, country_formatting)
            if decimal_price is not None: prices['monthly'] = decimal_price # Assume monthly

    return prices, final_currency_code


def convert_to_cny(amount, currency_code, rates):
    """Converts an amount from a given currency to CNY via USD."""
    # (Function remains the same as V4)
    if not isinstance(amount, Decimal): return None
    if not rates or not currency_code or currency_code not in rates or 'CNY' not in rates: return None
    try:
        cny_rate = Decimal(rates['CNY'])
        if currency_code == 'USD': cny_amount = amount * cny_rate
        else:
            original_rate = Decimal(rates[currency_code])
            if original_rate == 0:
                 print(f"警告：{currency_code} 的汇率为零。")
                 return None
            usd_amount = amount / original_rate
            cny_amount = usd_amount * cny_rate
        return cny_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception as e:
        print(f"转换 {amount} {currency_code} 时出错: {e}")
        return None

def sort_by_plan_cny(processed_data, original_data, plan_keyword="Premium"):
    """按指定套餐的CNY价格从低到高排序国家，并在JSON前面添加最便宜的10个"""
    countries_with_plan_price = []
    countries_without_plan_price = []
    
    for country_code, country_info in processed_data.items():
        target_plan = None
        
        # 查找包含关键字的套餐
        for plan in country_info.get('plans', []):
            if plan_keyword in plan.get('plan_name', ''):
                target_plan = plan
                break
        
        if target_plan and target_plan.get('monthly_price_cny') is not None:
            price_cny_str = target_plan['monthly_price_cny'].replace('CNY ', '')
            try:
                price_cny = float(price_cny_str)
                countries_with_plan_price.append((country_code, price_cny, country_info, target_plan))
            except (ValueError, TypeError):
                countries_without_plan_price.append((country_code, country_info))
        else:
            countries_without_plan_price.append((country_code, country_info))
            
    # 按CNY价格排序
    countries_with_plan_price.sort(key=lambda x: x[1])
    
    # 创建排序后的结果
    sorted_data = {}
    
    # 添加Top 10摘要
    top_10_cheapest = []
    for i, (country_code, price_cny, country_info, plan) in enumerate(countries_with_plan_price[:10]):
        country_name_cn = COUNTRY_INFO.get(country_code, {}).get('name_cn', country_info.get('name_cn', country_code))
        
        top_10_cheapest.append({
            'rank': i + 1,
            'country_code': country_code,
            'country_name_cn': country_name_cn,
            'plan_name': plan.get('plan_name'),
            'original_price': plan.get('monthly_price_original'),
            'currency': plan.get('currency_code'),
            'price_cny': price_cny
        })
        
    sorted_data[f'_top_10_cheapest_{plan_keyword.lower()}_plans'] = {
        'description': f'最便宜的10个Disney+ {plan_keyword}套餐 (按月付)',
        'updated_at': time.strftime('%Y-%m-%d'),
        'data': top_10_cheapest
    }
    
    # 添加所有国家的数据
    for country_code, price_cny, country_info, plan in countries_with_plan_price:
        sorted_data[country_code] = country_info
        
    for country_code, country_info in countries_without_plan_price:
        sorted_data[country_code] = country_info
        
    return sorted_data

# --- Main Script ---

# 1. Fetch Exchange Rates
print("正在获取汇率...")
exchange_rates = get_exchange_rates(API_KEYS, API_URL_TEMPLATE)
if not exchange_rates: exit()
else:
    print(f"基础货币: USD。找到 {len(exchange_rates)} 个汇率。")
    if 'CNY' in exchange_rates: print(f"USD 到 CNY 汇率: {exchange_rates['CNY']:.4f}")
    else: print("警告：获取的数据中未找到 CNY 汇率！")

# 2. Load Input JSON
print(f"正在从 {INPUT_JSON_PATH} 加载数据...")
try:
    with open(INPUT_JSON_PATH, 'r', encoding='utf-8') as f: data = json.load(f)
    print("数据加载成功。")
except FileNotFoundError: print(f"错误：输入文件未找到于 {INPUT_JSON_PATH}"); exit()
except json.JSONDecodeError as e: print(f"错误：无法解码来自 {INPUT_JSON_PATH} 的 JSON: {e}"); exit()
except Exception as e: print(f"加载文件时发生意外错误: {e}"); exit()

# 3. Process Data
print("正在处理订阅数据...")
processed_data = {}

for country_iso, plans in data.items():
    if country_iso not in COUNTRY_INFO:
        print(f"警告：跳过国家/地区 {country_iso} - 在 COUNTRY_INFO 中未找到信息。")
        continue

    country_details = COUNTRY_INFO[country_iso]
    country_name_cn = country_details.get('name_cn', country_details.get('name_en', country_iso))
    processed_plans_list = []
    print(f"正在处理 {country_name_cn} ({country_iso})...")

    for plan_info in plans:
        original_plan_name = plan_info.get('plan', 'Unknown Plan')
        price_text = plan_info.get('price', '')
        if not price_text:
            print(f"  跳过计划 '{original_plan_name}' - 无价格文本。")
            continue

        standard_plan_name = standardize_plan_name(original_plan_name)
        extracted_prices, final_currency_code = extract_prices_and_currency(price_text, country_details)

        plan_output = {
            "plan_name": standard_plan_name,
            "currency_code": final_currency_code if final_currency_code else "N/A",
            "monthly_price_original": None, "monthly_price_cny": None,
            "annual_price_original": None, "annual_price_cny": None,
        }

        if not final_currency_code: print(f"  警告：计划 '{standard_plan_name}' 无法检测到货币，无法进行转换。")
        else:
            if 'monthly' in extracted_prices and extracted_prices['monthly'] is not None:
                monthly_price = extracted_prices['monthly']
                plan_output["monthly_price_original"] = f"{final_currency_code} {monthly_price}"
                cny_equiv = convert_to_cny(monthly_price, final_currency_code, exchange_rates)
                if cny_equiv is not None: plan_output["monthly_price_cny"] = f"CNY {cny_equiv}"

            if 'annual' in extracted_prices and extracted_prices['annual'] is not None:
                annual_price = extracted_prices['annual']
                plan_output["annual_price_original"] = f"{final_currency_code} {annual_price}"
                cny_equiv = convert_to_cny(annual_price, final_currency_code, exchange_rates)
                if cny_equiv is not None: plan_output["annual_price_cny"] = f"CNY {cny_equiv}"

        processed_plans_list.append(plan_output)

    if processed_plans_list:
        processed_data[country_iso] = {"name_cn": country_name_cn, "plans": processed_plans_list}
    else: print(f"  未找到 {country_name_cn} ({country_iso}) 的可处理计划。")

# 4. Sort data and add Top 10
sorted_data = sort_by_plan_cny(processed_data, data, plan_keyword="Premium")

# 5. Output Processed Data
print(f"正在将处理后的数据保存到 {OUTPUT_JSON_PATH}...")
try:
    with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(sorted_data, f, ensure_ascii=False, indent=2)
    print("处理完成。输出已保存。")
except Exception as e: print(f"保存输出文件时出错: {e}")