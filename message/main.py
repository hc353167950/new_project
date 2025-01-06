import requests
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
    report += "<h3>🎰 已为您生成今日份5注幸运彩票：</h3>"
    if result_lotto and isinstance(result_lotto, list):  # 检查是否有彩票数据
        report += "<pre>"
        for lotto in result_lotto:
            report += f"{lotto}\n"  # 每注彩票换行
        report += "</pre>"
    else:
        report += f"<pre>{result_lotto}</pre>"  # 如果没有彩票数据，直接展示返回的内容

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
    # 替换为你的 WxPusher AppToken
    app_token = "AT_M6s0l9nVAHVDAmg977dqIIDq2cpl2jVn"

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
target_type = "topic"  # 可选值：`topic`（发送到群组）或 `uid`（发送到单个用户）
target_id = "36910"  # 替换为你的 Topic ID 或 UID

# target_type = "uid"  # 可选值：`topic`（发送到群组）或 `uid`（发送到单个用户）
# target_id = "UID_bKFb5j6lj4q8Gzs3w2PhmBtLZ6VY"  # 替换为你的 Topic ID 或 UID

# 发送消息
send_to_wechat(daily_report, target_type, target_id)
