#!/usr/bin/env python3
"""
多源资讯搜索脚本 - 整合金十数据、雪球、新闻搜索、政策公告等
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import re
import sys
import time
from typing import List, Dict


def search_jin10(keyword: str, days: int = 90, max_items: int = 20) -> List[Dict]:
    """搜索金十数据"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.jin10.com/',
    }
    
    results = []
    cutoff_date = datetime.now() - timedelta(days=days)
    
    try:
        flash_url = 'https://flash-api.jin10.com/get_flash_list'
        params = {
            'channel': '-8200',
            'vip': 1,
            'max_time': int(datetime.now().timestamp())
        }
        
        response = requests.get(flash_url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and 'data' in data:
                for item in data['data'][:200]:
                    content = item.get('content', '') or item.get('data', {}).get('content', '')
                    title = item.get('title', '') or content[:50] if content else ''
                    timestamp = item.get('time', 0)
                    item_time = datetime.fromtimestamp(timestamp) if timestamp else None
                    
                    if keyword.lower() in content.lower() or keyword.lower() in title.lower():
                        if item_time and item_time >= cutoff_date:
                            results.append({
                                'title': title,
                                'content': content,
                                'time': item_time.strftime('%Y-%m-%d %H:%M'),
                                'source': '金十数据',
                                'type': '快讯'
                            })
                    
                    if len(results) >= max_items:
                        break
    except Exception as e:
        print(f"金十数据获取失败: {e}", file=sys.stderr)
    
    return results


def search_xueqiu(keyword: str, days: int = 90, max_items: int = 20) -> List[Dict]:
    """搜索雪球"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
    }
    
    session = requests.Session()
    try:
        session.get('https://xueqiu.com', headers=headers, timeout=10)
        time.sleep(0.3)
    except:
        pass
    
    results = []
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # 搜索帖子
    try:
        url = 'https://xueqiu.com/query/v1/search/web/all.json'
        params = {'q': keyword, 'page': 1, 'size': max_items}
        
        response = session.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            if 'posts' in data:
                for item in data['posts'][:max_items]:
                    created_at = item.get('created_at', 0)
                    item_time = datetime.fromtimestamp(created_at / 1000) if created_at else None
                    
                    results.append({
                        'title': item.get('title', '') or item.get('text', '')[:50],
                        'content': item.get('text', '')[:500] if item.get('text') else '',
                        'time': item_time.strftime('%Y-%m-%d %H:%M') if item_time else '',
                        'source': '雪球',
                        'type': '讨论',
                        'user': item.get('user', {}).get('screen_name', ''),
                        'retweet_count': item.get('retweet_count', 0),
                        'like_count': item.get('like_count', 0)
                    })
    except Exception as e:
        print(f"雪球搜索失败: {e}", file=sys.stderr)
    
    return results


def search_eastmoney_news(keyword: str, days: int = 90, max_items: int = 15) -> List[Dict]:
    """搜索东方财富新闻"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://so.eastmoney.com/',
    }
    
    results = []
    
    try:
        url = 'https://searchapi.eastmoney.com/bussiness/web/QuotationLabelSearch'
        params = {
            'keyword': keyword,
            'type': 'news',  # 新闻类型
            'pi': 1,
            'ps': max_items,
            'token': '0'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and 'Data' in data:
                for item in data['Data'][:max_items]:
                    results.append({
                        'title': item.get('Title', '') or item.get('title', ''),
                        'content': item.get('Content', '')[:500] or item.get('content', '')[:500] if item.get('Content') or item.get('content') else '',
                        'time': item.get('ShowTime', '') or item.get('time', ''),
                        'source': '东方财富',
                        'type': '新闻',
                        'url': item.get('Url', '') or item.get('url', '')
                    })
    except Exception as e:
        print(f"东方财富新闻搜索失败: {e}", file=sys.stderr)
    
    return results


def search_sina_finance(keyword: str, days: int = 90, max_items: int = 15) -> List[Dict]:
    """搜索新浪财经"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://search.sina.com.cn/',
    }
    
    results = []
    
    try:
        url = 'https://interface.sina.cn/news/wap/finance_news_search.d.json'
        params = {
            'keyword': keyword,
            'page': 1,
            'pagesize': max_items,
            'c': 'finance'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and 'result' in data and 'data' in data['result']:
                for item in data['result']['data'][:max_items]:
                    results.append({
                        'title': item.get('title', ''),
                        'content': item.get('intro', '')[:500] if item.get('intro') else '',
                        'time': item.get('ctime', '') or item.get('time', ''),
                        'source': '新浪财经',
                        'type': '新闻',
                        'url': item.get('url', '')
                    })
    except Exception as e:
        print(f"新浪财经搜索失败: {e}", file=sys.stderr)
    
    return results


def search_sina_policy(keyword: str, days: int = 90, max_items: int = 10) -> List[Dict]:
    """搜索政策相关新闻"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    }
    
    results = []
    
    try:
        # 搜索政策类新闻
        policy_keyword = f"{keyword} 政策"
        url = 'https://interface.sina.cn/news/wap/finance_news_search.d.json'
        params = {
            'keyword': policy_keyword,
            'page': 1,
            'pagesize': max_items,
            'c': 'finance'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and 'result' in data and 'data' in data['result']:
                for item in data['result']['data'][:max_items]:
                    results.append({
                        'title': item.get('title', ''),
                        'content': item.get('intro', '')[:500] if item.get('intro') else '',
                        'time': item.get('ctime', ''),
                        'source': '新浪财经',
                        'type': '政策新闻',
                        'url': item.get('url', '')
                    })
    except Exception as e:
        print(f"政策新闻搜索失败: {e}", file=sys.stderr)
    
    return results


def search_cls_cn(keyword: str, days: int = 90, max_items: int = 15) -> List[Dict]:
    """搜索财联社"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://www.cls.cn/',
    }
    
    results = []
    cutoff_date = datetime.now() - timedelta(days=days)
    
    try:
        url = 'https://www.cls.cn/api/sw'
        params = {'app': 'CailianpressWeb', 'os': 'web', 'sv': '8.4.6'}
        data = {
            'type': 'telegram',
            'keyword': keyword,
            'rn': max_items,
            'last_time': ''
        }
        
        response = requests.post(url, headers=headers, params=params, json=data, timeout=10)
        if response.status_code == 200:
            resp_data = response.json()
            if resp_data and 'data' in resp_data and 'telegram_data' in resp_data['data']:
                for item in resp_data['data']['telegram_data'][:max_items]:
                    ctime = item.get('ctime', 0)
                    item_time = datetime.fromtimestamp(ctime) if ctime else None
                    
                    if item_time and item_time >= cutoff_date:
                        results.append({
                            'title': item.get('title', '') or item.get('content', '')[:50],
                            'content': item.get('content', ''),
                            'time': item_time.strftime('%Y-%m-%d %H:%M') if item_time else '',
                            'source': '财联社',
                            'type': '快讯',
                            'importance': item.get('level', 'normal')
                        })
    except Exception as e:
        print(f"财联社搜索失败: {e}", file=sys.stderr)
    
    return results


def search_company_announcement(keyword: str, stock_code: str = '', max_items: int = 10) -> List[Dict]:
    """搜索公司公告"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Referer': 'https://data.eastmoney.com/',
    }
    
    results = []
    
    try:
        # 东方财富公告搜索
        url = 'https://searchapi.eastmoney.com/bussiness/web/QuotationLabelSearch'
        params = {
            'keyword': keyword,
            'type': 'announcement',
            'pi': 1,
            'ps': max_items,
            'token': '0'
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and 'Data' in data:
                for item in data['Data'][:max_items]:
                    results.append({
                        'title': item.get('Title', '') or item.get('title', ''),
                        'content': item.get('Summary', '')[:500] if item.get('Summary') else '',
                        'time': item.get('NoticeDate', '') or item.get('time', ''),
                        'source': '东方财富公告',
                        'type': '公司公告',
                        'url': item.get('Url', '') or item.get('url', '')
                    })
    except Exception as e:
        print(f"公司公告搜索失败: {e}", file=sys.stderr)
    
    return results


def search_yahoo_finance(keyword: str, days: int = 90, max_items: int = 15) -> List[Dict]:
    """搜索Yahoo Finance新闻（主要用于美股）"""
    results = []
    
    try:
        import yfinance as yf
        
        ticker_map = {
            '美光': 'MU', '美光科技': 'MU', '英伟达': 'NVDA', '苹果': 'AAPL',
            '特斯拉': 'TSLA', '微软': 'MSFT', '亚马逊': 'AMZN', '谷歌': 'GOOGL',
            '英特尔': 'INTC', '高通': 'QCOM', '台积电': 'TSM', '拼多多': 'PDD',
            '京东': 'JD', '蔚来': 'NIO', '小鹏': 'XPEV', '理想': 'LI',
            '阿里巴巴': 'BABA', '阿里': 'BABA', '百度': 'BIDU', '网易': 'NTES',
            '哔哩哔哩': 'BILI', 'B站': 'BILI',
        }
        
        symbol = keyword.upper()
        if keyword in ticker_map:
            symbol = ticker_map[keyword]
        
        ticker = yf.Ticker(symbol)
        news = ticker.news
        
        if news:
            cutoff_date = datetime.now() - timedelta(days=days)
            for item in news[:max_items]:
                pub_time = None
                if 'content' in item:
                    content_data = item['content']
                    title = content_data.get('title', '')
                    summary = content_data.get('summary', '') or content_data.get('description', '')
                    pub_date_str = content_data.get('pubDate', '')
                    provider_name = content_data.get('provider', {}).get('displayName', 'Yahoo Finance')
                    canonical_url = content_data.get('canonicalUrl', {}).get('url', '')
                    
                    if pub_date_str:
                        try:
                            pub_time = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00')).replace(tzinfo=None)
                        except:
                            pass
                else:
                    title = item.get('title', '')
                    summary = item.get('summary', '') or item.get('description', '')
                    provider_name = item.get('publisher', 'Yahoo Finance')
                    canonical_url = item.get('link', '')
                    publish_ts = item.get('providerPublishTime', 0)
                    if publish_ts:
                        pub_time = datetime.fromtimestamp(publish_ts)
                
                if pub_time and pub_time < cutoff_date:
                    continue
                
                results.append({
                    'title': title,
                    'content': summary[:500] if summary else '',
                    'time': pub_time.strftime('%Y-%m-%d %H:%M') if pub_time else '',
                    'source': f'Yahoo Finance ({provider_name})',
                    'type': '美股新闻',
                    'url': canonical_url
                })
    except ImportError:
        print("yfinance未安装，跳过Yahoo Finance搜索", file=sys.stderr)
    except Exception as e:
        print(f"Yahoo Finance新闻获取失败: {e}", file=sys.stderr)
    
    return results


def search_industry_news(keyword: str, days: int = 90, max_items: int = 10) -> List[Dict]:
    """搜索行业新闻"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    }
    
    results = []
    
    try:
        # 构造行业相关搜索词
        industry_keywords = ['行业', '市场', '趋势', '发展']
        for ind_kw in industry_keywords:
            search_kw = f"{keyword} {ind_kw}"
            
            url = 'https://searchapi.eastmoney.com/bussiness/web/QuotationLabelSearch'
            params = {
                'keyword': search_kw,
                'type': 'news',
                'pi': 1,
                'ps': 5,
                'token': '0'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data and 'Data' in data:
                    for item in data['Data'][:3]:
                        results.append({
                            'title': item.get('Title', '') or item.get('title', ''),
                            'content': item.get('Content', '')[:300] if item.get('Content') else '',
                            'time': item.get('ShowTime', ''),
                            'source': '行业新闻',
                            'type': '行业资讯'
                        })
            
            if len(results) >= max_items:
                break
            time.sleep(0.2)
    except Exception as e:
        print(f"行业新闻搜索失败: {e}", file=sys.stderr)
    
    return results[:max_items]


def search_all(keyword: str, days: int = 90, stock_code: str = '') -> Dict:
    """
    综合搜索所有来源
    
    Args:
        keyword: 搜索关键词
        days: 搜索天数范围
        stock_code: 股票代码（可选，用于精确搜索公告）
    
    Returns:
        按来源分类的搜索结果
    """
    results = {
        'keyword': keyword,
        'days': days,
        'sources': {}
    }
    
    # 金十数据
    jin10_results = search_jin10(keyword, days, 15)
    if jin10_results:
        results['sources']['金十数据'] = jin10_results
    
    # 雪球
    xueqiu_results = search_xueqiu(keyword, days, 15)
    if xueqiu_results:
        results['sources']['雪球'] = xueqiu_results
    
    # 东方财富新闻
    eastmoney_results = search_eastmoney_news(keyword, days, 15)
    if eastmoney_results:
        results['sources']['东方财富'] = eastmoney_results
    
    # 新浪财经
    sina_results = search_sina_finance(keyword, days, 10)
    if sina_results:
        results['sources']['新浪财经'] = sina_results
    
    # 财联社
    cls_results = search_cls_cn(keyword, days, 10)
    if cls_results:
        results['sources']['财联社'] = cls_results
    
    # 政策新闻
    policy_results = search_sina_policy(keyword, days, 10)
    if policy_results:
        results['sources']['政策新闻'] = policy_results
    
    # 公司公告
    announcement_results = search_company_announcement(keyword, stock_code, 10)
    if announcement_results:
        results['sources']['公司公告'] = announcement_results
    
    # Yahoo Finance（美股新闻）
    yahoo_results = search_yahoo_finance(keyword, days, 15)
    if yahoo_results:
        results['sources']['Yahoo Finance'] = yahoo_results
    
    # 行业新闻
    industry_results = search_industry_news(keyword, days, 10)
    if industry_results:
        results['sources']['行业新闻'] = industry_results
    
    # 统计
    total_count = sum(len(v) for v in results['sources'].values())
    results['total_count'] = total_count
    
    return results


def merge_and_sort(results: Dict) -> List[Dict]:
    """合并所有结果并按时间排序"""
    all_items = []
    
    for source, items in results.get('sources', {}).items():
        all_items.extend(items)
    
    # 按时间排序（最新的在前）
    def parse_time(item):
        time_str = item.get('time', '')
        if not time_str:
            return datetime.min
        try:
            # 尝试多种格式
            for fmt in ['%Y-%m-%d %H:%M', '%Y-%m-%d', '%Y/%m/%d %H:%M']:
                try:
                    return datetime.strptime(time_str, fmt)
                except:
                    continue
            return datetime.min
        except:
            return datetime.min
    
    all_items.sort(key=parse_time, reverse=True)
    return all_items


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python multi_source_search.py <keyword> [days] [stock_code]")
        sys.exit(1)
    
    keyword = sys.argv[1]
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 90
    stock_code = sys.argv[3] if len(sys.argv) > 3 else ''
    
    results = search_all(keyword, days, stock_code)
    print(json.dumps(results, ensure_ascii=False, indent=2))
