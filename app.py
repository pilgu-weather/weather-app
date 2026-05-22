from flask import Flask, render_template, request
import requests
from datetime import datetime
import random

app = Flask(__name__)

API_KEY = "2fd339c206c2fa601c64bc589a4750e9"


@app.route("/", methods=["GET", "POST"])
def home():

    temp = None
    feels_like = None

    temp_min = None
    temp_max = None
    day_temp = None

    pm = None
    pm_text = None

    outfits = []

    icon_url = None
    city_name = None

    weather_main = None
    wind_speed = 0

    lat = None
    lon = None

    error = None

    # =========================
    # 도시 검색
    # =========================

    if request.method == "POST":

        city = request.form["city"]

        weather_url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={city}&appid={API_KEY}&units=metric"
        )

        response = requests.get(weather_url)
        data = response.json()

        if response.status_code != 200:

            error = "도시를 찾을 수 없습니다."

            return render_template(
                "index.html",
                error=error
            )

        city_name = data["name"]

        temp = round(data["main"]["temp"])
        feels_like = round(data["main"]["feels_like"])

        weather_main = data["weather"][0]["main"]
        wind_speed = data["wind"]["speed"]

        icon = data["weather"][0]["icon"]

        icon_url = (
            f"https://openweathermap.org/img/wn/{icon}@2x.png"
        )

        lat = data["coord"]["lat"]
        lon = data["coord"]["lon"]

    # =========================
    # 현재 위치
    # =========================

    elif request.args.get("lat") and request.args.get("lon"):

        try:

            lat = float(request.args.get("lat"))
            lon = float(request.args.get("lon"))

        except:

            error = "위치 정보를 불러오지 못했습니다."

            return render_template(
                "index.html",
                error=error
            )

        weather_url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        )

        response = requests.get(weather_url)
        data = response.json()

        if response.status_code != 200:

            error = "현재 위치 날씨를 가져오지 못했습니다."

            return render_template(
                "index.html",
                error=error
            )

        city_name = data["name"]

        temp = round(data["main"]["temp"])
        feels_like = round(data["main"]["feels_like"])

        weather_main = data["weather"][0]["main"]
        wind_speed = data["wind"]["speed"]

        icon = data["weather"][0]["icon"]

        icon_url = (
            f"https://openweathermap.org/img/wn/{icon}@2x.png"
        )

        lat = data["coord"]["lat"]
        lon = data["coord"]["lon"]

    else:

        return render_template("index.html")

    # =========================
    # Forecast API
    # =========================

    forecast_url = (
        f"https://api.openweathermap.org/data/2.5/forecast"
        f"?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
    )

    forecast_response = requests.get(forecast_url)
    forecast_data = forecast_response.json()

    today = datetime.now().strftime("%Y-%m-%d")

    today_temps = []
    daytime_temps = []

    if "list" in forecast_data:

        for item in forecast_data["list"]:

            dt_txt = item["dt_txt"]

            date_part = dt_txt.split(" ")[0]

            hour_part = int(
                dt_txt.split(" ")[1].split(":")[0]
            )

            if date_part == today:

                current_temp = item["main"]["temp"]

                today_temps.append(current_temp)

                if 12 <= hour_part <= 15:

                    daytime_temps.append(current_temp)

    if today_temps:

        temp_min = round(min(today_temps))
        temp_max = round(max(today_temps))

    else:

        temp_min = temp
        temp_max = temp

    if daytime_temps:

        day_temp = round(
            sum(daytime_temps) / len(daytime_temps)
        )

    else:

        day_temp = temp

    # =========================
    # 미세먼지
    # =========================

    air_url = (
        f"https://api.openweathermap.org/data/2.5/air_pollution"
        f"?lat={lat}&lon={lon}&appid={API_KEY}"
    )

    air_data = requests.get(air_url).json()

    if "list" in air_data:

        pm = air_data["list"][0]["main"]["aqi"]

    else:

        pm = 1

    if pm == 1:

        pm_text = "좋음"

    elif pm == 2:

        pm_text = "보통"

    elif pm == 3:

        pm_text = "나쁨"

    elif pm == 4:

        pm_text = "매우 나쁨"

    else:

        pm_text = "최악"

    # =========================
    # 계절 판단
    # =========================

    if temp >= 27:

        season = "summer"

    elif temp >= 20:

        season = "spring"

    elif temp >= 10:

        season = "fall"

    else:

        season = "winter"

    # =========================
    # 계절별 스타일 추천
    # =========================

    if season == "summer":

        outfits = [

            {
                "title": "여름 미니멀",
                "desc": "반팔과 쇼츠 기반의 깔끔한 여름 스타일.",
                "img": random.choice([
                    "/static/styles/summer_minimal_1.png",
                    "/static/styles/summer_minimal_2.png",
                    "/static/styles/summer_minimal_3.png",
                    "/static/styles/summer_minimal_4.png",
                    "/static/styles/summer_minimal_5.png"
                ])
            },

            {
                "title": "여름 남친룩",
                "desc": "린넨 셔츠와 반바지 조합의 데이트룩.",
                "img": random.choice([
                    "/static/styles/summer_boyfriend_1.png",
                    "/static/styles/summer_boyfriend_2.png",
                    "/static/styles/summer_boyfriend_3.png",
                    "/static/styles/summer_boyfriend_4.png",
                    "/static/styles/summer_boyfriend_5.png"
                ])
            },

            {
                "title": "여름 스트릿",
                "desc": "오버핏 반팔 중심의 스트릿 무드.",
                "img": random.choice([
                    "/static/styles/summer_street_1.png",
                    "/static/styles/summer_street_2.png",
                    "/static/styles/summer_street_3.png",
                    "/static/styles/summer_street_4.png",
                    "/static/styles/summer_street_5.png"
                ])
            }

        ]

    elif season == "spring":

        outfits = [

            {
                "title": "봄 미니멀",
                "desc": "가디건 기반의 깔끔한 미니멀룩.",
                "img": random.choice([
                    "/static/styles/spring_minimal_1.png",
                    "/static/styles/spring_minimal_2.png",
                    "/static/styles/spring_minimal_3.png",
                    "/static/styles/spring_minimal_4.png",
                    "/static/styles/spring_minimal_5.png"
                ])
            },

            {
                "title": "봄 남친룩",
                "desc": "셔츠 레이어드 중심의 데이트 스타일.",
                "img": random.choice([
                    "/static/styles/spring_boyfriend_1.png",
                    "/static/styles/spring_boyfriend_2.png",
                    "/static/styles/spring_boyfriend_3.png",
                    "/static/styles/spring_boyfriend_4.png",
                    "/static/styles/spring_boyfriend_5.png"
                ])
            },

            {
                "title": "봄 스트릿",
                "desc": "가벼운 바람막이 중심 스트릿룩.",
                "img": random.choice([
                    "/static/styles/spring_street_1.png",
                    "/static/styles/spring_street_2.png",
                    "/static/styles/spring_street_3.png",
                    "/static/styles/spring_street_4.png",
                    "/static/styles/spring_street_5.png"
                ])
            }

        ]

    elif season == "fall":

        outfits = [

            {
                "title": "가을 미니멀",
                "desc": "가디건과 슬랙스 기반 감성 코디.",
                "img": random.choice([
                    "/static/styles/fall_minimal_1.png",
                    "/static/styles/fall_minimal_2.png",
                    "/static/styles/fall_minimal_3.png",
                    "/static/styles/fall_minimal_4.png",
                    "/static/styles/fall_minimal_5.png"
                ])
            },

            {
                "title": "가을 남친룩",
                "desc": "자켓과 셔츠 조합의 데일리룩.",
                "img": random.choice([
                    "/static/styles/fall_boyfriend_1.png",
                    "/static/styles/fall_boyfriend_2.png",
                    "/static/styles/fall_boyfriend_3.png",
                    "/static/styles/fall_boyfriend_4.png",
                    "/static/styles/fall_boyfriend_5.png"
                ])
            },

            {
                "title": "가을 스트릿",
                "desc": "후드와 와이드 팬츠 기반 스트릿룩.",
                "img": random.choice([
                    "/static/styles/fall_street_1.png",
                    "/static/styles/fall_street_2.png",
                    "/static/styles/fall_street_3.png",
                    "/static/styles/fall_street_4.png",
                    "/static/styles/fall_street_5.png"
                ])
            }

        ]

    else:

        outfits = [

            {
                "title": "겨울 미니멀",
                "desc": "코트와 니트 중심의 겨울 스타일.",
                "img": random.choice([
                    "/static/styles/winter_minimal_1.png",
                    "/static/styles/winter_minimal_2.png",
                    "/static/styles/winter_minimal_3.png",
                    "/static/styles/winter_minimal_4.png",
                    "/static/styles/winter_minimal_5.png"
                ])
            },

            {
                "title": "겨울 남친룩",
                "desc": "패딩과 머플러 기반 데일리룩.",
                "img": random.choice([
                    "/static/styles/winter_boyfriend_1.png",
                    "/static/styles/winter_boyfriend_2.png",
                    "/static/styles/winter_boyfriend_3.png",
                    "/static/styles/winter_boyfriend_4.png",
                    "/static/styles/winter_boyfriend_5.png"
                ])
            },

            {
                "title": "겨울 스트릿",
                "desc": "패딩과 후드 조합의 스트릿 무드.",
                "img": random.choice([
                    "/static/styles/winter_street_1.png",
                    "/static/styles/winter_street_2.png",
                    "/static/styles/winter_street_3.png",
                    "/static/styles/winter_street_4.png",
                    "/static/styles/winter_street_5.png"
                ])
            }

        ]

    return render_template(

        "index.html",

        temp=temp,
        feels_like=feels_like,

        temp_min=temp_min,
        temp_max=temp_max,
        day_temp=day_temp,

        pm=pm,
        pm_text=pm_text,

        outfits=outfits,

        icon_url=icon_url,
        city_name=city_name,

        error=error
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)