#!/usr/bin/env python3
"""
雪球爬虫脚本 - 获取股票讨论和资讯
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re
import sys
import time


def get_stock_code(keyword: str) -> dict:
    """
    根据关键词搜索股票代码
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Origin': 'https://xueqiu.com',
        'Referer': 'https://xueqiu.com/',
    }
    
    try:
        # 雪球搜索接口
        url = 'https://xueqiu.com/query/v1/search/web/all.json'
        params = {
            'q': keyword,
            'page': 1,
            'size': 10
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            stocks = []
            if 'stocks' in data:
                for stock in data['stocks'][:5]:
                    stocks.append({
                        'code': stock.get('code', ''),
                        'name': stock.get('name', ''),
                        'symbol': stock.get('symbol', ''),
                        'exchange': stock.get('exchange', '')
                    })
            return {'stocks': stocks}
    except Exception as e:
        print(f"搜索股票代码失败: {e}", file=sys.stderr)
    
    return {'stocks': []}


def get_stock_news(symbol: str, days: int = 30, max_items: int = 20) -> list:
    """
    获取雪球股票相关新闻和讨论
    
    Args:
        symbol: 股票代码（如 SH600519, SZ000001）
        days: 搜索最近几天
        max_items: 最大返回条数
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Origin': 'https://xueqiu.com',
        'Referer': f'https://xueqiu.com/S/{symbol}',
    }
    
    results = []
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # 首先获取cookies
    session = requests.Session()
    try:
        session.get('https://xueqiu.com', headers=headers, timeout=10)
        time.sleep(0.5)  # 避免请求过快
    except:
        pass
    
    # 获取股票新闻
    try:
        url = f'https://xueqiu.com/v5/stock/{symbol}/news.json'
        params = {
            'page': 1,
            'size': max_items
        }
        
        response = session.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'list' in data:
                for item in data['list'][:max_items]:
                    created_at = item.get('created_at', 0)
                    item_time = datetime.fromtimestamp(created_at / 1000) if created_at else None
                    
                    if item_time and item_time >= cutoff_date:
                        results.append({
                            'title': item.get('title', ''),
                            'content': item.get('text', '')[:500] if item.get('text') else '',
                            'time': item_time.strftime('%Y-%m-%d %H:%M'),
                            'source': '雪球',
                            'url': f"https://xueqiu.com/{item.get('id', '')}"
                        })
    except Exception as e:
        print(f"获取雪球新闻失败: {e}", file=sys.stderr)
    
    # 获取热门讨论
    try:
        url = f'https://xueqiu.com/query/v1/symbol/search/status.json'
        params = {
            'symbol': symbol,
            'count': max_items,
            'comment': 0,
            'page': 1,
            'source': 'all'
        }
        
        response = session.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'list' in data:
                for item in data['list'][:max_items]:
                    created_at = item.get('created_at', 0)
                    item_time = datetime.fromtimestamp(created_at / 1000) if created_at else None
                    
                    if item_time and item_time >= cutoff_date:
                        title = item.get('title', '') or item.get('text', '')[:50]
                        results.append({
                            'title': title,
                            'content': item.get('text', '')[:500] if item.get('text') else '',
                            'time': item_time.strftime('%Y-%m-%d %H:%M'),
                            'source': '雪球讨论',
                            'user': item.get('user', {}).get('screen_name', ''),
                            'retweet_count': item.get('retweet_count', 0),
                            'reply_count': item.get('reply_count', 0),
                            'like_count': item.get('like_count', 0)
                        })
    except Exception as e:
        print(f"获取雪球讨论失败: {e}", file=sys.stderr)
    
    return results


def search_keyword(keyword: str, days: int = 30, max_items: int = 20) -> list:
    """
    按关键词搜索雪球内容
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    
    session = requests.Session()
    try:
        session.get('https://xueqiu.com', headers=headers, timeout=10)
        time.sleep(0.5)
    except:
        pass
    
    results = []
    cutoff_date = datetime.now() - timedelta(days=days)
    
    try:
        url = 'https://xueqiu.com/query/v1/search/web/all.json'
        params = {
            'q': keyword,
            'page': 1,
            'size': max_items
        }
        
        response = session.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # 处理帖子
            if 'posts' in data:
                for item in data['posts'][:max_items]:
                    created_at = item.get('created_at', 0)
                    item_time = datetime.fromtimestamp(created_at / 1000) if created_at else None
                    
                    if item_time and item_time >= cutoff_date:
                        results.append({
                            'title': item.get('title', '') or item.get('text', '')[:50],
                            'content': item.get('text', '')[:500] if item.get('text') else '',
                            'time': item_time.strftime('%Y-%m-%d %H:%M'),
                            'source': '雪球',
                            'user': item.get('user', {}).get('screen_name', ''),
                        })
            
            # 处理新闻
            if 'news' in data:
                for item in data['news'][:max_items]:
                    results.append({
                        'title': item.get('title', ''),
                        'content': item.get('text', '')[:500] if item.get('text') else '',
                        'time': '',  # 新闻可能没有时间
                        'source': '雪球新闻'
                    })
    except Exception as e:
        print(f"雪球关键词搜索失败: {e}", file=sys.stderr)
    
    return results


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python xueqiu_scraper.py <keyword_or_symbol> [days] [max_items]")
        print("Examples:")
        print("  python xueqiu_scraper.py 茅台")
        print("  python xueqiu_scraper.py SH600519 30 20")
        sys.exit(1)
    
    query = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    max_items = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    
    # 判断是否为股票代码
    if query.upper().startswith(('SH', 'SZ', 'HK', 'US')):
        results = get_stock_news(query.upper(), days, max_items)
    else:
        # 先搜索股票代码
        stock_info = get_stock_code(query)
        if stock_info['stocks']:
            symbol = stock_info['stocks'][0]['symbol']
            results = get_stock_news(symbol, days, max_items)
        else:
            # 直接关键词搜索
            results = search_keyword(query, days, max_items)
    
    print(json.dumps(results, ensure_ascii=False, indent=2))
