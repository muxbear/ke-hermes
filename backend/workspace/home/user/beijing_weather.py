#!/usr/bin/env python3
"""获取今天北京的天气信息。

使用 wttr.in 提供的免费天气 API，无需注册或 API Key。
"""

import json
import urllib.request
import urllib.error


def get_beijing_weather():
    """获取北京今天的天气并打印。"""
    # wttr.in 免费天气 API，返回 JSON 格式数据
    url = "https://wttr.in/Beijing?format=j1&lang=zh"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"网络请求失败: {e}")
        return
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败: {e}")
        return

    # 解析当前天气
    current = data.get("current_condition", [{}])[0]
    weather_desc = current.get("lang_zh", [{}])[0].get("value", "未知")
    temp_c = current.get("temp_C", "N/A")
    feels_like = current.get("FeelsLikeC", "N/A")
    humidity = current.get("humidity", "N/A")
    wind_speed = current.get("windspeedKmph", "N/A")
    wind_dir = current.get("winddir16Point", "N/A")
    visibility = current.get("visibility", "N/A")
    pressure = current.get("pressure", "N/A")

    print("=" * 50)
    print("           🌤️  北京今日天气")
    print("=" * 50)
    print(f"  天气状况:  {weather_desc}")
    print(f"  当前温度:  {temp_c} °C")
    print(f"  体感温度:  {feels_like} °C")
    print(f"  湿度:      {humidity}%")
    print(f"  风向风速:  {wind_dir} {wind_speed} km/h")
    print(f"  能见度:    {visibility} km")
    print(f"  气压:      {pressure} hPa")
    print("=" * 50)

    # 解析今天天气预报
    forecast = data.get("weather", [{}])[0]
    date = forecast.get("date", "未知")
    max_temp = forecast.get("maxtempC", "N/A")
    min_temp = forecast.get("mintempC", "N/A")
    avg_temp = forecast.get("avgtempC", "N/A")
    sunrise = forecast.get("astronomy", [{}])[0].get("sunrise", "N/A")
    sunset = forecast.get("astronomy", [{}])[0].get("sunset", "N/A")

    print(f"\n📅 今日预报 ({date})")
    print("-" * 50)
    print(f"  最高温度:  {max_temp} °C")
    print(f"  最低温度:  {min_temp} °C")
    print(f"  平均温度:  {avg_temp} °C")
    print(f"  日出:      {sunrise}")
    print(f"  日落:      {sunset}")
    print("=" * 50)


if __name__ == "__main__":
    get_beijing_weather()
