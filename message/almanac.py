import requests
import os
from datetime import datetime

# 从环境变量中获取 API Key
apiKey = os.getenv('LAOHUANGLI_API_KEY')

# 基本参数配置
apiUrl = 'http://v.juhe.cn/laohuangli/d'  # 接口请求URL


def get_laohuangli(date=None):
    # 如果没有传入日期，则使用当天日期
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')

    # 接口请求入参配置
    requestParams = {
        'key': apiKey,
        'date': date,
    }

    # 发起接口网络请求
    response = requests.get(apiUrl, params=requestParams)

    # 解析响应结果
    if response.status_code == 200:
        responseResult = response.json()

        # 检查接口返回的状态码是否为0（表示成功）
        if responseResult.get('error_code') == 0:
            # 提取老黄历数据
            result = responseResult['result']

            # 按照指定格式整理老黄历数据（去掉阳历行）
            laohuangli_info = (
                f"阴历：{result['yinli']}\n"
                f"五行：{result['wuxing']}\n"
                f"冲煞：{result['chongsha']}\n"
                f"彭祖百忌：{result['baiji']}\n"
                f"吉神宜趋：{result['jishen']}\n"
                f"宜：{result['yi']}\n"
                f"凶神宜忌：{result['xiongshen']}\n"
                f"忌：{result['ji']}\n"
            )
            return laohuangli_info
        else:
            # 接口返回错误信息
            return f"查询老黄历失败，原因：{responseResult.get('reason')}"
    else:
        # 网络异常等因素，解析结果异常
        return f"请求老黄历异常，状态码：{response.status_code}"
