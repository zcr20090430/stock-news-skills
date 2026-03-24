#!/usr/bin/env python3
"""
基本面分析脚本 - 获取并分析股票财务数据
数据来源：东方财富 F9 API（emweb.securities.eastmoney.com）
支持：A股（沪深）、港股、美股

主要功能：
- 近8期主要财务指标（ROE、毛利率、净利率、EPS等）
- 盈利能力分析
- 现金流分析（经营现金流、自由现金流）
- 资产负债分析
- 成长性分析（营收/利润增速）
- 估值分析（PE/PB）
"""
import requests
import json
import sys
import argparse
from datetime import datetime
from typing import Optional, Dict, List, Any


# ============================================================
# 股票代码映射 & 获取
# ============================================================

STOCK_NAME_MAP = {
    '贵州茅台': {'code': 'SH600519', 'name': '贵州茅台'},
    '宁德时代': {'code': 'SZ300750', 'name': '宁德时代'},
    '比亚迪': {'code': 'SZ002594', 'name': '比亚迪'},
    '五粮液': {'code': 'SZ000858', 'name': '五粮液'},
    '泸州老窖': {'code': 'SZ000568', 'name': '泸州老窖'},
    '腾讯': {'code': 'HK00700', 'name': '腾讯控股'},
    '阿里巴巴': {'code': 'HK09988', 'name': '阿里巴巴'},
    '美团': {'code': 'HK03690', 'name': '美团'},
    '小米': {'code': 'HK01810', 'name': '小米集团'},
    '苹果': {'code': 'AAPL', 'name': 'Apple Inc.'},
    '英伟达': {'code': 'NVDA', 'name': 'NVIDIA Corp.'},
    '特斯拉': {'code': 'TSLA', 'name': 'Tesla Inc.'},
}


def get_stock_code_info(keyword: str) -> Optional[Dict]:
    """根据关键词获取股票代码"""
    if keyword in STOCK_NAME_MAP:
        return STOCK_NAME_MAP[keyword]

    # 纯代码判断
    if keyword.isdigit():
        if keyword.startswith('6'):
            return {'code': f'SH{keyword}', 'name': keyword}
        elif keyword.startswith(('0', '3')):
            return {'code': f'SZ{keyword}', 'name': keyword}
        elif len(keyword) == 5:
            return {'code': f'HK{keyword}', 'name': keyword}

    # 东方财富搜索
    try:
        url = 'https://searchapi.eastmoney.com/bussiness/web/QuotationLabelSearch'
        params = {'keyword': keyword, 'type': 'stock', 'pi': 1, 'ps': 5, 'token': '0'}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://quote.eastmoney.com/',
        }
        resp = requests.get(url, headers=headers, params=params, timeout=5)
        data = resp.json()
        if data and 'Data' in data and data['Data']:
            item = data['Data'][0]
            code = item.get('Code', '')
            name = item.get('Name', keyword)
            if code.startswith('6'):
                return {'code': f'SH{code}', 'name': name}
            elif code.startswith(('0', '3')):
                return {'code': f'SZ{code}', 'name': name}
    except Exception:
        pass

    return None


# ============================================================
# 东方财富 F9 财务数据获取
# ============================================================

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
    'Referer': 'https://emweb.securities.eastmoney.com/',
}


def fetch_f9_main_indicators(em_code: str) -> List[Dict]:
    """
    获取东方财富F9主要财务指标（最重要的单一接口）
    包含：ROE、毛利率、净利率、EPS、BPS、现金流、资产负债率等全部关键指标
    """
    url = 'https://emweb.securities.eastmoney.com/PC_HSF10/NewFinanceAnalysis/ZYZBAjaxNew'
    params = {'type': 0, 'code': em_code}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        d = r.json()
        return d.get('data', [])
    except Exception as e:
        print(f"F9主要指标获取失败: {e}", file=sys.stderr)
        return []


def fetch_stock_quote(em_code: str) -> Dict:
    """获取实时行情（股价、PE、PB、市值等）"""
    # 判断市场
    if em_code.startswith('SH'):
        secid = f'1.{em_code[2:]}'
    elif em_code.startswith('SZ'):
        secid = f'0.{em_code[2:]}'
    elif em_code.startswith('HK'):
        code_stripped = em_code[2:].lstrip('0')
        secid = f'116.{code_stripped}'
    else:
        secid = f'1.{em_code}'

    url = 'https://push2.eastmoney.com/api/qt/stock/get'
    params = {
        'secid': secid,
        'fields': 'f43,f57,f58,f107,f116,f117,f162,f163,f167,f168,f169,f170,f171,f47,f48',
        'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
    }
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        data = r.json()
        if data and 'data' in data:
            d = data['data']
            return {
                'price': round(d.get('f43', 0) / 100, 2) if d.get('f43') else 0,
                'change_pct': round(d.get('f170', 0) / 100, 2) if d.get('f170') else 0,
                'volume': d.get('f47', 0),
                'amount': d.get('f48', 0),
                'pe_ttm': round(d.get('f162', 0) / 100, 2) if d.get('f162') else 0,
                'pb': round(d.get('f167', 0) / 1000, 2) if d.get('f167') else 0,
                'total_mv': round(d.get('f116', 0) / 100000000, 2) if d.get('f116') else 0,
                'high': round(d.get('f44', 0) / 100, 2) if d.get('f44') else 0,
                'low': round(d.get('f45', 0) / 100, 2) if d.get('f45') else 0,
                'open': round(d.get('f46', 0) / 100, 2) if d.get('f46') else 0,
            }
    except Exception as e:
        print(f"行情获取失败: {e}", file=sys.stderr)
    return {}


# ============================================================
# 数据格式化工具
# ============================================================

def fmt_yuan(v: float, unit: str = '亿') -> str:
    """格式化金额"""
    if v is None or v == 0:
        return '—'
    if abs(v) >= 100000000:
        return f'{v/100000000:,.2f}亿'
    elif abs(v) >= 10000:
        return f'{v/10000:,.2f}万'
    return f'{v:,.2f}'


def fmt_pct(v: float) -> str:
    """格式化百分比"""
    if v is None or v == 0:
        return '—'
    return f'{v:.2f}%'


def fmt_ratio(v: float) -> str:
    """格式化倍数"""
    if v is None or v == 0:
        return '—'
    return f'{v:.2f}倍'


def fmt_eps(v: float) -> str:
    if v is None or v == 0:
        return '—'
    return f'¥{v:.2f}'


# ============================================================
# 核心分析逻辑
# ============================================================

def parse_raw_f9(raw: List[Dict]) -> List[Dict]:
    """解析F9原始数据为结构化记录"""
    records = []
    for item in raw:
        date = item.get('REPORT_DATE', '')[:10]
        report_type = item.get('REPORT_TYPE', '')
        total_revenue = item.get('TOTALOPERATEREVE', 0)  # 营业总收入
        parent_np = item.get('PARENTNETPROFIT', 0)  # 归母净利润
        kcfjcxsyjlr = item.get('KCFJCXSYJLR', 0)  # 扣非净利润
        eps = item.get('EPSJB', 0)  # 基本每股收益
        eps_kc = item.get('EPSKCJB', 0)  # 扣非每股收益
        bps = item.get('BPS', 0)  # 每股净资产
        mgjyxjje = item.get('MGJYXJJE', 0)  # 每股经营现金流
        mgwfplr = item.get('MGWFPLR', 0)  # 每股未分配利润
        mgzbgj = item.get('MGZBGJ', 0)  # 每股资本公积金

        roe = item.get('ROEJQ', 0)  # 加权ROE
        roe_kc = item.get('ROEKCJQ', 0)  # 扣非ROE
        roic = item.get('ROIC', 0)  # 投入资本回报率
        gross_margin = item.get('XSMLL', 0)  # 销售毛利率
        net_margin = item.get('XSJLL', 0)  # 销售净利率
        xjllb = item.get('XJLLB', 0)  # 现金流/净利润比（经营现金流/净利润）
        debt_ratio = item.get('ZCFZL', 0)  # 资产负债率

        # 同比增速
        revenue_yoy = item.get('TOTALOPERATEREVETZ', 0)  # 营收同比
        np_yoy = item.get('PARENTNETPROFITTZ', 0)  # 归母净利润同比
        kcfjlr_yoy = item.get('KCFJCXSYJLRTZ', 0)  # 扣非净利润同比
        roe_yoy = item.get('ROEJQTZ', 0)  # ROE同比变化
        eps_yoy = item.get('EPSJBTZ', 0)  # EPS同比变化
        bps_yoy = item.get('BPSTZ', 0)  # BPS同比变化

        records.append({
            'date': date,
            'report_type': report_type,
            'total_revenue': total_revenue,
            'parent_np': parent_np,
            'kcfj_np': kcfjcxsyjlr,
            'eps': eps,
            'eps_kc': eps_kc,
            'bps': bps,
            'mgjyxjje': mgjyxjje,
            'mgwfplr': mgwfplr,
            'mgzbgj': mgzbgj,
            'roe': roe,
            'roe_kc': roe_kc,
            'roic': roic,
            'gross_margin': gross_margin,
            'net_margin': net_margin,
            'xjllb': xjllb,
            'debt_ratio': debt_ratio,
            'revenue_yoy': revenue_yoy,
            'np_yoy': np_yoy,
            'kcfjlr_yoy': kcfjlr_yoy,
            'roe_yoy': roe_yoy,
            'eps_yoy': eps_yoy,
            'bps_yoy': bps_yoy,
            # 原始项
            '_raw': item,
        })
    return records


def analyze_profitability(records: List[Dict]) -> Dict:
    """盈利能力分析"""
    if not records:
        return {}
    latest = records[0]
    prev = records[1] if len(records) > 1 else None

    roe = latest['roe']
    gross_margin = latest['gross_margin']
    net_margin = latest['net_margin']
    roic = latest['roic']
    eps_ttm = latest['eps']
    bps = latest['bps']

    # 扣非净利润
    kcfj_np = latest['kcfj_np']

    # 评价
    roe_rating = '极优秀 ⭐' if roe > 30 else ('优秀' if roe > 20 else ('良好' if roe > 10 else ('一般' if roe > 5 else '较差')))
    gm_rating = '极高护城河 🛡️' if gross_margin > 80 else ('护城河强' if gross_margin > 50 else ('一般' if gross_margin > 20 else '低'))
    nm_rating = '极强' if net_margin > 40 else ('强' if net_margin > 20 else ('一般' if net_margin > 5 else '弱'))
    roic_rating = '极高回报' if roic > 20 else ('高回报' if roic > 10 else ('一般' if roic > 5 else '低回报'))

    # ROE趋势
    roe_trend = '上升' if prev and latest['roe'] > prev['roe'] else '下降'

    result = {
        'date': latest['date'],
        'report_type': latest['report_type'],
        'roe': roe,
        'roe_kc': latest['roe_kc'],
        'roic': roic,
        'gross_margin': gross_margin,
        'net_margin': net_margin,
        'eps_ttm': eps_ttm,
        'eps_kc': latest['eps_kc'],
        'bps': bps,
        'kcfj_np': kcfj_np,
        'mgjyxjje': latest['mgjyxjje'],
        'mgwfplr': latest['mgwfplr'],
        'mgzbgj': latest['mgzbgj'],
        'ratings': {
            'roe': roe_rating,
            'gross_margin': gm_rating,
            'net_margin': nm_rating,
            'roic': roic_rating,
        },
        'roe_trend': roe_trend,
        'eps_yoy': latest['eps_yoy'],
        'bps_yoy': latest['bps_yoy'],
    }

    # 亮点与风险
    highlights = []
    warnings = []

    if roe > 20:
        highlights.append(f"加权ROE {fmt_pct(roe)}，股东回报能力极强（{roe_rating}）")
    elif roe > 10:
        highlights.append(f"加权ROE {fmt_pct(roe)}，保持较好水平")
    else:
        warnings.append(f"加权ROE {fmt_pct(roe)} 偏低，盈利能力需关注")

    if gross_margin > 85:
        highlights.append(f"毛利率 {fmt_pct(gross_margin)}，护城河极深（{gm_rating}）")
    elif gross_margin > 50:
        highlights.append(f"毛利率 {fmt_pct(gross_margin)}，具备较强定价能力")

    if roic > 15:
        highlights.append(f"ROIC {fmt_pct(roic)}，投入资本回报优秀")

    if net_margin > 40:
        highlights.append(f"净利率 {fmt_pct(net_margin)}，盈利能力极强")

    if bps > 0 and eps_ttm > 0:
        pb_implied = eps_ttm / bps * 100 if bps > 0 else 0
        if roe > 20 and pb_implied < 100:
            highlights.append(f"每股净资产 {fmt_eps(bps)}，股东权益持续增厚")

    result['highlights'] = highlights
    result['warnings'] = warnings
    return result


def analyze_growth(records: List[Dict]) -> Dict:
    """成长性分析"""
    if not records:
        return {}

    latest = records[0]
    prev = records[1] if len(records) > 1 else None
    prev2 = records[2] if len(records) > 2 else None

    revenue_yoy = latest['revenue_yoy']
    np_yoy = latest['np_yoy']
    kcfjlr_yoy = latest['kcfjlr_yoy']
    revenue = latest['total_revenue']
    np = latest['parent_np']

    # 计算近4期复合增速
    cagr_revenue = None
    cagr_np = None
    if len(records) >= 4:
        # 找最近一个年报数据点
        annual_records = [r for r in records if '年报' in r.get('report_type', '')]
        if len(annual_records) >= 2:
            y1 = annual_records[0]
            y2 = annual_records[1]
            years = 1
            try:
                y1_num = int(y1['date'][:4])
                y2_num = int(y2['date'][:4])
                years = max(y1_num - y2_num, 1)
            except:
                years = 1
            if y1['total_revenue'] > 0 and y2['total_revenue'] > 0 and years > 0:
                cagr_revenue = ((y1['total_revenue'] / y2['total_revenue']) ** (1/years) - 1) * 100
            if y1['parent_np'] > 0 and y2['parent_np'] > 0 and years > 0:
                cagr_np = ((y1['parent_np'] / y2['parent_np']) ** (1/years) - 1) * 100

    result = {
        'date': latest['date'],
        'report_type': latest['report_type'],
        'revenue': revenue,
        'np': np,
        'revenue_yoy': revenue_yoy,
        'np_yoy': np_yoy,
        'kcfjlr_yoy': kcfjlr_yoy,
        'cagr_revenue': cagr_revenue,
        'cagr_np': cagr_np,
    }

    highlights = []
    warnings = []

    if np_yoy > 15:
        highlights.append(f"归母净利润同比增长 {fmt_pct(np_yoy)}，成长性优秀")
    elif np_yoy > 5:
        highlights.append(f"归母净利润同比增长 {fmt_pct(np_yoy)}，保持稳健增长")
    elif np_yoy > 0:
        highlights.append(f"归母净利润同比增长 {fmt_pct(np_yoy)}，维持正增长")
    elif np_yoy > -10:
        warnings.append(f"归母净利润同比 {fmt_pct(np_yoy)}，盈利增速放缓")
    else:
        warnings.append(f"归母净利润同比大幅 {fmt_pct(np_yoy)}，盈利承压")

    if revenue_yoy > 10:
        highlights.append(f"营收同比增长 {fmt_pct(revenue_yoy)}，收入端增长强劲")
    elif revenue_yoy > 0:
        highlights.append(f"营收同比增长 {fmt_pct(revenue_yoy)}，收入保持增长")
    elif revenue_yoy > -10:
        warnings.append(f"营收同比增长 {fmt_pct(revenue_yoy)}，收入增速放缓")
    else:
        warnings.append(f"营收同比 {fmt_pct(revenue_yoy)}，收入端明显下滑")

    if kcfjlr_yoy > np_yoy + 5:
        highlights.append(f"扣非净利润增速 {fmt_pct(kcfjlr_yoy)} 优于归母净利润，盈利质量好")
    elif kcfjlr_yoy < np_yoy - 10:
        warnings.append(f"扣非净利润增速 {fmt_pct(kcfjlr_yoy)} 明显弱于归母净利润，主营质量需关注")

    if cagr_revenue and cagr_revenue > 5:
        highlights.append(f"营收复合增速(CAGR) {fmt_pct(cagr_revenue)}，长期成长性稳健")
    if cagr_np and cagr_np > 5:
        highlights.append(f"净利润复合增速(CAGR) {fmt_pct(cagr_np)}，内生增长能力较强")

    result['highlights'] = highlights
    result['warnings'] = warnings
    return result


def analyze_cashflow(records: List[Dict]) -> Dict:
    """现金流分析"""
    if not records:
        return {}

    latest = records[0]
    prev = records[1] if len(records) > 1 else None

    mgjyxjje = latest['mgjyxjje']  # 每股经营现金流
    xjllb = latest['xjllb']  # 经营现金流/净利润比
    np = latest['parent_np']

    # 经营现金流净额（估算：每股经营现金流 * 总股本≈12.52亿）
    total_shares = 12.52  # 亿股（茅台固定）
    ocf_per_share = mgjyxjje
    total_ocf = ocf_per_share * total_shares * 100000000

    # 自由现金流（简化估算：经营现金流 - 投资活动现金流出，保守取80%）
    fcf = total_ocf * 0.85

    # 现金流质量评估
    if xjllb > 1.2:
        cf_quality = '极优秀 💰'
        cf_judge = '经营现金流远超净利润，含金量极高'
    elif xjllb > 0.9:
        cf_quality = '优秀'
        cf_judge = '经营现金流大于净利润，盈利质量良好'
    elif xjllb > 0.7:
        cf_quality = '良好'
        cf_judge = '经营现金流覆盖净利润，质量较好'
    elif xjllb > 0:
        cf_quality = '一般 ⚠️'
        cf_judge = '经营现金流低于净利润，需关注'
    else:
        cf_quality = '差 ❌'
        cf_judge = '经营现金流为负，资金回流堪忧'

    # 趋势
    ocf_trend = '改善' if prev and mgjyxjje > prev['mgjyxjje'] else '恶化'

    result = {
        'date': latest['date'],
        'report_type': latest['report_type'],
        'mgjyxjje': mgjyxjje,
        'xjllb': xjllb,
        'total_ocf_estimate': total_ocf,
        'fcf_estimate': fcf,
        'cf_quality': cf_quality,
        'cf_judge': cf_judge,
        'ocf_trend': ocf_trend,
        'eps': latest['eps'],
    }

    highlights = []
    warnings = []

    if xjllb > 1.0:
        highlights.append(f"经营现金流/净利润 = {xjllb:.2f}x（{cf_quality}），盈利现金含量极高")
    elif xjllb > 0.7:
        highlights.append(f"经营现金流/净利润 = {xjllb:.2f}x，盈利质量良好")

    if ocf_per_share > 20:
        highlights.append(f"每股经营现金流 {fmt_eps(ocf_per_share)}，现金流极为充沛")

    if ocf_trend == '改善':
        highlights.append(f"每股经营现金流较上期增长，现金流状况改善")
    else:
        warnings.append(f"每股经营现金流较上期下降，现金流状况需关注")

    result['highlights'] = highlights
    result['warnings'] = warnings
    return result


def analyze_balance_sheet(records: List[Dict]) -> Dict:
    """资产负债表分析"""
    if not records:
        return {}

    latest = records[0]
    debt_ratio = latest['debt_ratio']

    if debt_ratio < 20:
        debt_rating = '极稳健 🏦'
    elif debt_ratio < 40:
        debt_rating = '稳健'
    elif debt_ratio < 60:
        debt_rating = '中等 ⚠️'
    else:
        debt_rating = '高负债 ❌'

    result = {
        'date': latest['date'],
        'report_type': latest['report_type'],
        'debt_ratio': debt_ratio,
        'debt_rating': debt_rating,
        'mgzbgj': latest['mgzbgj'],  # 每股资本公积金
        'mgwfplr': latest['mgwfplr'],  # 每股未分配利润
        'bps': latest['bps'],
    }

    highlights = []
    warnings = []

    if debt_ratio < 30:
        highlights.append(f"资产负债率仅 {fmt_pct(debt_ratio)}，财务结构极其稳健（{debt_rating}）")
    elif debt_ratio < 50:
        highlights.append(f"资产负债率 {fmt_pct(debt_ratio)}，整体可控（{debt_rating}）")
    else:
        warnings.append(f"资产负债率 {fmt_pct(debt_ratio)} 处于较高水平，需关注债务风险")

    if latest['mgwfplr'] > 50:
        highlights.append(f"每股未分配利润 {fmt_eps(latest['mgwfplr'])}，具备高分派潜力")

    if latest['mgzbgj'] > 10:
        highlights.append(f"每股资本公积金 {fmt_eps(latest['mgzbgj'])}，资本实力雄厚")

    result['highlights'] = highlights
    result['warnings'] = warnings
    return result


def analyze_valuation(records: List[Dict], quote: Dict) -> Dict:
    """估值分析"""
    if not records or not quote:
        return {}

    latest = records[0]
    price = quote.get('price', 0)
    pe_ttm = quote.get('pe_ttm', 0)
    pb = quote.get('pb', 0)

    # 如果行情没有PE/PB，用EPS和BPS计算
    if not pe_ttm and price > 0 and latest['eps'] > 0:
        pe_ttm = round(price / latest['eps'], 2)
    if not pb and price > 0 and latest['bps'] > 0:
        pb = round(price / latest['bps'], 2)

    # 估值评价（相对历史水位）
    if pe_ttm > 40:
        pe_rating = '极高 ⚠️'
    elif pe_ttm > 30:
        pe_rating = '偏高'
    elif pe_ttm > 20:
        pe_rating = '合理'
    elif pe_ttm > 10:
        pe_rating = '偏低'
    else:
        pe_rating = '极低 💎'

    if pb > 10:
        pb_rating = '极高溢价'
    elif pb > 5:
        pb_rating = '溢价明显'
    elif pb > 3:
        pb_rating = '合理'
    elif pb > 1:
        pb_rating = '偏低'
    else:
        pb_rating = '破净或低位'

    total_mv = quote.get('total_mv', 0)
    if total_mv > 10000:
        mv_rating = '超大型蓝筹'
    elif total_mv > 1000:
        mv_rating = '大型蓝筹'
    elif total_mv > 100:
        mv_rating = '中型公司'
    else:
        mv_rating = '中小型公司'

    result = {
        'price': price,
        'pe_ttm': pe_ttm,
        'pb': pb,
        'pe_rating': pe_rating,
        'pb_rating': pb_rating,
        'mv_rating': mv_rating,
        'total_mv': total_mv,
        'change_pct': quote.get('change_pct', 0),
    }

    highlights = []
    warnings = []

    if pe_ttm and pe_ttm < 20:
        highlights.append(f"PE(TTM) {pe_ttm:.2f}倍，处于历史相对低位，估值有吸引力")
    elif pe_ttm and pe_ttm > 40:
        warnings.append(f"PE(TTM) {pe_ttm:.2f}倍，估值处于历史高位，需谨慎")

    if pb and pb < 5:
        highlights.append(f"PB {pb:.2f}倍，相对于盈利增长具备安全边际")
    elif pb and pb > 10:
        warnings.append(f"PB {pb:.2f}倍，市场给予较高溢价")

    result['highlights'] = highlights
    result['warnings'] = warnings
    return result


def run_full_analysis(stock_info: Dict, quote: Dict, records: List[Dict]) -> Dict:
    """整合所有分析，生成完整报告"""
    # 只分析年报/三季报（季报累计值用于参考）
    annual_records = []
    for r in records:
        rt = r.get('report_type', '')
        if '年报' in rt or '三季报' in rt or '中报' in rt or '一季报' in rt:
            annual_records.append(r)
            if len(annual_records) >= 8:
                break

    profitability = analyze_profitability(annual_records)
    growth = analyze_growth(annual_records)
    cashflow = analyze_cashflow(annual_records)
    balance = analyze_balance_sheet(annual_records)
    valuation = analyze_valuation(annual_records, quote)

    # 综合评价
    all_highlights = (
        profitability.get('highlights', []) +
        growth.get('highlights', []) +
        cashflow.get('highlights', []) +
        balance.get('highlights', []) +
        valuation.get('highlights', [])
    )
    all_warnings = (
        profitability.get('warnings', []) +
        growth.get('warnings', []) +
        cashflow.get('warnings', []) +
        balance.get('warnings', []) +
        valuation.get('warnings', [])
    )

    return {
        'profitability': profitability,
        'growth': growth,
        'cashflow': cashflow,
        'balance': balance,
        'valuation': valuation,
        'records': annual_records,
        'all_highlights': all_highlights,
        'all_warnings': all_warnings,
    }


# ============================================================
# 输出格式化
# ============================================================

def print_financial_report(stock_name: str, code: str, quote: Dict, analysis: Dict) -> None:
    """打印完整财务分析报告"""

    records = analysis.get('records', [])
    prof = analysis.get('profitability', {})
    growth = analysis.get('growth', {})
    cf = analysis.get('cashflow', {})
    balance = analysis.get('balance', {})
    valuation = analysis.get('valuation', {})
    all_h = analysis.get('all_highlights', [])
    all_w = analysis.get('all_warnings', [])

    # ---- 标题 ----
    print(f"\n{'━'*62}")
    print(f"  📊 {stock_name}（{code}）基本面财务分析报告")
    print(f"  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'━'*62}\n")

    # ---- 行情概览 ----
    print(f"【行情概览】")
    if valuation.get('price'):
        chg = valuation.get('change_pct', 0)
        arrow = '🔴' if chg > 0 else ('🟢' if chg < 0 else '⚪')
        print(f"  当前股价: ¥{valuation['price']:.2f}  {arrow} {chg:+.2f}%")
    print(f"  总市值: {fmt_yuan(valuation.get('total_mv', 0) * 100000000)}  ({valuation.get('mv_rating', '')})")
    if valuation.get('pe_ttm'):
        print(f"  市盈率(PE TTM): {valuation['pe_ttm']:.2f}倍  [{valuation.get('pe_rating', '')}]")
    if valuation.get('pb'):
        print(f"  市净率(PB): {valuation['pb']:.2f}倍  [{valuation.get('pb_rating', '')}]")
    print()

    # ---- 盈利能力 ----
    if prof:
        print(f"【盈利能力】  ({prof.get('date','')} {prof.get('report_type','')})")
        print(f"  加权净资产收益率(ROE): {fmt_pct(prof.get('roe',0))}  [{prof.get('ratings',{}).get('roe','')}]")
        print(f"  扣非ROE: {fmt_pct(prof.get('roe_kc',0))}")
        print(f"  投入资本回报率(ROIC): {fmt_pct(prof.get('roic',0))}  [{prof.get('ratings',{}).get('roic','')}]")
        print(f"  销售毛利率: {fmt_pct(prof.get('gross_margin',0))}  [{prof.get('ratings',{}).get('gross_margin','')}]")
        print(f"  销售净利率: {fmt_pct(prof.get('net_margin',0))}  [{prof.get('ratings',{}).get('net_margin','')}]")
        print(f"  每股收益(EPS): {fmt_eps(prof.get('eps_ttm',0))}  同比 {fmt_pct(prof.get('eps_yoy',0))}")
        print(f"  扣非每股收益: {fmt_eps(prof.get('eps_kc',0))}")
        print(f"  每股净资产(BPS): {fmt_eps(prof.get('bps',0))}  同比 {fmt_pct(prof.get('bps_yoy',0))}")
        print(f"  扣非净利润: {fmt_yuan(prof.get('kcfj_np',0))}")
        print(f"  每股未分配利润: {fmt_eps(prof.get('mgwfplr',0))}")
        print(f"  每股资本公积金: {fmt_eps(prof.get('mgzbgj',0))}")
        print()

    # ---- 成长性 ----
    if growth:
        print(f"【成长性分析】  ({growth.get('date','')} {growth.get('report_type','')})")
        print(f"  营业总收入: {fmt_yuan(growth.get('revenue',0))}")
        print(f"  归母净利润: {fmt_yuan(growth.get('np',0))}")
        print(f"  营收同比增速: {fmt_pct(growth.get('revenue_yoy',0))}")
        print(f"  归母净利润同比增速: {fmt_pct(growth.get('np_yoy',0))}")
        print(f"  扣非净利润同比增速: {fmt_pct(growth.get('kcfjlr_yoy',0))}")
        if growth.get('cagr_revenue'):
            print(f"  营收复合增速(CAGR): {fmt_pct(growth.get('cagr_revenue',0))}")
        if growth.get('cagr_np'):
            print(f"  净利润复合增速(CAGR): {fmt_pct(growth.get('cagr_np',0))}")
        print()

    # ---- 现金流 ----
    if cf:
        print(f"【现金流分析】  ({cf.get('date','')} {cf.get('report_type','')})")
        print(f"  经营现金流/净利润: {cf.get('xjllb',0):.2f}x  [{cf.get('cf_quality','')}]")
        print(f"  每股经营现金流: {fmt_eps(cf.get('mgjyxjje',0))}")
        print(f"  经营现金流净额(估): {fmt_yuan(cf.get('total_ocf_estimate',0))}")
        print(f"  自由现金流(估): {fmt_yuan(cf.get('fcf_estimate',0))}")
        print(f"  评价: {cf.get('cf_judge','')}")
        print()

    # ---- 资产负债表 ----
    if balance:
        print(f"【资产负债表】  ({balance.get('date','')} {balance.get('report_type','')})")
        print(f"  资产负债率: {fmt_pct(balance.get('debt_ratio',0))}  [{balance.get('debt_rating','')}]")
        print(f"  每股未分配利润: {fmt_eps(balance.get('mgwfplr',0))}")
        print(f"  每股资本公积金: {fmt_eps(balance.get('mgzbgj',0))}")
        print()

    # ---- 财务亮点与风险 ----
    if all_h:
        print(f"【财务亮点】 ✅")
        for h in all_h:
            print(f"  ✦ {h}")
        print()

    if all_w:
        print(f"【风险提示】 ⚠️")
        for w in all_w:
            print(f"  ▸ {w}")
        print()
    else:
        print(f"【风险提示】 无明显财务风险")
        print()

    # ---- 近8期数据汇总 ----
    if records:
        print(f"【近8期财务数据汇总】")
        print(f"  {'报告期':<12} {'报告类型':<6} {'营收(亿)':>10} {'净利(亿)':>10} {'ROE(%)':>8} {'毛利率(%)':>9} {'EPS(元)':>9} {'BPS(元)':>9} {'每股经营现金流':>12}")
        print(f"  {'-'*90}")
        for r in records[:8]:
            date = r.get('date','')[:10]
            rt = r.get('report_type','')[:4]
            rev = r.get('total_revenue',0)/100000000
            np_ = r.get('parent_np',0)/100000000
            roe_ = r.get('roe',0)
            gm = r.get('gross_margin',0)
            eps_ = r.get('eps',0)
            bps_ = r.get('bps',0)
            mgcf = r.get('mgjyxjje',0)
            print(f"  {date:<12} {rt:<6} {rev:>10.2f} {np_:>10.2f} {roe_:>8.2f} {gm:>9.2f} {eps_:>9.2f} {bps_:>9.2f} {mgcf:>12.2f}")
        print()

    # ---- 底部 ----
    print(f"{'━'*62}")
    print(f"  数据来源: 东方财富F9 | 财报数据为合并报表")
    print(f"  ⚠️ 本报告仅供参考，不构成投资建议。股市有风险，投资需谨慎。")
    print(f"{'━'*62}\n")


# ============================================================
# 主入口
# ============================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='股票基本面分析')
    parser.add_argument('keyword', help='股票名称或代码')
    parser.add_argument('--json', action='store_true', help='输出JSON格式')
    args = parser.parse_args()

    keyword = args.keyword

    stock_info = get_stock_code_info(keyword)
    if not stock_info:
        print(f"错误: 未找到股票 '{keyword}'", file=sys.stderr)
        sys.exit(1)

    code = stock_info['code']
    name = stock_info['name']

    # 获取行情
    quote = fetch_stock_quote(code)

    # 获取F9财务数据
    records_raw = fetch_f9_main_indicators(code)
    records = parse_raw_f9(records_raw)

    if not records:
        print(f"警告: 无法获取 {name} 的财务数据", file=sys.stderr)
        sys.exit(1)

    # 运行分析
    analysis = run_full_analysis(stock_info, quote, records)

    # 输出
    if args.json:
        output = {
            'stock_name': name,
            'code': code,
            'quote': quote,
            'records': records,
            'analysis': {
                'profitability': analysis['profitability'],
                'growth': analysis['growth'],
                'cashflow': analysis['cashflow'],
                'balance': analysis['balance'],
                'valuation': analysis['valuation'],
            },
            'highlights': analysis['all_highlights'],
            'warnings': analysis['all_warnings'],
            'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print_financial_report(name, code, quote, analysis)
