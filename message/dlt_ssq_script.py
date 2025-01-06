from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from collections import defaultdict
import csv
import random
from datetime import datetime, timedelta
import os
import time
import re

# 大乐透和双色球的开奖数据网址
url_dlt = "http://zhong.china-ssq.net/dlt/latest"
url_ssq = "http://zhong.china-ssq.net/ssq/latest"

# CSV文件路径
data_dir = "data"  # 数据文件夹
csv_generated_dlt = os.path.join(data_dir, "generated_dlt.csv")
csv_generated_ssq = os.path.join(data_dir, "generated_ssq.csv")


# 根据年份生成文件路径
def get_year_csv_path(base_filename, year):
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


# 使用Selenium获取网页内容
def fetch_html_with_selenium(url):
    # 设置Selenium选项
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 无头模式
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # 启动浏览器
    service = Service(ChromeDriverManager().install())  # 自动管理并下载与浏览器匹配的驱动
    driver = webdriver.Chrome(service=service, options=options)
    driver.get(url)
    time.sleep(3)  # 等待页面加载
    html = driver.page_source
    driver.quit()
    return html


# 解析大乐透开奖数据
def parse_dlt(html):
    from lxml import etree
    dom = etree.HTML(html)
    results = []

    # 获取开奖数据列表
    items = dom.xpath("/html/body/div[2]/div[2]/div/div[2]/a")
    for item in items:
        issue = item.xpath(".//div/div/div[1]/div[1]/label[2]/text()")[0].strip()  # 开奖期数
        date_raw = item.xpath(".//div/div/div[1]/div[2]/text()")[0].strip()  # 开奖时间（原始格式）
        date = re.search(r"\d{4}-\d{2}-\d{2}", date_raw).group()  # 提取日期部分
        numbers = item.xpath(".//div/div/div[2]/div[1]/em/text()")  # 号码列表
        if len(numbers) >= 7:  # 确保号码数量正确
            front = numbers[:5]  # 前区
            back = numbers[5:]  # 后区
            results.append([issue, date] + front + back)

    return results


# 解析双色球开奖数据
def parse_ssq(html):
    from lxml import etree
    dom = etree.HTML(html)
    results = []

    # 获取开奖数据列表
    items = dom.xpath("/html/body/div[2]/div[2]/div/div[2]/a")
    for item in items:
        issue = item.xpath(".//div/div/div[1]/div[1]/label[2]/text()")[0].strip()  # 开奖期数
        date_raw = item.xpath(".//div/div/div[1]/div[2]/text()")[0].strip()  # 开奖时间（原始格式）
        date = re.search(r"\d{4}-\d{2}-\d{2}", date_raw).group()  # 提取日期部分
        numbers = item.xpath(".//div/div/div[2]/div[1]/em/text()")  # 号码列表
        if len(numbers) >= 7:  # 确保号码数量正确
            front = numbers[:6]  # 前区
            back = numbers[6:]  # 后区
            results.append([issue, date] + front + back)

    return results


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
    # 初始化前区和后区号码的计数器
    front_counter = {num: 0 for num in range(front_range[0], front_range[1] + 1)}
    back_counter = {num: 0 for num in range(back_range[0], back_range[1] + 1)}

    # 统计历史数据中号码的出现次数
    front_numbers = [int(num) for draw in data for num in draw[2:-2] if front_range[0] <= int(num) <= front_range[1]]
    back_numbers = [int(num) for draw in data for num in draw[-2:] if back_range[0] <= int(num) <= back_range[1]]

    for num in front_numbers:
        front_counter[num] += 1
    for num in back_numbers:
        back_counter[num] += 1

    # 计算前区和后区号码的概率
    front_total = sum(front_counter.values())
    back_total = sum(back_counter.values())

    front_prob = {num: count / front_total for num, count in front_counter.items()}
    back_prob = {num: count / back_total for num, count in back_counter.items()}

    return front_prob, back_prob


# 生成大乐透号码，确保红球和篮球都不重复，并且不与之前生成的号码重复
def generate_dlt_numbers(front_prob, back_prob, generated_data, front_range=(1, 35), back_range=(1, 12)):
    # 读取已生成的大乐透号码
    existing_numbers = set()
    for row in generated_data:
        front = tuple(map(int, row[1].split(',')))  # 红球
        back = tuple(map(int, row[2].split(',')))  # 篮球
        existing_numbers.add((front, back))  # 将红球和篮球组合作为唯一标识

    while True:
        # 生成前区号码（红球），根据概率分布
        front_numbers = list(front_prob.keys())
        front_weights = list(front_prob.values())
        front = random.choices(front_numbers, weights=front_weights, k=5)  # 使用概率分布生成号码
        front = sorted(list(set(front)))  # 去重并排序
        if len(front) == 5:  # 确保生成了5个不重复的号码
            break

    while True:
        # 生成后区号码（篮球），根据概率分布
        back_numbers = list(back_prob.keys())
        back_weights = list(back_prob.values())
        back = random.choices(back_numbers, weights=back_weights, k=2)  # 使用概率分布生成号码
        back = sorted(list(set(back)))  # 去重并排序
        if len(back) == 2:  # 确保生成了2个不重复的号码
            break

    # 检查是否与已生成的号码重复
    if (tuple(front), tuple(back)) not in existing_numbers:
        return front, back
    else:
        return generate_dlt_numbers(front_prob, back_prob, generated_data, front_range, back_range)  # 递归生成


# 生成双色球号码，确保红球和篮球都不重复，并且不与之前生成的号码重复
def generate_ssq_numbers(front_prob, back_prob, generated_data, front_range=(1, 33), back_range=(1, 16)):
    # 读取已生成的双色球号码
    existing_numbers = set()
    for row in generated_data:
        front = tuple(map(int, row[1].split(',')))  # 红球
        back = tuple(map(int, row[2].split(',')))  # 篮球
        existing_numbers.add((front, back))  # 将红球和篮球组合作为唯一标识

    while True:
        # 生成前区号码（红球），根据概率分布
        front_numbers = list(front_prob.keys())
        front_weights = list(front_prob.values())
        front = random.choices(front_numbers, weights=front_weights, k=6)  # 使用概率分布生成号码
        front = sorted(list(set(front)))  # 去重并排序
        if len(front) == 6:  # 确保生成了6个不重复的号码
            break

    while True:
        # 生成后区号码（篮球），根据概率分布
        back_numbers = list(back_prob.keys())
        back_weights = list(back_prob.values())
        back = random.choices(back_numbers, weights=back_weights, k=1)  # 使用概率分布生成号码
        back = sorted(list(set(back)))  # 去重并排序
        if len(back) == 1:  # 确保生成了1个不重复的号码
            break

    # 检查是否与已生成的号码重复
    if (tuple(front), tuple(back)) not in existing_numbers:
        return front, back
    else:
        return generate_ssq_numbers(front_prob, back_prob, generated_data, front_range, back_range)  # 递归生成


# 保存生成的随机号码
def save_generated_number(lottery_type, results):
    filename = csv_generated_dlt if lottery_type == "大乐透" else csv_generated_ssq
    header = ["类型", "红球", "篮球"]
    ensure_csv_exists(filename, header)

    # 保存生成的号码
    with open(filename, 'a', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        for front, back in results:
            writer.writerow([lottery_type, ','.join(map(str, front)), ','.join(map(str, back))])


# 判断CSV文件中是否已经存在今天、昨天或前天的数据（排除星期五）
def has_recent_data(base_filename, target_year=None):
    # 如果没有指定年份，则使用当前年份
    if target_year is None:
        target_year = datetime.today().year

    filename = get_year_csv_path(base_filename, target_year)

    # 获取今天、昨天和前天的日期
    today = datetime.today()
    yesterday = today - timedelta(days=1)
    day_before_yesterday = today - timedelta(days=2)

    # 如果昨天是星期五，则跳过昨天，检查更早一天
    if yesterday.weekday() == 4:  # 4 表示星期五
        yesterday = today - timedelta(days=2)
        day_before_yesterday = today - timedelta(days=3)
    # 如果前天是星期五，则跳过前天，检查更早一天
    if day_before_yesterday.weekday() == 4:  # 4 表示星期五
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
            if row[1] in dates_to_check:  # 检查日期是否为需要检查的日期
                return True
    return False


# 生成号码的函数，可以被其他地方调用
def generate_lottery_numbers(num_results=1, target_year=None):
    # 如果没有指定年份，则使用当前年份
    if target_year is None:
        target_year = datetime.today().year

    # 确保所有CSV文件存在
    dlt_filename = get_year_csv_path("dlt_results", target_year)
    ssq_filename = get_year_csv_path("ssq_results", target_year)
    ensure_csv_exists(dlt_filename, ["开奖期数", "开奖时间", "红球1", "红球2", "红球3", "红球4", "红球5", "篮球1", "篮球2"])
    ensure_csv_exists(ssq_filename, ["开奖期数", "开奖时间", "红球1", "红球2", "红球3", "红球4", "红球5", "红球6", "篮球1"])
    ensure_csv_exists(csv_generated_dlt, ["类型", "红球", "篮球"])
    ensure_csv_exists(csv_generated_ssq, ["类型", "红球", "篮球"])

    # 获取今天是星期几
    today = datetime.today().weekday()  # 0:星期一, 1:星期二, ..., 6:星期日

    if today == 4:  # 星期五
        return "今天双色球和大乐透都不开奖噢！"

    if today in [0, 2, 5]:  # 星期一、星期三、星期六（大乐透）
        if not has_recent_data("dlt_results", target_year):
            # 爬取大乐透数据
            dlt_html = fetch_html_with_selenium(url_dlt)
            dlt_data = parse_dlt(dlt_html)
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
        results = []
        for _ in range(num_results):
            front, back = generate_dlt_numbers(front_prob, back_prob, generated_dlt_data, front_range=(1, 35), back_range=(1, 12))
            results.append((front, back))
        save_generated_number("大乐透", results)
        # 返回格式化后的结果，每组结果换行显示
        formatted_results = "\n".join([f"红球：{', '.join(map(str, front))}   篮球：{', '.join(map(str, back))}" for front, back in results])
        return formatted_results

    if today in [1, 3, 6]:  # 星期二、星期四、星期日（双色球）
        if not has_recent_data("ssq_results", target_year):
            # 爬取双色球数据
            ssq_html = fetch_html_with_selenium(url_ssq)
            ssq_data = parse_ssq(ssq_html)
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
        results = []
        for _ in range(num_results):
            front, back = generate_ssq_numbers(front_prob, back_prob, generated_ssq_data, front_range=(1, 33), back_range=(1, 16))
            results.append((front, back))
        save_generated_number("双色球", results)
        # 返回格式化后的结果，每组结果换行显示
        formatted_results = "\n".join([f"红球：{', '.join(map(str, front))}   篮球：{', '.join(map(str, back))}" for front, back in results])
        return formatted_results

    return "今天没有开奖活动！"


# 处理返回结果，按按篮球号码排序
def default_result(int_data):
    initial = generate_lottery_numbers(int_data)

    # 将结果拆分为多组，并按照篮球号码排序
    result_lines = initial.split("\n")  # 将结果按行拆分
    result_lines.sort(key=lambda x: int(x.split("篮球：")[1].split(",")[0]))
    # 重新组合为字符串
    result = "\n".join(result_lines)
    return result
