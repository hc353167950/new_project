import sys
import os
import requests

# 将项目根目录添加到 sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from message.almanac import get_laohuangli
from message.dlt_ssq_script import default_result
from message.weather import get_weather
from datetime import datetime


# 获取当前日期
today_date = datetime.now().strftime('%Y-%m-%d')

# 彩票结果
result_lotto = default_result(5)

# 天气结果
result_weather = get_weather()

# 老黄历结果
laohuangli_data = get_laohuangli()


# 整合并规范输出为 HTML 格式
def generate_daily_report():
    # 第一行：今日时间
    report = f"<h2>📅 今日时间：{today_date}</h2>"

    # 第二行：彩票结果
    if result_lotto:  # 检查是否有彩票数据
        # 将彩票结果按类型分组
        lottery_data = {}
        if isinstance(result_lotto, str):  # 如果返回的是字符串
            # 按行拆分彩票结果
            result_lines = result_lotto.split("\n")
            for lotto in result_lines:
                # 提取彩票类型（如“双色球”、“大乐透”、“七星彩”）
                if " - " in lotto:  # 确保数据包含分隔符
                    lottery_type = lotto.split(" - ")[0]  # 提取彩票类型
                    if lottery_type not in lottery_data:
                        lottery_data[lottery_type] = []
                    lottery_data[lottery_type].append(lotto)
                else:
                    print(f"数据格式错误：{lotto}")  # 打印格式错误的数据
        elif isinstance(result_lotto, list):  # 如果返回的是列表
            for lotto in result_lotto:
                # 提取彩票类型（如“双色球”、“大乐透”、“七星彩”）
                if " - " in lotto:  # 确保数据包含分隔符
                    lottery_type = lotto.split(" - ")[0]  # 提取彩票类型
                    if lottery_type not in lottery_data:
                        lottery_data[lottery_type] = []
                    lottery_data[lottery_type].append(lotto)
                else:
                    print(f"数据格式错误：{lotto}")  # 打印格式错误的数据
        else:
            print(f"未知的彩票结果格式：{type(result_lotto)}")

        # 为每种彩票类型生成标题和内容
        if lottery_data:  # 检查是否有彩票数据
            for lottery_type, data in lottery_data.items():
                report += f"<h3>🎰 已为您生成今日份 {lottery_type} 5注：</h3>"
                report += "<pre>"
                for item in data:
                    report += f"{item}\n"  # 每注彩票换行
                report += "</pre>"
        else:
            report += "<h3>🎰 今日无彩票数据</h3>"
    else:
        report += "<h3>🎰 今日无彩票数据</h3>"

    # 第三行：天气结果
    if result_weather:  # 检查是否有天气数据
        report += "<h3>🌤️ 今日天气：</h3>"
        report += "<pre>"
        if isinstance(result_weather, list):  # 如果天气数据是列表
            for weather in result_weather:
                report += f"{weather}\n"  # 每个城市的天气换行
        else:
            report += f"{result_weather}\n"  # 如果天气数据是字符串或其他格式
        report += "</pre>"

    # 第四行：老黄历结果
    report += "<h3>📜 今日老黄历：</h3>"
    if laohuangli_data:  # 检查是否有老黄历数据
        report += "<pre>"
        if isinstance(laohuangli_data, dict):  # 如果老黄历数据是字典
            for key, value in laohuangli_data.items():
                report += f"{key}：{value}\n"  # 每个字段换行
        else:
            report += f"{laohuangli_data}\n"  # 如果老黄历数据是字符串或其他格式
        report += "</pre>"

    return report


# 发送消息到微信群或单个用户（通过 WxPusher）
def send_to_wechat(content, target_type, target_id):
    # 从环境变量中获取 WxPusher AppToken
    app_token = os.getenv('WXPUSHER_APP_TOKEN')

    # 构造消息体
    url = "https://wxpusher.zjiecode.com/api/send/message"
    data = {
        "appToken": app_token,  # 必传
        "content": content,  # 必传，HTML 格式
        "summary": "恭喜发财",  # 消息摘要，显示在微信聊天页面
        "contentType": 2,  # 2 表示 HTML 格式
        # "url": "https://wxpusher.zjiecode.com",  # 原文链接，可选
        "verifyPayType": 0  # 0 表示不验证订阅时间
    }

    # 根据目标类型设置参数
    if target_type == "topic":
        data["topicIds"] = [int(target_id)]  # 发送到 Topic ID，注意是数组
    elif target_type == "uid":
        data["uids"] = [target_id]  # 发送到单个用户 UID，注意是数组
    else:
        print("无效的目标类型！")
        return

    # 发送请求
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print("消息发送成功！")
    else:
        print(f"消息发送失败，状态码：{response.status_code}")
        print(f"错误信息：{response.text}")  # 打印错误信息


# 生成每日报告
daily_report = generate_daily_report()

# 选择发送方式
target_type = os.getenv('WXPUSHER_TARGET_TYPE', 'topic')  # 默认发送到群组
target_id = os.getenv('WXPUSHER_TARGET_ID')  # 从环境变量中获取 Topic ID 或 UID

# 发送消息
send_to_wechat(daily_report, target_type, target_id)

