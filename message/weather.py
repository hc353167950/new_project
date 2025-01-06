import requests

# API Key（明文）
apiKey = 'ca1c8cfffe12b57d7e74cd99930aa366'


def get_weather(city=None):
    # 默认城市列表
    default_cities = ['武汉', '广州']

    # 如果没有传入城市，则使用默认城市
    if city is None:
        cities = default_cities
    else:
        cities = [city]  # 将传入的城市转为列表形式

    # 基本参数配置
    apiUrl = 'http://apis.juhe.cn/simpleWeather/query'  # 接口请求URL

    # 存储所有城市的天气数据
    weather_results = []

    for city in cities:
        # 接口请求入参配置
        requestParams = {
            'key': apiKey,
            'city': city,
        }

        # 发起接口网络请求
        response = requests.get(apiUrl, params=requestParams)

        # 解析响应结果
        if response.status_code == 200:
            responseResult = response.json()

            # 检查接口返回的状态码是否为0（表示成功）
            if responseResult.get('error_code') == 0:
                # 提取当天数据（只使用 realtime 字段）
                realtime_weather = responseResult['result']['realtime']

                # 按照指定格式整理天气数据
                weather_info = (
                    f"城市：{city}\n"
                    f"天气：{realtime_weather['info']}\n"
                    f"风向：{realtime_weather['direct']}\n"
                    f"风力：{realtime_weather['power']}\n"
                    f"温度：{realtime_weather['temperature']}℃\n"
                    f"湿度：{realtime_weather['humidity']}%\n"
                    f"空气质量指数：{realtime_weather['aqi']}\n"
                )
                weather_results.append(weather_info)
            else:
                # 接口返回错误信息
                weather_results.append(f"城市：{city}\n错误：查询失败，原因：{responseResult.get('reason')}")
        else:
            # 网络异常等因素，解析结果异常
            weather_results.append(f"城市：{city}\n错误：请求异常，状态码：{response.status_code}")

    return weather_results
