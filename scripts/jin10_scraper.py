#!/usr/bin/env python3
"""
金十数据爬虫脚本 - 获取财经快讯和新闻
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re
import sys


def search_jin10(keyword: str, days: int = 30, max_items: int = 20) -> list:
    """
    搜索金十数据相关资讯
    
    Args:
        keyword: 搜索关键词（股票名称、代码等）
        days: 搜索最近几天的新闻
        max_items: 最大返回条数
    
    Returns:
        新闻列表，每条包含 title, content, time, source
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://www.jin10.com/',
    }
    
    results = []
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # 金十数据快讯接口
    try:
        # 尝试获取实时快讯
        flash_url = 'https://flash-api.jin10.com/get_flash_list'
        params = {
            'channel': '-8200',  # 全部频道
            'vip': 1,
            'max_time': int(datetime.now().timestamp())
        }
        
        response = requests.get(flash_url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and 'data' in data:
                for item in data['data'][:100]:  # 获取最近100条筛选
                    content = item.get('content', '') or item.get('data', {}).get('content', '')
                    title = item.get('title', '') or content[:50] if content else ''
                    timestamp = item.get('time', 0)
                    item_time = datetime.fromtimestamp(timestamp) if timestamp else None
                    
                    # 关键词筛选
                    if keyword.lower() in content.lower() or keyword.lower() in title.lower():
                        if item_time and item_time >= cutoff_date:
                            results.append({
                                'title': title,
                                'content': content,
                                'time': item_time.strftime('%Y-%m-%d %H:%M'),
                                'source': '金十数据'
                            })
                    
                    if len(results) >= max_items:
                        break
    except Exception as e:
        print(f"金十数据快讯接口请求失败: {e}", file=sys.stderr)
    
    # 如果API失败，尝试网页爬取
    if not results:
        try:
            search_url = f'https://r.jin10.com/?q={keyword}'
            response = requests.get(search_url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # 解析搜索结果页面
                items = soup.select('.news-item, .flash-item, .list-item')
                for item in items[:max_items]:
                    title_elem = item.select_one('.title, .news-title, h3, h4')
                    content_elem = item.select_one('.content, .news-content, p')
                    time_elem = item.select_one('.time, .news-time, .date')
                    
                    if title_elem or content_elem:
                        results.append({
                            'title': title_elem.get_text(strip=True) if title_elem else '',
                            'content': content_elem.get_text(strip=True) if content_elem else '',
                            'time': time_elem.get_text(strip=True) if time_elem else '',
                            'source': '金十数据'
                        })
        except Exception as e:
            print(f"金十数据网页爬取失败: {e}", file=sys.stderr)
    
    return results


def get_market_news(max_items: int = 30) -> list:
    """
    获取市场重要新闻（不限关键词）
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    
    results = []
    
    try:
        url = 'https://flash-api.jin10.com/get_flash_list'
        params = {
            'channel': '-8200',
            'vip': 1,
            'max_time': int(datetime.now().timestamp())
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and 'data' in data:
                for item in data['data'][:max_items]:
                    content = item.get('content', '') or item.get('data', {}).get('content', '')
                    timestamp = item.get('time', 0)
                    item_time = datetime.fromtimestamp(timestamp) if timestamp else None
                    
                    results.append({
                        'title': content[:50] + '...' if len(content) > 50 else content,
                        'content': content,
                        'time': item_time.strftime('%Y-%m-%d %H:%M') if item_time else '',
                        'source': '金十数据',
                        'importance': item.get('importance', 0)
                    })
    except Exception as e:
        print(f"获取市场新闻失败: {e}", file=sys.stderr)
    
    return results


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python jin10_scraper.py <keyword> [days] [max_items]")
        sys.exit(1)
    
    keyword = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    max_items = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    
    results = search_jin10(keyword, days, max_items)
    print(json.dumps(results, ensure_ascii=False, indent=2))
