from collections import defaultdict
import csv
import random
from datetime import datetime, timedelta
import os
import logging
import requests

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 大乐透、双色球和七星彩的开奖数据网址
url_dlt = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry?gameNo=85&provinceId=0&pageSize=100&isVerify=1&pageNo=1"
url_ssq = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice?name=ssq&issueCount=&issueStart=&issueEnd=&dayStart=&dayEnd=&pageNo=1&pageSize=100&week=&systemType=PC"
url_qxc = "https://webapi.sporttery.cn/gateway/lottery/getHistoryPageListV1.qry?gameNo=04&provinceId=0&pageSize=100&isVerify=1&pageNo=1"

# CSV文件路径
data_dir = os.path.join("message", "data")  # 数据文件夹
csv_generated_dlt = os.path.join(data_dir, "generated_dlt.csv")
csv_generated_ssq = os.path.join(data_dir, "generated_ssq.csv")
csv_generated_qxc = os.path.join(data_dir, "generated_qxc.csv")


# 根据年份生成文件路径
def get_year_csv_path(base_filename, year):
    """
    根据基础文件名和年份生成 CSV 文件路径。
    :param base_filename: 基础文件名（如 "dlt_results"）
    :param year: 年份（如 2023）
    :return: 完整的文件路径（如 "message/data/dlt_results_2023.csv"）
    """
    return os.path.join(data_dir, f"{base_filename}_{year}.csv")


# 确保数据文件夹存在
def ensure_data_dir_exists():
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)


# 确保CSV文件存在，如果不存在则创建
def ensure_csv_exists(filename, header):
    ensure_data_dir_exists()  # 确保数据文件夹存在
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(header)


# 通用的请求和解析彩票数据的方法
def fetch_and_parse_lottery(url, lottery_type):
    """
    通用的请求和解析彩票数据的方法。
    :param url: 彩票数据的 API URL
    :param lottery_type: 彩票类型（用于日志记录）
    :return: 解析后的彩票数据列表
    """
    try:
        # 发送请求
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Referer": "https://static.sporttery.cn/",
            "X-Forwarded-For": "47.95.47.253"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 检查请求是否成功

        # 解析数据
        data = response.json()
        results = []

        # 获取开奖数据列表
        items = data["value"]["list"]
        for item in items:
            issue = item["lotteryDrawNum"]  # 开奖期数
            date = item["lotteryDrawTime"]  # 开奖时间
            numbers = item["lotteryDrawResult"].split()  # 开奖号码
            if lottery_type == "大乐透" and len(numbers) >= 7:  # 大乐透需要 7 个号码
                front = numbers[:5]  # 前区（红球）
                back = numbers[5:]  # 后区（篮球）
                results.append([issue, date] + front + back)
            elif lottery_type == "七星彩" and len(numbers) == 7:  # 七星彩需要 7 个号码
                front = numbers[:6]  # 前区
                back = numbers[6]  # 后区
                results.append([issue, date] + front + [back])

        return results
    except requests.exceptions.RequestException as e:
        logger.error(f"请求 {lottery_type} 数据失败: {e}")
        return None


# 双色球数据爬取方法
def fetch_and_parse_ssq(url):
    """
    通用的请求和解析双色球数据的方法。
    :param url: 双色球数据的 API URL
    :return: 解析后的双色球数据列表
    """
    try:
        # 发送请求
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "X-Forwarded-For": "47.95.47.253"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 检查请求是否成功

        # 解析数据
        data = response.json()
        results = []

        # 获取开奖数据列表
        items = data.get("result", [])
        for item in items:
            issue = item.get("code")  # 开奖期数
            date = item.get("date")  # 开奖时间
            red = item.get("red", "")  # 红球号码（字符串）
            blue = item.get("blue")  # 蓝球号码

            # 确保所有字段都存在
            if issue and date and red and blue:
                # 将红球号码按逗号分割为列表
                red_numbers = red.split(",")
                # 将结果存储为 [期数, 日期, 红球1, 红球2, 红球3, 红球4, 红球5, 红球6, 蓝球]
                results.append([issue, date] + red_numbers + [blue])

        return results
    except requests.exceptions.RequestException as e:
        logger.error(f"请求双色球数据失败: {e}")
        return None


# 保存数据到CSV文件
def save_to_csv(data, base_filename, header):
    # 按年份分组保存数据
    year_to_data = defaultdict(list)
    for row in data:
        date = row[1]  # 开奖日期
        year = date.split("-")[0]  # 提取年份
        year_to_data[year].append(row)

    # 保存到对应年份的文件
    for year, year_data in year_to_data.items():
        filename = get_year_csv_path(base_filename, year)
        ensure_csv_exists(filename, header)

        # 读取已存在的期数
        existing_issues = set()
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                next(reader)  # 跳过表头
                for row in reader:
                    existing_issues.add(row[0])  # 期数作为唯一标识

        # 只保存未存在的数据
        new_data = [row for row in year_data if row[0] not in existing_issues]
        if new_data:
            with open(filename, 'a', encoding='utf-8', newline='') as file:
                writer = csv.writer(file)
                writer.writerows(new_data)


# 读取指定年份的数据
def read_year_data(base_filename, year):
    filename = get_year_csv_path(base_filename, year)
    if not os.path.exists(filename):
        return []
    with open(filename, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # 跳过表头
        return list(reader)


# 获取最近30期数据
def get_recent_30_data(base_filename, target_year):
    # 读取当前年份的数据
    data = read_year_data(base_filename, target_year)
    if len(data) >= 30:
        return data  # 如果当前年份数据足够，直接返回

    # 如果当前年份数据不足30条，从上一年的数据中补充
    previous_year = str(int(target_year) - 1)
    previous_data = read_year_data(base_filename, previous_year)
    if previous_data:
        # 从上一年的数据中取最后 (30 - len(data)) 条
        needed = 30 - len(data)
        data.extend(previous_data[-needed:])

    return data


# 分析号码概率
def analyze_number_probability(data, front_range=(1, 35), back_range=(1, 12)):
    """
    分析历史数据中号码的概率分布，包括多维度走势分析。
    :param data: 历史开奖数据
    :param front_range: 前区号码范围，如(1, 35)表示1-35
    :param back_range: 后区号码范围，如(1, 12)表示1-12
    :return: 前区和后区号码的概率分布
    """
    # 初始化前区和后区号码的计数器
    front_counter = {num: 0 for num in range(front_range[0], front_range[1] + 1)}
    back_counter = {num: 0 for num in range(back_range[0], back_range[1] + 1)}
    
    # 初始化遗漏值计数器
    front_missing = {num: 0 for num in range(front_range[0], front_range[1] + 1)}
    back_missing = {num: 0 for num in range(back_range[0], back_range[1] + 1)}
    
    # 初始化最近30期的热号计数（如果历史数据不足30期，则使用所有可用数据）
    recent_draws = min(30, len(data))  # 最近30期或全部数据（如果少于30期）
    recent_front_counter = {num: 0 for num in range(front_range[0], front_range[1] + 1)}
    recent_back_counter = {num: 0 for num in range(back_range[0], back_range[1] + 1)}
    
    # 初始化连号统计
    consecutive_front_counter = {num: 0 for num in range(front_range[0], front_range[1])}  # 统计num和num+1同时出现的次数
    
    # 初始化重号统计（上期出现，本期也出现）
    repeat_front_counter = {num: 0 for num in range(front_range[0], front_range[1] + 1)}
    repeat_back_counter = {num: 0 for num in range(back_range[0], back_range[1] + 1)}
    
    # 初始化质数统计
    prime_numbers = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]  # 35以内的质数
    prime_ratio_list = []  # 每期质数比例
    
    # 初始化和值统计
    sum_values_front = []  # 前区和值列表
    sum_values_back = []   # 后区和值列表
    
    # 初始化跨度统计（最大号码与最小号码的差值）
    span_values_front = []  # 前区跨度列表
    
    # 初始化周期性统计
    weekday_front_stats = {0: {}, 1: {}, 2: {}, 3: {}, 4: {}, 5: {}, 6: {}}  # 按周几统计（0-6对应周一到周日）
    for day in weekday_front_stats:
        weekday_front_stats[day] = {num: 0 for num in range(front_range[0], front_range[1] + 1)}
    
    # 统计历史数据中号码的出现次数
    prev_front_nums = []  # 上一期前区号码
    prev_back_nums = []   # 上一期后区号码
    
    for i, draw in enumerate(data):
        # 提取当期前区和后区号码
        current_front = []
        for num in draw[2:-2]:
            try:
                num_int = int(num)
                if front_range[0] <= num_int <= front_range[1]:
                    current_front.append(num_int)
            except ValueError:
                # 跳过无法转换为整数的值（如日期）
                continue
        current_back = []
        for num in draw[-2:]:
            try:
                num_int = int(num)
                if back_range[0] <= num_int <= back_range[1]:
                    current_back.append(num_int)
            except ValueError:
                # 跳过无法转换为整数的值
                continue
        
        # 提取当期日期
        date_str = draw[1]
        # 移除可能的额外内容，只保留YYYY-MM-DD部分
        if '(' in date_str:  # 处理类似 "2025-01-26(日)" 的格式
            date_str = date_str.split('(')[0]
        elif len(date_str) > 10:  # 标准日期格式YYYY-MM-DD长度为10
            date_str = date_str[:10]
        draw_date = datetime.strptime(date_str, "%Y-%m-%d")
        weekday = draw_date.weekday()
        
        # 更新总体计数
        for num in current_front:
            front_counter[num] += 1
            # 更新周几统计
            weekday_front_stats[weekday][num] += 1
        
        for num in current_back:
            back_counter[num] += 1
        
        # 更新最近30期的热号计数
        if i < recent_draws:
            for num in current_front:
                recent_front_counter[num] += 1
            for num in current_back:
                recent_back_counter[num] += 1
        
        # 更新遗漏值计数
        for num in range(front_range[0], front_range[1] + 1):
            if num in current_front:
                front_missing[num] = 0  # 当期出现，遗漏值重置为0
            else:
                front_missing[num] += 1  # 当期未出现，遗漏值+1
        
        for num in range(back_range[0], back_range[1] + 1):
            if num in current_back:
                back_missing[num] = 0  # 当期出现，遗漏值重置为0
            else:
                back_missing[num] += 1  # 当期未出现，遗漏值+1
        
        # 更新连号统计
        sorted_front = sorted(current_front)
        for j in range(len(sorted_front) - 1):
            if sorted_front[j] + 1 == sorted_front[j + 1]:  # 检测连号
                consecutive_front_counter[sorted_front[j]] += 1
        
        # 更新重号统计
        if prev_front_nums:
            for num in current_front:
                if num in prev_front_nums:
                    repeat_front_counter[num] += 1
        
        if prev_back_nums:
            for num in current_back:
                if num in prev_back_nums:
                    repeat_back_counter[num] += 1
        
        # 更新质数比例
        prime_count = sum(1 for num in current_front if num in prime_numbers)
        prime_ratio = prime_count / len(current_front) if current_front else 0
        prime_ratio_list.append(prime_ratio)
        
        # 更新和值统计
        sum_values_front.append(sum(current_front))
        sum_values_back.append(sum(current_back))
        
        # 更新跨度统计
        if current_front:
            span_values_front.append(max(current_front) - min(current_front))
        
        # 保存当前号码作为下一期的上期号码
        prev_front_nums = current_front
        prev_back_nums = current_back
    
    # 计算基础概率（历史频率）
    front_total = sum(front_counter.values()) or 1  # 避免除以零
    back_total = sum(back_counter.values()) or 1
    front_base_prob = {num: count / front_total for num, count in front_counter.items()}
    back_base_prob = {num: count / back_total for num, count in back_counter.items()}
    
    # 计算热号权重（最近30期的频率）
    recent_front_total = sum(recent_front_counter.values()) or 1
    recent_back_total = sum(recent_back_counter.values()) or 1
    front_hot_weight = {num: count / recent_front_total for num, count in recent_front_counter.items()}
    back_hot_weight = {num: count / recent_back_total for num, count in recent_back_counter.items()}
    
    # 计算遗漏值权重（遗漏越多，权重越大）
    max_front_missing = max(front_missing.values()) or 1
    max_back_missing = max(back_missing.values()) or 1
    front_missing_weight = {num: miss / max_front_missing for num, miss in front_missing.items()}
    back_missing_weight = {num: miss / max_back_missing for num, miss in back_missing.items()}
    
    # 计算连号权重
    consecutive_total = sum(consecutive_front_counter.values()) or 1
    consecutive_weight = {num: count / consecutive_total for num, count in consecutive_front_counter.items()}
    
    # 计算重号权重
    repeat_front_total = sum(repeat_front_counter.values()) or 1
    repeat_back_total = sum(repeat_back_counter.values()) or 1
    repeat_front_weight = {num: count / repeat_front_total for num, count in repeat_front_counter.items()}
    repeat_back_weight = {num: count / repeat_back_total for num, count in repeat_back_counter.items()}
    
    # 分析号码组合特征（奇偶比例、大小比例）
    odd_even_ratios = []  # 奇偶比例列表
    high_low_ratios = []  # 大小比例列表（大：大于等于中间值，小：小于中间值）
    front_mid = (front_range[0] + front_range[1]) / 2  # 前区中间值
    
    for draw in data:
        current_front = []
        for num in draw[2:-2]:
            try:
                num_int = int(num)
                if front_range[0] <= num_int <= front_range[1]:
                    current_front.append(num_int)
            except ValueError:
                # 跳过无法转换为整数的值（如日期）
                continue
        
        # 计算奇偶比例
        odd_count = sum(1 for num in current_front if num % 2 == 1)  # 奇数个数
        even_count = len(current_front) - odd_count  # 偶数个数
        odd_even_ratios.append(odd_count / len(current_front) if len(current_front) > 0 else 0.5)
        
        # 计算大小比例
        high_count = sum(1 for num in current_front if num >= front_mid)  # 大号个数
        low_count = len(current_front) - high_count  # 小号个数
        high_low_ratios.append(high_count / len(current_front) if len(current_front) > 0 else 0.5)
    
    # 计算平均奇偶比例和大小比例
    avg_odd_ratio = sum(odd_even_ratios) / len(odd_even_ratios) if odd_even_ratios else 0.5
    avg_high_ratio = sum(high_low_ratios) / len(high_low_ratios) if high_low_ratios else 0.5
    
    # 计算平均和值和跨度
    avg_sum_front = sum(sum_values_front) / len(sum_values_front) if sum_values_front else 0
    avg_sum_back = sum(sum_values_back) / len(sum_values_back) if sum_values_back else 0
    avg_span_front = sum(span_values_front) / len(span_values_front) if span_values_front else 0
    
    # 计算平均质数比例
    avg_prime_ratio = sum(prime_ratio_list) / len(prime_ratio_list) if prime_ratio_list else 0.3
    
    # 获取当前日期的周几
    current_weekday = datetime.today().weekday()
    
    # 计算周几权重
    weekday_total = sum(weekday_front_stats[current_weekday].values()) or 1
    weekday_weight = {num: count / weekday_total for num, count in weekday_front_stats[current_weekday].items()}
    
    # 综合计算最终概率（多维度分析）
    front_prob = {}
    back_prob = {}
    
    for num in range(front_range[0], front_range[1] + 1):
        # 基础概率权重
        base_prob = 0.3 * front_base_prob[num]
        
        # 热号权重
        hot_prob = 0.1 * front_hot_weight[num]
        
        # 遗漏值权重
        missing_prob = 0.1 * front_missing_weight[num]
        
        # 连号权重（对num和num-1进行检查）
        consec_prob = 0.05 * (consecutive_weight.get(num, 0) + consecutive_weight.get(num-1, 0)) / 2 if num > front_range[0] else 0.05 * consecutive_weight.get(num, 0)
        
        # 重号权重
        repeat_prob = 0.05 * repeat_front_weight.get(num, 0)
        
        # 奇偶特征调整
        is_odd = num % 2 == 1
        odd_adjust = 1.1 if (is_odd and avg_odd_ratio > 0.5) or (not is_odd and avg_odd_ratio < 0.5) else 0.9
        
        # 大小特征调整
        is_high = num >= front_mid
        high_adjust = 1.1 if (is_high and avg_high_ratio > 0.5) or (not is_high and avg_high_ratio < 0.5) else 0.9
        
        # 质合特征调整
        is_prime = num in prime_numbers
        prime_adjust = 1.1 if (is_prime and avg_prime_ratio > 0.3) or (not is_prime and avg_prime_ratio < 0.3) else 0.9
        
        # 和值与跨度特征调整
        sum_span_adjust = 1.0  # 默认不调整
        
        # 周几特征权重
        weekday_prob = 0.1 * weekday_weight.get(num, 0)
        
        # 组合所有特征
        feature_adjust = 0.1 * (odd_adjust * high_adjust * prime_adjust * sum_span_adjust - 1.0)
        
        # 计算最终概率
        front_prob[num] = base_prob + hot_prob + missing_prob + consec_prob + repeat_prob + weekday_prob + feature_adjust
    
    for num in range(back_range[0], back_range[1] + 1):
        # 后区概率计算（多维度分析）
        base_prob = 0.4 * back_base_prob[num]
        hot_prob = 0.2 * back_hot_weight[num]
        missing_prob = 0.2 * back_missing_weight[num]
        repeat_prob = 0.1 * repeat_back_weight.get(num, 0)
        
        # 计算最终概率
        back_prob[num] = base_prob + hot_prob + missing_prob + repeat_prob
    
    # 归一化概率分布
    front_total_prob = sum(front_prob.values()) or 1
    back_total_prob = sum(back_prob.values()) or 1
    front_prob = {num: prob / front_total_prob for num, prob in front_prob.items()}
    back_prob = {num: prob / back_total_prob for num, prob in back_prob.items()}
    
    # 输出分析结果
    print("\n===== 号码走势分析 =====")
    print(f"基本走势: 前区热门号码: {sorted([num for num, prob in front_base_prob.items() if prob > 1.5/len(front_base_prob)])}")
    print(f"红球走势: 最近遗漏值高的号码: {sorted([num for num, miss in front_missing.items() if miss > 0.7*max_front_missing])}")
    print(f"篮球走势: 后区热门号码: {sorted([num for num, prob in back_base_prob.items() if prob > 1.0/len(back_base_prob)])}")
    print(f"连号走势: 连号概率较高的起始号码: {sorted([num for num, weight in consecutive_weight.items() if weight > 1.5/len(consecutive_weight)])}")
    print(f"重号走势: 重复出现概率高的号码: {sorted([num for num, weight in repeat_front_weight.items() if weight > 1.5/len(repeat_front_weight)])}")
    print(f"大小走势: 大号比例趋势: {avg_high_ratio:.2f} (>0.5表示大号占优)")
    print(f"奇偶走势: 奇数比例趋势: {avg_odd_ratio:.2f} (>0.5表示奇数占优)")
    print(f"跨度走势: 平均跨度值: {avg_span_front:.2f}")
    print(f"和值走势: 前区平均和值: {avg_sum_front:.2f}, 后区平均和值: {avg_sum_back:.2f}")
    print(f"质合走势: 质数比例趋势: {avg_prime_ratio:.2f} (>0.3表示质数占优)")
    print(f"周期走势: 今天是周{['一','二','三','四','五','六','日'][current_weekday]}, 历史上这天的热门号码: {sorted([num for num, count in weekday_front_stats[current_weekday].items() if count > 0])[:5]}")
    print("=====================\n")
    
    return front_prob, back_prob

# 生成大乐透号码
def generate_dlt_numbers(front_prob, back_prob, generated_data, front_range=(1, 35), back_range=(1, 12)):
    # 读取已生成的大乐透号码
    existing_numbers = set()
    for row in generated_data:
        if not row:  # 跳过空行
            continue
        try:
            if len(row) < 3:
                raise ValueError(f"数据格式错误：行数据不足 3 个元素，当前行：{row}")
            front = tuple(row[1].split(','))  # 红球（保留字符串格式）
            back = tuple(row[2].split(','))   # 篮球（保留字符串格式）
            existing_numbers.add((front, back))
        except (IndexError, ValueError) as e:
            print(f"数据解析错误：{row}，错误信息：{e}")
            continue  # 跳过错误数据，继续处理下一行

    # 生成新号码的逻辑
    while True:
        front_numbers = list(front_prob.keys())
        front_weights = list(front_prob.values())
        front = random.choices(front_numbers, weights=front_weights, k=5)
        front = sorted(list(set(front)))
        if len(front) == 5:
            front = [f"{num:02d}" for num in front]  # 确保是两位数格式
            break

    while True:
        back_numbers = list(back_prob.keys())
        back_weights = list(back_prob.values())
        back = random.choices(back_numbers, weights=back_weights, k=2)
        back = sorted(list(set(back)))
        if len(back) == 2:
            back = [f"{num:02d}" for num in back]  # 确保是两位数格式
            break

    # 检查是否与已生成的号码重复
    if (tuple(front), tuple(back)) not in existing_numbers:
        return front, back
    else:
        return generate_dlt_numbers(front_prob, back_prob, generated_data, front_range, back_range)


# 生成双色球号码
def generate_ssq_numbers(front_prob, back_prob, generated_data, front_range=(1, 33), back_range=(1, 16)):
    # 读取已生成的双色球号码
    existing_numbers = set()
    for row in generated_data:
        if not row:  # 跳过空行
            continue
        try:
            if len(row) < 3:
                raise ValueError(f"数据格式错误：行数据不足 3 个元素，当前行：{row}")
            front = tuple(row[1].split(','))  # 红球（保留字符串格式）
            back = tuple(row[2].split(','))   # 篮球（保留字符串格式）
            existing_numbers.add((front, back))
        except (IndexError, ValueError) as e:
            print(f"数据解析错误：{row}，错误信息：{e}")
            continue  # 跳过错误数据，继续处理下一行

    # 生成新号码的逻辑
    while True:
        front_numbers = list(front_prob.keys())
        front_weights = list(front_prob.values())
        front = random.choices(front_numbers, weights=front_weights, k=6)
        front = sorted(list(set(front)))
        if len(front) == 6:
            front = [f"{num:02d}" for num in front]  # 确保是两位数格式
            break

    while True:
        back_numbers = list(back_prob.keys())
        back_weights = list(back_prob.values())
        back = random.choices(back_numbers, weights=back_weights, k=1)
        back = sorted(list(set(back)))
        if len(back) == 1:
            back = [f"{num:02d}" for num in back]  # 确保是两位数格式
            break

    # 检查是否与已生成的号码重复
    if (tuple(front), tuple(back)) not in existing_numbers:
        return front, back
    else:
        return generate_ssq_numbers(front_prob, back_prob, generated_data, front_range, back_range)


# 生成七星彩号码（基于概率分布，允许前区重复）
def generate_qxc_numbers(front_prob, back_prob, generated_data):
    # 读取已生成的七星彩号码
    existing_numbers = set()
    for row in generated_data:
        if not row:  # 跳过空行
            continue
        try:
            if len(row) < 3:
                raise ValueError(f"数据格式错误：行数据不足 3 个元素，当前行：{row}")
            front = tuple(map(int, row[1].split(',')))  # 前区
            back = int(row[2])  # 后区
            existing_numbers.add((front, back))
        except (IndexError, ValueError) as e:
            print(f"数据解析错误：{row}，错误信息：{e}")
            continue  # 跳过错误数据，继续处理下一行

    # 生成新号码的逻辑
    while True:
        front_numbers = list(front_prob.keys())
        front_weights = list(front_prob.values())
        front = random.choices(front_numbers, weights=front_weights, k=6)
        front = tuple(front)  # 转换为元组以便去重检查

        back_numbers = list(back_prob.keys())
        back_weights = list(back_prob.values())
        back = random.choices(back_numbers, weights=back_weights, k=1)
        back = back[0]  # 取第一个元素

        # 检查是否与已生成的号码重复
        if (front, back) not in existing_numbers:
            return list(front), back


def save_generated_number(lottery_type, results):
    if lottery_type == "大乐透":
        filename = csv_generated_dlt
        header = ["类型", "红球", "篮球"]
    elif lottery_type == "双色球":
        filename = csv_generated_ssq
        header = ["类型", "红球", "篮球"]
    elif lottery_type == "七星彩":
        filename = csv_generated_qxc
        header = ["类型", "前区", "后区"]
    else:
        raise ValueError(f"未知的彩票类型: {lottery_type}")

    ensure_csv_exists(filename, header)

    # 过滤出与彩票类型匹配的号码
    filtered_results = [result for result in results if result[0] == lottery_type]

    # 保存生成的号码
    with open(filename, 'a', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        for result in filtered_results:
            _, front, back = result  # 解包为彩票类型、前区号码、后区号码
            if lottery_type == "七星彩":
                writer.writerow([lottery_type, ','.join(map(str, front)), back])
            else:
                writer.writerow([lottery_type, ','.join(map(str, front)), ','.join(map(str, back))])


# 判断CSV文件中是否已经存在今天、昨天或前天的数据
def has_recent_data(base_filename, target_year=None):
    # 如果没有指定年份，则使用当前年份
    if target_year is None:
        target_year = datetime.today().year

    filename = get_year_csv_path(base_filename, target_year)

    # 获取今天、昨天和前天的日期
    today = datetime.today()
    yesterday = today - timedelta(days=1)
    day_before_yesterday = today - timedelta(days=2)

    # 如果昨天是星期五，则跳过昨天，检查更早一天（仅针对大乐透和双色球）
    if base_filename in ["dlt_results", "ssq_results"] and yesterday.weekday() == 4:  # 4 表示星期五
        yesterday = today - timedelta(days=2)
        day_before_yesterday = today - timedelta(days=3)
    # 如果前天是星期五，则跳过前天，检查更早一天（仅针对大乐透和双色球）
    if base_filename in ["dlt_results", "ssq_results"] and day_before_yesterday.weekday() == 4:  # 4 表示星期五
        day_before_yesterday = today - timedelta(days=3)

    # 准备需要检查的日期
    dates_to_check = [
        today.strftime("%Y-%m-%d"),
        yesterday.strftime("%Y-%m-%d"),
        day_before_yesterday.strftime("%Y-%m-%d")
    ]

    if not os.path.exists(filename):
        return False

    with open(filename, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # 跳过表头
        for row in reader:
            # 检查 row 是否有足够的字段
            if len(row) < 2:
                logger.warning(f"跳过不完整的行: {row}")
                continue
            if row[1] in dates_to_check:  # 检查日期是否为需要检查的日期
                return True
    return False


# 生成号码的函数
def generate_lottery_numbers(num_results=1, target_year=None):
    # 如果没有指定年份，则使用当前年份
    if target_year is None:
        target_year = datetime.today().year

    # 确保所有CSV文件存在
    dlt_filename = get_year_csv_path("dlt_results", target_year)
    ssq_filename = get_year_csv_path("ssq_results", target_year)
    qxc_filename = get_year_csv_path("qxc_results", target_year)
    ensure_csv_exists(dlt_filename, ["开奖期数", "开奖时间", "红球1", "红球2", "红球3", "红球4", "红球5", "篮球1", "篮球2"])
    ensure_csv_exists(ssq_filename, ["开奖期数", "开奖时间", "红球1", "红球2", "红球3", "红球4", "红球5", "红球6", "篮球1"])
    ensure_csv_exists(qxc_filename, ["开奖期数", "开奖时间", "前区1", "前区2", "前区3", "前区4", "前区5", "前区6", "后区1"])
    ensure_csv_exists(csv_generated_dlt, ["类型", "红球", "篮球"])
    ensure_csv_exists(csv_generated_ssq, ["类型", "红球", "篮球"])
    ensure_csv_exists(csv_generated_qxc, ["类型", "前区", "后区"])

    # 获取今天是星期几
    today = datetime.today().weekday()  # 0:星期一, 1:星期二, ..., 6:星期日

    results = []

    # 处理大乐透
    if today in [0, 2, 5]:  # 星期一、星期三、星期六（大乐透）
        if not has_recent_data("dlt_results", target_year):
            # 爬取大乐透数据
            dlt_data = fetch_and_parse_lottery(url_dlt, "大乐透")
            if dlt_data:
                save_to_csv(dlt_data, "dlt_results", ["开奖期数", "开奖时间", "红球1", "红球2", "红球3", "红球4", "红球5", "篮球1", "篮球2"])

        # 获取最近30期数据
        dlt_data = get_recent_30_data("dlt_results", target_year)

        # 分析大乐透号码概率
        front_prob, back_prob = analyze_number_probability(dlt_data, front_range=(1, 35), back_range=(1, 12))

        # 读取已生成的大乐透号码
        generated_dlt_data = []
        with open(csv_generated_dlt, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # 跳过表头
            generated_dlt_data = list(reader)

        # 生成大乐透号码
        for _ in range(num_results):
            front, back = generate_dlt_numbers(front_prob, back_prob, generated_dlt_data, front_range=(1, 35), back_range=(1, 12))
            results.append(("大乐透", front, back))
        save_generated_number("大乐透", results)

    # 处理双色球
    if today in [1, 3, 6]:  # 星期二、星期四、星期日（双色球）
        if not has_recent_data("ssq_results", target_year):
            # 爬取双色球数据
            ssq_data = fetch_and_parse_ssq(url_ssq)
            if ssq_data:
                save_to_csv(ssq_data, "ssq_results", ["开奖期数", "开奖时间", "红球1", "红球2", "红球3", "红球4", "红球5", "红球6", "篮球1"])

        # 获取最近30期数据
        ssq_data = get_recent_30_data("ssq_results", target_year)

        # 分析双色球号码概率
        front_prob, back_prob = analyze_number_probability(ssq_data, front_range=(1, 33), back_range=(1, 16))

        # 读取已生成的双色球号码
        generated_ssq_data = []
        with open(csv_generated_ssq, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # 跳过表头
            generated_ssq_data = list(reader)

        # 生成双色球号码
        for _ in range(num_results):
            front, back = generate_ssq_numbers(front_prob, back_prob, generated_ssq_data, front_range=(1, 33), back_range=(1, 16))
            results.append(("双色球", front, back))
        save_generated_number("双色球", results)

    # 处理七星彩
    if today in [1, 4, 6]:  # 星期二、星期五、星期日（七星彩）
        if not has_recent_data("qxc_results", target_year):
            # 爬取七星彩数据
            qxc_data = fetch_and_parse_lottery(url_qxc, "七星彩")
            if qxc_data:
                save_to_csv(qxc_data, "qxc_results", ["开奖期数", "开奖时间", "前区1", "前区2", "前区3", "前区4", "前区5", "前区6", "后区1"])

        # 获取最近30期数据
        qxc_data = get_recent_30_data("qxc_results", target_year)

        # 分析七星彩号码概率
        front_prob, back_prob = analyze_number_probability(qxc_data, front_range=(0, 9), back_range=(0, 14))

        # 读取已生成的七星彩号码
        generated_qxc_data = []
        with open(csv_generated_qxc, 'r', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # 跳过表头
            generated_qxc_data = list(reader)

        # 生成七星彩号码
        for _ in range(num_results):
            front, back = generate_qxc_numbers(front_prob, back_prob, generated_qxc_data)
            results.append(("七星彩", front, back))
        save_generated_number("七星彩", results)

    # 如果没有生成任何号码，返回提示信息
    if not results:
        return "今天没有开奖活动！"

    # 格式化结果
    formatted_results = []
    for lottery_type, front, back in results:
        if lottery_type == "七星彩":
            formatted_results.append(f"{lottery_type} - 前：{', '.join(map(str, front))}  后：{back}")
        else:
            formatted_results.append(f"{lottery_type} - 红：{', '.join(map(str, front))}  蓝：{', '.join(map(str, back))}")
    return "\n".join(formatted_results)



def default_result(int_data):
    initial = generate_lottery_numbers(int_data)

    # 判断是否是星期五的特殊提示
    if initial == "今天没有开奖活动！":
        return initial  # 直接返回提示信息，不进行排序

    # 将结果拆分为多组，并按照篮球号码排序
    result_lines = initial.split("\n")  # 将结果按行拆分
    try:
        result_lines.sort(key=lambda x: int(x.split("篮球：")[1].split(",")[0]))
    except (IndexError, ValueError) as e:
        # 如果排序失败（例如数据格式不正确），直接返回原始结果
        return initial

    # 重新组合为字符串
    result = "\n".join(result_lines)
    return result

if __name__ == "__main__":
    # 生成并打印结果
    result = generate_lottery_numbers()
    print(result)