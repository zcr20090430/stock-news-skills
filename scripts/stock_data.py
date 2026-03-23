#!/usr/bin/env python3
"""
股票数据获取脚本 - 支持多个数据源
数据源优先级: 新浪财经 > 腾讯财经 > 东方财富
"""
import requests
import json
import re
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, List


def get_stock_code(keyword: str) -> Optional[str]:
    """
    根据关键词获取股票代码
    """
    # 先尝试直接判断
    keyword_upper = keyword.upper()
    if keyword_upper.startswith(('SH', 'SZ', 'HK')):
        return keyword_upper
    
    # 常见股票名称映射
    stock_map = {
        # 美股
        'MU': 'USMU',
        '美光': 'USMU',
        '美光科技': 'USMU',
        'NVDA': 'USNVDA',
        '英伟达': 'USNVDA',
        'AAPL': 'USAAPL',
        '苹果': 'USAAPL',
        'TSLA': 'USTSLA',
        '特斯拉': 'USTSLA',
        'MSFT': 'USMSFT',
        '微软': 'USMSFT',
        'AMZN': 'USAMZN',
        '亚马逊': 'USAMZN',
        'GOOGL': 'USGOOGL',
        '谷歌': 'USGOOGL',
        'META': 'USMETA',
        'AMD': 'USAMD',
        'INTC': 'USINTC',
        '英特尔': 'USINTC',
        'QCOM': 'USQCOM',
        '高通': 'USQCOM',
        'TSM': 'USTSM',
        '台积电': 'USTSM',
        'BABA': 'USBABA',
        'PDD': 'USPDD',
        '拼多多': 'USPDD',
        'JD': 'USJD',
        '京东': 'USJD',
        'NIO': 'USNIO',
        '蔚来': 'USNIO',
        'XPEV': 'USXPEV',
        '小鹏': 'USXPEV',
        'LI': 'USLI',
        '理想': 'USLI',
        # 港股
        '泡泡玛特': 'HK09992',
        '茅台': 'SH600519',
        '贵州茅台': 'SH600519',
        '宁德时代': 'SZ300750',
        '宁德': 'SZ300750',
        '比亚迪': 'SZ002594',
        '腾讯': 'HK00700',
        '阿里': 'HK09988',
        '阿里巴巴': 'HK09988',
        '美团': 'HK03690',
        '招商银行': 'SH600036',
        '招行': 'SH600036',
        '平安': 'SH601318',
        '中国平安': 'SH601318',
        '工商银行': 'SH601398',
        '工行': 'SH601398',
        '建设银行': 'SH601939',
        '建行': 'SH601939',
        '中国中免': 'SH601888',
        '中免': 'SH601888',
        '隆基绿能': 'SH601012',
        '隆基': 'SH601012',
        '通威股份': 'SH600438',
        '通威': 'SH600438',
        '阳光电源': 'SZ300274',
        '长城汽车': 'SH601633',
        '长城': 'SH601633',
        '理想汽车': 'HK02015',
        '理想': 'HK02015',
        '蔚来': 'USNIO',
        '小鹏': 'USXPEV',
        '中芯国际': 'SH688981',
        '中芯': 'SH688981',
        '海康威视': 'SZ002415',
        '海康': 'SZ002415',
        '药明康德': 'SH603259',
        '药明': 'SH603259',
        '恒瑞医药': 'SH600276',
        '恒瑞': 'SH600276',
        '五粮液': 'SZ000858',
        '泸州老窖': 'SZ000568',
        '洋河股份': 'SZ002304',
        '洋河': 'SZ002304',
        '伊利股份': 'SH600887',
        '伊利': 'SH600887',
        '格力电器': 'SZ000651',
        '格力': 'SZ000651',
        '美的集团': 'SZ000333',
        '美的': 'SZ000333',
        '海尔智家': 'SH600690',
        '海尔': 'SH600690',
        '万科A': 'SZ000002',
        '万科': 'SZ000002',
        '保利发展': 'SH600048',
        '保利': 'SH600048',
    }
    
    if keyword in stock_map:
        return stock_map[keyword]
    
    # 尝试从东方财富搜索
    try:
        url = 'https://searchapi.eastmoney.com/bussiness/web/QuotationLabelSearch'
        params = {
            'keyword': keyword,
            'type': 'stock',
            'pi': 1,
            'ps': 5,
            'token': '0'
        }
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://quote.eastmoney.com/',
        }
        response = requests.get(url, headers=headers, params=params, timeout=5)
        data = response.json()
        
        if data and 'Data' in data and data['Data']:
            for item in data['Data']:
                code = item.get('Code', '')
                market_code = item.get('MktNum', '')
                if code:
                    # 判断市场
                    if market_code == '1' or code.startswith('6'):
                        return f'SH{code}'
                    elif market_code == '0' or code.startswith(('0', '3')):
                        return f'SZ{code}'
    except Exception as e:
        print(f"东方财富搜索失败: {e}", file=sys.stderr)
    
    # 尝试从新浪搜索
    try:
        url = 'https://suggest.sinajs.cn/suggest/type=11'
        params = {'key': keyword}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://finance.sina.com.cn/',
        }
        response = requests.get(url, headers=headers, params=params, timeout=5)
        response.encoding = 'gbk'
        text = response.text
        
        # 解析建议结果
        if text and 'var suggest_value="' in text:
            match = re.search(r'var suggest_value="([^"]+)"', text)
            if match:
                suggestions = match.group(1).split(';')
                for s in suggestions:
                    parts = s.split(',')
                    if len(parts) >= 4:
                        code = parts[3]
                        # 返回第一个结果
                        if code.startswith('6'):
                            return f'SH{code}'
                        elif code.startswith(('0', '3')):
                            return f'SZ{code}'
    except Exception as e:
        print(f"新浪搜索失败: {e}", file=sys.stderr)
    
    return None


def get_sina_kline(code: str, days: int = 30) -> List[Dict]:
    """
    从新浪财经获取K线数据
    code: 纯代码（不带交易所前缀），如 600519
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://finance.sina.com.cn/',
    }
    
    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days * 2)  # 多取一些，排除非交易日
    
    results = []
    
    try:
        # 新浪日K线接口
        url = f'https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData'
        params = {
            'symbol': code,
            'scale': '240',  # 日K
            'datalen': days + 20  # 多取一些数据用于计算指标
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            # 解析返回数据
            text = response.text
            # 格式: [{day:"2024-01-01",open:"100",high:"110",low:"95",close:"105",volume:"10000"}]
            
            # 尝试JSON解析
            try:
                data = json.loads(text)
                if isinstance(data, list):
                    for item in data[-days:]:
                        results.append({
                            'date': item.get('day', ''),
                            'open': float(item.get('open', 0)),
                            'high': float(item.get('high', 0)),
                            'low': float(item.get('low', 0)),
                            'close': float(item.get('close', 0)),
                            'volume': float(item.get('volume', 0)),
                        })
            except json.JSONDecodeError:
                # 如果JSON解析失败，尝试正则
                pattern = r'\{[^}]*day:"([^"]+)"[^}]*open:"([^"]+)"[^}]*high:"([^"]+)"[^}]*low:"([^"]+)"[^}]*close:"([^"]+)"[^}]*volume:"([^"]+)"[^}]*\}'
                matches = re.findall(pattern, text)
                for match in matches[-days:]:
                    results.append({
                        'date': match[0],
                        'open': float(match[1]),
                        'high': float(match[2]),
                        'low': float(match[3]),
                        'close': float(match[4]),
                        'volume': float(match[5]),
                    })
    except Exception as e:
        print(f"新浪财经数据获取失败: {e}", file=sys.stderr)
    
    return results


def get_yahoo_kline(symbol: str, days: int = 30) -> List[Dict]:
    """
    从Yahoo Finance获取K线数据（主要用于美股）
    symbol: 美股ticker，如 MU, NVDA, AAPL
    """
    results = []
    
    try:
        import yfinance as yf
        
        ticker = yf.Ticker(symbol)
        period = '3mo' if days <= 90 else '6mo'
        hist = ticker.history(period=period)
        
        if hist is not None and not hist.empty:
            for idx, row in hist.tail(days).iterrows():
                results.append({
                    'date': idx.strftime('%Y-%m-%d'),
                    'open': round(float(row['Open']), 2),
                    'high': round(float(row['High']), 2),
                    'low': round(float(row['Low']), 2),
                    'close': round(float(row['Close']), 2),
                    'volume': int(row['Volume']),
                })
    except ImportError:
        print("yfinance未安装，跳过Yahoo Finance数据获取", file=sys.stderr)
    except Exception as e:
        print(f"Yahoo Finance数据获取失败: {e}", file=sys.stderr)
    
    return results


def get_eastmoney_kline(code: str, days: int = 30, market: str = 'auto') -> List[Dict]:
    """
    从东方财富获取K线数据
    code: 纯代码，如 600519, 03690
    market: 'auto'(自动判断), 'sh'(沪市), 'sz'(深市), 'hk'(港股), 'us'(美股)
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://quote.eastmoney.com/',
    }
    
    # 判断市场
    if market == 'auto':
        if code.startswith('6'):
            secid = f'1.{code}'
        elif code.startswith(('0', '3')):
            secid = f'0.{code}'
        elif code.startswith('68'):
            secid = f'1.{code}'  # 科创板
        else:
            # 港股或美股，尝试不同市场
            secid = f'116.{code}'  # 港股
    elif market == 'hk':
        secid = f'116.{code}'
    elif market == 'us':
        secid = f'105.{code}'
    elif market == 'sh':
        secid = f'1.{code}'
    elif market == 'sz':
        secid = f'0.{code}'
    else:
        secid = f'1.{code}'
    
    results = []
    
    try:
        url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
        params = {
            'secid': secid,
            'fields1': 'f1,f2,f3,f4,f5,f6',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
            'klt': '101',  # 日K
            'fqt': '1',    # 前复权
            'end': '20500101',
            'lmt': days + 20,  # 多取一些用于计算
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and 'data' in data and data['data'] and 'klines' in data['data']:
                for kline in data['data']['klines'][-days:]:
                    parts = kline.split(',')
                    if len(parts) >= 6:
                        results.append({
                            'date': parts[0],
                            'open': float(parts[1]),
                            'close': float(parts[2]),
                            'high': float(parts[3]),
                            'low': float(parts[4]),
                            'volume': float(parts[5]),
                            'amount': float(parts[6]) if len(parts) > 6 else 0,
                            'amplitude': float(parts[7]) if len(parts) > 7 else 0,
                            'change_pct': float(parts[8]) if len(parts) > 8 else 0,
                            'change_amount': float(parts[9]) if len(parts) > 9 else 0,
                            'turnover': float(parts[10]) if len(parts) > 10 else 0,
                        })
    except Exception as e:
        print(f"东方财富数据获取失败: {e}", file=sys.stderr)
    
    return results


def get_stock_data(keyword: str, days: int = 30) -> Dict:
    """
    获取股票数据（自动判断数据源）
    
    Returns:
        {
            'code': '股票代码',
            'name': '股票名称',
            'klines': [...],  # K线数据
            'source': '数据源'
        }
    """
    # 获取股票代码
    symbol = get_stock_code(keyword)
    if not symbol:
        # 尝试作为纯代码使用
        if keyword.isdigit():
            if keyword.startswith('6'):
                symbol = f'SH{keyword}'
            else:
                symbol = f'SZ{keyword}'
        else:
            return {'error': f'未找到股票: {keyword}'}
    
    # 提取纯代码和市场
    market = 'auto'
    if symbol.startswith('SH'):
        code = symbol[2:]
        market = 'sh'
    elif symbol.startswith('SZ'):
        code = symbol[2:]
        market = 'sz'
    elif symbol.startswith('HK'):
        code = symbol[2:]
        market = 'hk'
    elif symbol.startswith('US'):
        code = symbol[2:]
        market = 'us'
    else:
        code = symbol
    
    # 美股优先使用Yahoo Finance
    if market == 'us':
        klines = get_yahoo_kline(code, days)
        source = 'yahoo'
    
    if not klines:
        klines = get_eastmoney_kline(code, days, market)
        source = 'eastmoney'
    
    if not klines and market == 'hk':
        code_stripped = code.lstrip('0')
        klines = get_eastmoney_kline(code_stripped, days, 'hk')
    
    if not klines:
        if market in ('sh', 'sz', 'auto'):
            klines = get_sina_kline(code, days)
            source = 'sina'
    
    if not klines:
        return {'error': f'无法获取股票数据: {symbol}'}
    
    return {
        'code': symbol,
        'pure_code': code,
        'market': market,
        'klines': klines,
        'source': source,
        'latest': klines[-1] if klines else None
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python stock_data.py <stock_name_or_code> [days]")
        print("Examples:")
        print("  python stock_data.py 茅台 30")
        print("  python stock_data.py 600519 30")
        print("  python stock_data.py SH600519 30")
        sys.exit(1)
    
    keyword = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    data = get_stock_data(keyword, days)
    print(json.dumps(data, ensure_ascii=False, indent=2))
