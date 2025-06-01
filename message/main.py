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


# 整合并规范输出为纯文本格式
def generate_daily_report():
    # 第一行：今日时间
    report = f"📅 今日时间：{today_date}\n\n"

    # 第二行：彩票结果
    if result_lotto:  # 检查是否有彩票数据
        # 将彩票结果按类型分组
        lottery_data = {}
        if isinstance(result_lotto, str):  # 如果返回的是字符串
            # 按行拆分彩票结果
            result_lines = result_lotto.split("\n")
            for lotto in result_lines:
                # 提取彩票类型（如"双色球"、"大乐透"、"七星彩"）
                if " - " in lotto:  # 确保数据包含分隔符
                    lottery_type = lotto.split(" - ")[0]  # 提取彩票类型
                    if lottery_type not in lottery_data:
                        lottery_data[lottery_type] = []
                    lottery_data[lottery_type].append(lotto)
                else:
                    print(f"数据格式错误：{lotto}")  # 打印格式错误的数据
        elif isinstance(result_lotto, list):  # 如果返回的是列表
            for lotto in result_lotto:
                # 提取彩票类型（如"双色球"、"大乐透"、"七星彩"）
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
                report += f"🎰 已为您生成今日份 {lottery_type} {len(data)}注：\n"
                for item in data:
                    # 确保每注彩票左对齐显示
                    report += f"{item}\n"  # 每注彩票换行
                report += "\n"  # 每种彩票类型之间添加空行
        else:
            report += "🎰 今日无彩票数据\n\n"
    else:
        report += "🎰 今日无彩票数据\n\n"

    # 第三行：天气结果
    if result_weather:  # 检查是否有天气数据
        report += "🌤️ 今日天气：\n"
        if isinstance(result_weather, list):  # 如果天气数据是列表
            for weather in result_weather:
                report += f"{weather}\n"  # 每个城市的天气换行
        else:
            report += f"{result_weather}\n"  # 如果天气数据是字符串或其他格式
        report += "\n"  # 天气数据后添加空行

    # 第四行：老黄历结果
    report += "📜 今日老黄历：\n"
    if laohuangli_data:  # 检查是否有老黄历数据
        if isinstance(laohuangli_data, dict):  # 如果老黄历数据是字典
            for key, value in laohuangli_data.items():
                report += f"{key}：{value}\n"  # 每个字段换行
        else:
            report += f"{laohuangli_data}\n"  # 如果老黄历数据是字符串或其他格式

    return report


# 发送消息到微信（通过 Server酱）
def send_to_wechat(content, target_type, target_id):
    # 从环境变量中获取 Server酱 SCKEY
    sckey = os.getenv('SERVERCHAN_SCKEY')
    
    if not sckey:
        print("错误：未设置SERVERCHAN_SCKEY环境变量！")
        return
    
    # 构造请求URL和参数
    url = f"https://sctapi.ftqq.com/{sckey}.send"
    data = {
        "title": "每日信息推送",  # 消息标题
        "desp": content,  # 消息内容，支持HTML格式
    }
    
    # 发送请求
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print("消息发送成功！")
            else:
                print(f"消息发送失败，错误码：{result.get('code')}")
                print(f"错误信息：{result.get('message')}")
        else:
            print(f"消息发送失败，状态码：{response.status_code}")
            print(f"错误信息：{response.text}")  # 打印错误信息
    except Exception as e:
        print(f"发送消息时发生异常：{str(e)}")



# 生成每日报告
daily_report = generate_daily_report()

# Server酱不需要target_type和target_id参数，但为了保持函数接口一致，仍然传递这些参数
target_type = "none"  # 对Server酱来说这个参数不起作用
target_id = "none"    # 对Server酱来说这个参数不起作用

# 发送消息
send_to_wechat(daily_report, target_type, target_id)


