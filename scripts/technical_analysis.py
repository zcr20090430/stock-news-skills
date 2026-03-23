#!/usr/bin/env python3
"""
技术分析脚本 - 包含量价分析、支撑位/压力位、斐波那契回撤、波浪理论等
"""
import json
import sys
from typing import Dict, List, Tuple, Optional
from datetime import datetime


def calculate_ma(prices: List[float], period: int) -> List[float]:
    """计算移动平均线"""
    result = []
    for i in range(len(prices)):
        if i < period - 1:
            result.append(None)
        else:
            avg = sum(prices[i - period + 1:i + 1]) / period
            result.append(round(avg, 2))
    return result


def calculate_ema(prices: List[float], period: int) -> List[float]:
    """计算指数移动平均线"""
    result = []
    multiplier = 2 / (period + 1)
    for i in range(len(prices)):
        if i == 0:
            result.append(prices[0])
        else:
            ema = (prices[i] * multiplier) + (result[-1] * (1 - multiplier))
            result.append(round(ema, 2))
    return result


def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
    """计算MACD指标"""
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    
    dif = [round(f - s, 4) if f and s else 0 for f, s in zip(ema_fast, ema_slow)]
    dea = calculate_ema(dif, signal)
    macd = [round((d - de) * 2, 4) for d, de in zip(dif, dea)]
    
    return {
        'dif': dif[-5:],  # 最近5天
        'dea': dea[-5:],
        'macd': macd[-5:],
        'latest': {
            'dif': round(dif[-1], 4) if dif else 0,
            'dea': round(dea[-1], 4) if dea else 0,
            'macd': round(macd[-1], 4) if macd else 0
        }
    }


def calculate_rsi(prices: List[float], period: int = 14) -> List[float]:
    """计算RSI指标"""
    if len(prices) < period + 1:
        return []
    
    result = []
    gains = []
    losses = []
    
    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        gains.append(max(0, change))
        losses.append(max(0, -change))
    
    for i in range(len(gains)):
        if i < period - 1:
            result.append(None)
        else:
            avg_gain = sum(gains[i - period + 1:i + 1]) / period
            avg_loss = sum(losses[i - period + 1:i + 1]) / period
            
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            result.append(round(rsi, 2))
    
    return result


def calculate_kdj(klines: List[Dict], period: int = 9) -> Dict:
    """计算KDJ指标"""
    if len(klines) < period:
        return {'k': [], 'd': [], 'j': []}
    
    k_values = []
    d_values = []
    j_values = []
    
    rsv_list = []
    
    for i in range(len(klines)):
        if i < period - 1:
            rsv_list.append(50)  # 默认值
        else:
            period_data = klines[i - period + 1:i + 1]
            high_max = max(d['high'] for d in period_data)
            low_min = min(d['low'] for d in period_data)
            close = klines[i]['close']
            
            if high_max == low_min:
                rsv = 50
            else:
                rsv = (close - low_min) / (high_max - low_min) * 100
            rsv_list.append(rsv)
    
    # 计算K值 (RSV的3日平滑移动平均)
    k = 50
    for rsv in rsv_list:
        k = (2 / 3) * k + (1 / 3) * rsv
        k_values.append(round(k, 2))
    
    # 计算D值 (K的3日平滑移动平均)
    d = 50
    for kv in k_values:
        d = (2 / 3) * d + (1 / 3) * kv
        d_values.append(round(d, 2))
    
    # 计算J值
    j_values = [round(3 * k - 2 * d, 2) for k, d in zip(k_values, d_values)]
    
    return {
        'k': k_values[-5:],
        'd': d_values[-5:],
        'j': j_values[-5:],
        'latest': {
            'k': k_values[-1] if k_values else 0,
            'd': d_values[-1] if d_values else 0,
            'j': j_values[-1] if j_values else 0
        }
    }


def find_support_resistance(klines: List[Dict], lookback: int = 20) -> Dict:
    """
    识别支撑位和压力位
    
    方法：
    1. 局部高低点识别
    2. 成交量确认
    3. 移动平均线作为动态支撑/压力
    """
    if len(klines) < lookback:
        lookback = len(klines)
    
    recent = klines[-lookback:]
    closes = [d['close'] for d in recent]
    highs = [d['high'] for d in recent]
    lows = [d['low'] for d in recent]
    volumes = [d.get('volume', 0) for d in recent]
    
    current_price = closes[-1]
    
    # 1. 找局部高低点
    local_highs = []
    local_lows = []
    
    for i in range(1, len(recent) - 1):
        # 局部高点
        if highs[i] > highs[i - 1] and highs[i] > highs[i + 1]:
            local_highs.append({
                'price': highs[i],
                'date': recent[i]['date'],
                'volume': volumes[i]
            })
        # 局部低点
        if lows[i] < lows[i - 1] and lows[i] < lows[i + 1]:
            local_lows.append({
                'price': lows[i],
                'date': recent[i]['date'],
                'volume': volumes[i]
            })
    
    # 2. 找重要支撑位（当前价格下方的局部低点，按距离排序）
    support_levels = []
    for low in local_lows:
        if low['price'] < current_price:
            support_levels.append({
                'price': low['price'],
                'date': low['date'],
                'volume': low['volume'],
                'distance': round((current_price - low['price']) / current_price * 100, 2),
                'strength': 'strong' if low['volume'] > sum(volumes) / len(volumes) else 'normal'
            })
    
    # 按价格排序（从高到低）
    support_levels.sort(key=lambda x: x['price'], reverse=True)
    
    # 3. 找重要压力位（当前价格上方的局部高点）
    resistance_levels = []
    for high in local_highs:
        if high['price'] > current_price:
            resistance_levels.append({
                'price': high['price'],
                'date': high['date'],
                'volume': high['volume'],
                'distance': round((high['price'] - current_price) / current_price * 100, 2),
                'strength': 'strong' if high['volume'] > sum(volumes) / len(volumes) else 'normal'
            })
    
    # 按价格排序（从低到高）
    resistance_levels.sort(key=lambda x: x['price'])
    
    # 4. 加入均线支撑/压力
    ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else None
    ma60 = sum(closes) / len(closes) if closes else None
    
    ma_supports = []
    ma_resistances = []
    
    if ma20:
        if ma20 < current_price:
            ma_supports.append({
                'price': round(ma20, 2),
                'type': 'MA20',
                'distance': round((current_price - ma20) / current_price * 100, 2)
            })
        else:
            ma_resistances.append({
                'price': round(ma20, 2),
                'type': 'MA20',
                'distance': round((ma20 - current_price) / current_price * 100, 2)
            })
    
    # 5. 整数关口
    price_level = 10 ** (len(str(int(current_price))) - 1)  # 数量级
    int_levels = []
    
    for mult in [0.5, 1, 1.5, 2, 2.5, 3]:
        level = mult * price_level
        if abs(level - current_price) / current_price < 0.15:  # 15%范围内
            if level < current_price:
                int_levels.append({'price': level, 'type': '整数支撑', 'distance': round((current_price - level) / current_price * 100, 2)})
            else:
                int_levels.append({'price': level, 'type': '整数压力', 'distance': round((level - current_price) / current_price * 100, 2)})
    
    return {
        'current_price': current_price,
        'support': support_levels[:5],  # 最近5个支撑位
        'resistance': resistance_levels[:5],  # 最近5个压力位
        'ma_support': ma_supports,
        'ma_resistance': ma_resistances,
        'integer_levels': int_levels,
        'recent_low': min(lows),
        'recent_high': max(highs)
    }


def analyze_elliott_wave(klines: List[Dict]) -> Dict:
    """
    波浪理论分析
    
    识别当前处于波浪的哪个阶段：
    - 上升趋势：1-2-3-4-5浪（推动浪）+ A-B-C浪（调整浪）
    - 下降趋势：A-B-C浪（推动浪）
    
    波浪特征：
    - 第1浪：起步浪，通常是底部开始的第一波上涨
    - 第2浪：回调浪，回调幅度通常为第1浪的50%-61.8%
    - 第3浪：主升浪，通常是最长的一波，涨幅最大
    - 第4浪：调整浪，回调幅度通常为第3浪的38.2%
    - 第5浪：冲顶浪，可能出现量价背离
    
    - A浪：下跌第一波
    - B浪：反弹浪
    - C浪：下跌延续
    """
    if len(klines) < 30:
        return {'error': '数据不足，需要至少30根K线'}
    
    closes = [d['close'] for d in klines]
    highs = [d['high'] for d in klines]
    lows = [d['low'] for d in klines]
    volumes = [d.get('volume', 0) for d in klines]
    dates = [d['date'] for d in klines]
    
    current_price = closes[-1]
    
    # 识别波段高低点
    def find_swing_points(data: List[float], lookback: int = 5) -> List[Dict]:
        """识别波段转折点"""
        points = []
        for i in range(lookback, len(data) - lookback):
            # 高点
            if all(data[i] >= data[i+j] for j in range(-lookback, lookback+1) if j != 0):
                points.append({'index': i, 'price': data[i], 'type': 'high'})
            # 低点
            if all(data[i] <= data[i+j] for j in range(-lookback, lookback+1) if j != 0):
                points.append({'index': i, 'price': data[i], 'type': 'low'})
        return sorted(points, key=lambda x: x['index'])
    
    # 从高点和低点中识别
    high_points = find_swing_points(highs, 3)
    low_points = find_swing_points(lows, 3)
    
    # 合并并按索引排序
    all_points = []
    for p in high_points:
        all_points.append({**p, 'type': 'high'})
    for p in low_points:
        all_points.append({**p, 'type': 'low'})
    all_points.sort(key=lambda x: x['index'])
    
    # 去除连续同类型点（保留极值）
    filtered_points = []
    for p in all_points:
        if not filtered_points:
            filtered_points.append(p)
        elif filtered_points[-1]['type'] != p['type']:
            filtered_points.append(p)
        else:
            # 保留更极端的
            if p['type'] == 'high' and p['price'] > filtered_points[-1]['price']:
                filtered_points[-1] = p
            elif p['type'] == 'low' and p['price'] < filtered_points[-1]['price']:
                filtered_points[-1] = p
    
    # 判断大趋势
    first_price = closes[0]
    last_price = closes[-1]
    max_price = max(highs)
    min_price = min(lows)
    max_idx = highs.index(max_price)
    min_idx = lows.index(min_price)
    
    # 判断当前处于什么趋势
    is_uptrend = max_idx > min_idx  # 高点在后，上升趋势
    
    # 波浪分析
    wave_analysis = {
        'trend': 'up' if is_uptrend else 'down',
        'current_price': current_price,
        'wave_points': [],
        'current_wave': None,
        'wave_count': None,
        'prediction': {}
    }
    
    # 记录关键点位
    key_points = []
    for p in filtered_points[-10:]:  # 取最近10个转折点
        key_points.append({
            'date': dates[p['index']],
            'price': p['price'],
            'type': p['type'],
            'index': p['index']
        })
    wave_analysis['wave_points'] = key_points
    
    # 尝试识别当前波浪位置
    if len(key_points) >= 3:
        recent_points = key_points[-3:]
        
        if is_uptrend:
            # 上升趋势分析
            if recent_points[-1]['type'] == 'high':
                # 最近是高点，可能处于调整浪开始
                if len(key_points) >= 5:
                    # 检查是否完成5浪
                    wave_5_high = key_points[-1]['price']
                    wave_3_high = None
                    wave_1_high = None
                    for i in range(len(key_points)-2, -1, -1):
                        if key_points[i]['type'] == 'high':
                            if wave_3_high is None:
                                wave_3_high = key_points[i]['price']
                            elif wave_1_high is None:
                                wave_1_high = key_points[i]['price']
                                break
                    
                    if wave_3_high and wave_1_high:
                        if wave_3_high > wave_5_high and wave_3_high > wave_1_high:
                            wave_analysis['current_wave'] = '可能处于A浪（下跌开始）'
                            wave_analysis['wave_count'] = 'A'
                        elif wave_5_high > wave_3_high:
                            wave_analysis['current_wave'] = '可能处于第5浪顶部'
                            wave_analysis['wave_count'] = '5'
                else:
                    wave_analysis['current_wave'] = '上升趋势中的高点'
                    wave_analysis['wave_count'] = '上升'
            
            else:
                # 最近是低点，可能处于推动浪中
                prev_high = None
                for p in reversed(key_points[:-1]):
                    if p['type'] == 'high':
                        prev_high = p
                        break
                
                if prev_high:
                    # 检查是否突破前高
                    if current_price > prev_high['price'] * 0.98:
                        wave_analysis['current_wave'] = '可能处于第3浪（主升浪）'
                        wave_analysis['wave_count'] = '3'
                    else:
                        wave_analysis['current_wave'] = '可能处于第1浪或第5浪'
                        wave_analysis['wave_count'] = '1或5'
        else:
            # 下降趋势分析
            if recent_points[-1]['type'] == 'low':
                wave_analysis['current_wave'] = '可能处于C浪（下跌延续）'
                wave_analysis['wave_count'] = 'C'
            else:
                wave_analysis['current_wave'] = '可能处于B浪反弹'
                wave_analysis['wave_count'] = 'B'
    
    # 波浪比例分析
    if len(key_points) >= 4:
        # 计算各波段幅度
        waves = []
        for i in range(1, len(key_points)):
            wave_move = {
                'from': key_points[i-1]['price'],
                'to': key_points[i]['price'],
                'change': key_points[i]['price'] - key_points[i-1]['price'],
                'change_pct': (key_points[i]['price'] - key_points[i-1]['price']) / key_points[i-1]['price'] * 100,
                'type': 'up' if key_points[i]['type'] == 'high' else 'down'
            }
            waves.append(wave_move)
        
        wave_analysis['wave_moves'] = waves[-5:]  # 最近5个波段
        
        # 波浪比例验证（艾略特波浪理论）
        # 第3浪通常是第1浪的1.618倍
        # 第5浪通常等于第1浪
        if len(waves) >= 3:
            wave_analysis['wave_ratios'] = {
                'note': '波浪比例分析仅供参考'
            }
    
    # 预测
    if wave_analysis.get('wave_count'):
        wc = wave_analysis['wave_count']
        
        if wc == '1或5':
            wave_analysis['prediction'] = {
                'short_term': '观察是否能突破前高确认浪型',
                'target': '若为第1浪，后续有第3浪主升',
                'risk': '若为第5浪，注意见顶风险'
            }
        elif wc == '3':
            wave_analysis['prediction'] = {
                'short_term': '主升浪中，涨幅可能最大',
                'target': '第1浪幅度的1.618倍位置',
                'risk': '第4浪回调风险'
            }
        elif wc == '5':
            wave_analysis['prediction'] = {
                'short_term': '冲顶阶段，注意量价背离',
                'target': '接近阶段性顶部',
                'risk': 'A浪下跌风险较高'
            }
        elif wc == 'A':
            wave_analysis['prediction'] = {
                'short_term': '下跌开始，可能有B浪反弹',
                'target': '支撑位附近',
                'risk': 'C浪下跌风险'
            }
        elif wc == 'B':
            wave_analysis['prediction'] = {
                'short_term': '反弹阶段，通常较弱',
                'target': '前期高点附近',
                'risk': '反弹后C浪下跌'
            }
        elif wc == 'C':
            wave_analysis['prediction'] = {
                'short_term': '下跌延续，寻找新支撑',
                'target': '前一循环低点',
                'risk': '下跌趋势未结束'
            }
    
    return wave_analysis


def calculate_fibonacci(klines: List[Dict], trend: str = 'up') -> Dict:
    """
    计算斐波那契回撤位
    
    trend: 'up' - 上升趋势回撤, 'down' - 下降趋势反弹
    """
    # 找最近一段明显趋势
    lookback = min(30, len(klines))
    recent = klines[-lookback:]
    
    highs = [d['high'] for d in recent]
    lows = [d['low'] for d in recent]
    
    # 找波段高低点
    swing_high = max(highs)
    swing_high_idx = highs.index(swing_high)
    swing_low = min(lows)
    swing_low_idx = lows.index(swing_low)
    
    current_price = recent[-1]['close']
    
    fib_levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
    fib_names = ['起点', '23.6%', '38.2%', '50%', '61.8%', '78.6%', '终点']
    
    levels = []
    
    if trend == 'up':
        # 上升趋势：从低点到高点
        diff = swing_high - swing_low
        for level, name in zip(fib_levels, fib_names):
            price = swing_low + diff * level
            distance = round((current_price - price) / current_price * 100, 2)
            levels.append({
                'level': name,
                'price': round(price, 2),
                'distance_pct': distance,
                'position': '支撑' if price < current_price else '压力'
            })
    else:
        # 下降趋势：从高点到低点
        diff = swing_high - swing_low
        for level, name in zip(fib_levels, fib_names):
            price = swing_high - diff * level
            distance = round((price - current_price) / current_price * 100, 2)
            levels.append({
                'level': name,
                'price': round(price, 2),
                'distance_pct': distance,
                'position': '压力' if price > current_price else '支撑'
            })
    
    return {
        'swing_high': swing_high,
        'swing_high_date': recent[swing_high_idx]['date'],
        'swing_low': swing_low,
        'swing_low_date': recent[swing_low_idx]['date'],
        'current_price': current_price,
        'trend': '上升' if trend == 'up' else '下降',
        'levels': levels
    }


def analyze_volume_price(klines: List[Dict]) -> Dict:
    """
    量价分析
    """
    if len(klines) < 5:
        return {'error': '数据不足'}
    
    recent = klines[-10:]  # 最近10天
    analysis = []
    
    for i in range(1, len(recent)):
        prev = recent[i - 1]
        curr = recent[i]
        
        price_change = (curr['close'] - prev['close']) / prev['close'] * 100
        vol_change = (curr['volume'] - prev['volume']) / prev['volume'] * 100 if prev['volume'] else 0
        
        # 判断量价关系
        if price_change > 2 and vol_change > 50:
            pattern = '放量上涨'
            signal = '看多'
        elif price_change > 0 and vol_change < 0:
            pattern = '缩量上涨'
            signal = '上涨乏力'
        elif price_change < -2 and vol_change > 50:
            pattern = '放量下跌'
            signal = '看空'
        elif price_change < 0 and vol_change < 0:
            pattern = '缩量下跌'
            signal = '下跌缓和'
        elif abs(price_change) < 0.5 and vol_change > 30:
            pattern = '放量横盘'
            signal = '变盘前兆'
        else:
            pattern = '正常波动'
            signal = '中性'
        
        analysis.append({
            'date': curr['date'],
            'price_change': round(price_change, 2),
            'volume_change': round(vol_change, 2),
            'pattern': pattern,
            'signal': signal
        })
    
    # 整体量价趋势判断
    latest = analysis[-1]
    
    # 统计最近5天的量价形态
    recent_patterns = [a['pattern'] for a in analysis[-5:]]
    bullish_count = sum(1 for p in recent_patterns if '上涨' in p and '缩量' not in p)
    bearish_count = sum(1 for p in recent_patterns if '下跌' in p and '缩量' not in p)
    
    if bullish_count > bearish_count + 1:
        trend_signal = '偏多'
    elif bearish_count > bullish_count + 1:
        trend_signal = '偏空'
    else:
        trend_signal = '震荡'
    
    return {
        'daily_analysis': analysis,
        'latest_pattern': latest['pattern'],
        'latest_signal': latest['signal'],
        'trend_signal': trend_signal,
        'volume_trend': '放量' if sum(1 for a in analysis[-3:] if a['volume_change'] > 20) >= 2 else '缩量'
    }


def generate_technical_report(klines: List[Dict]) -> Dict:
    """
    生成完整的技术分析报告
    """
    closes = [d['close'] for d in klines]
    
    # 计算各项指标
    ma5 = calculate_ma(closes, 5)
    ma10 = calculate_ma(closes, 10)
    ma20 = calculate_ma(closes, 20)
    ma60 = calculate_ma(closes, min(60, len(closes)))
    
    macd = calculate_macd(closes)
    rsi = calculate_rsi(closes)
    kdj = calculate_kdj(klines)
    
    support_resistance = find_support_resistance(klines)
    
    # 判断趋势方向
    current_price = closes[-1]
    ma_status = []
    
    if ma5[-1] and ma10[-1]:
        if ma5[-1] > ma10[-1]:
            ma_status.append('短期均线多头排列')
        else:
            ma_status.append('短期均线空头排列')
    
    if ma20[-1]:
        if current_price > ma20[-1]:
            ma_status.append('股价站上20日均线')
        else:
            ma_status.append('股价跌破20日均线')
    
    # MACD信号
    macd_signal = []
    if macd['latest']['macd'] > 0:
        macd_signal.append('MACD红柱')
    else:
        macd_signal.append('MACD绿柱')
    
    if len(macd['dif']) >= 2:
        if macd['dif'][-1] > macd['dif'][-2]:
            macd_signal.append('DIF上升')
        else:
            macd_signal.append('DIF下降')
    
    # RSI信号
    rsi_signal = ''
    if rsi:
        latest_rsi = rsi[-1]
        if latest_rsi > 80:
            rsi_signal = '超买区(>80)，注意回调风险'
        elif latest_rsi > 60:
            rsi_signal = '强势区(60-80)'
        elif latest_rsi < 20:
            rsi_signal = '超卖区(<20)，可能反弹'
        elif latest_rsi < 40:
            rsi_signal = '弱势区(20-40)'
        else:
            rsi_signal = '中性区(40-60)'
    
    # KDJ信号
    kdj_signal = ''
    if kdj['latest']:
        k, d, j = kdj['latest']['k'], kdj['latest']['d'], kdj['latest']['j']
        if k > 80 and d > 80:
            kdj_signal = f'KDJ超买(K={k}, D={d})，注意风险'
        elif k < 20 and d < 20:
            kdj_signal = f'KDJ超卖(K={k}, D={d})，可能反弹'
        elif k > d:
            kdj_signal = f'KDJ金叉趋势(K={k}, D={d})'
        else:
            kdj_signal = f'KDJ死叉趋势(K={k}, D={d})'
    
    # 量价分析
    volume_price = analyze_volume_price(klines)
    
    # 斐波那契
    fib = calculate_fibonacci(klines, trend='up' if closes[-1] > closes[-10] else 'down')
    
    # 波浪理论分析
    elliott_wave = analyze_elliott_wave(klines)
    
    return {
        'current_price': current_price,
        'date': klines[-1]['date'],
        'moving_averages': {
            'ma5': ma5[-1] if ma5 and ma5[-1] else None,
            'ma10': ma10[-1] if ma10 and ma10[-1] else None,
            'ma20': ma20[-1] if ma20 and ma20[-1] else None,
            'ma60': ma60[-1] if ma60 and ma60[-1] else None,
            'status': ma_status
        },
        'macd': {
            **macd,
            'signal': macd_signal
        },
        'rsi': {
            'value': rsi[-1] if rsi else None,
            'signal': rsi_signal
        },
        'kdj': {
            **kdj,
            'signal': kdj_signal
        },
        'support_resistance': support_resistance,
        'fibonacci': fib,
        'elliott_wave': elliott_wave,
        'volume_price': volume_price,
        'summary': {
            'trend': '上涨' if ma20 and ma20[-1] and current_price > ma20[-1] else '下跌' if ma20 and ma20[-1] and current_price < ma20[-1] else '震荡',
            'strength': '强' if rsi and rsi[-1] and rsi[-1] > 60 else '弱' if rsi and rsi[-1] and rsi[-1] < 40 else '中性',
            'volume_trend': volume_price.get('volume_trend', '未知'),
            'main_signal': volume_price.get('trend_signal', '中性'),
            'wave_position': elliott_wave.get('current_wave', '未知')
        }
    }


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python technical_analysis.py <klines_json_file>")
        print("       python technical_analysis.py -d '<json_data>'")
        sys.exit(1)
    
    if sys.argv[1] == '-d':
        klines = json.loads(sys.argv[2])
    else:
        with open(sys.argv[1], 'r') as f:
            klines = json.load(f)
    
    report = generate_technical_report(klines)
    print(json.dumps(report, ensure_ascii=False, indent=2))
