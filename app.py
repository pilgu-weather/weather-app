id="m4x8qp"
from flask import Flask, render_template, request
import requests
from datetime import datetime

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
    extra_items = []

    style_name = ""
    style_desc = ""
    mood_message = ""
    style_img = ""

    icon_url = None
    city_name = None

    weather_main = None
    wind_speed = 0

    lat = None
    lon = None

    error = None

    # =========================
    # 스타일 선택
    # =========================

    selected_style = request.args.get(
        "style",
        "minimal"
    )

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
    # 스타일 선택 로직
    # =========================

    if selected_style == "street":

        style_name = "스트릿 무드"

        style_desc = (
            "오버핏 + 와이드 팬츠 기반 스트릿 스타일"
        )

        mood_message = (
            "오늘은 무드 있게, 살짝 힙하게."
        )

        style_img = "/static/styles/street.png"

    elif selected_style == "boyfriend":

        style_name = "남친룩"

        style_desc = (
            "셔츠 + 슬랙스 기반 깔끔한 스타일"
        )

        mood_message = (
            "꾸안꾸 느낌으로 가기 좋은 날."
        )

        style_img = "/static/styles/boyfriend.png"

    else:

        style_name = "미니멀 룩"

        style_desc = (
            "심플하고 깔끔한 데일리 스타일"
        )

        mood_message = (
            "미니멀은 언제나 실패하지 않는다."
        )

        style_img = "/static/styles/minimal.png"

    # =========================
    # 코디 추천
    # =========================

    outfits = [
        {
            "top": {
                "name": "반팔",
                "img": "https://images.unsplash.com/photo-1520975922284-8b456906c813?auto=format&fit=crop&w=300&q=80"
            },

            "bottom": {
                "name": "긴바지",
                "img": "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?auto=format&fit=crop&w=300&q=80"
            },

            "outer": {
                "name": "가디건",
                "img": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=300&q=80"
            },

            "link": "https://www.musinsa.com"
        }
    ]

    # =========================
    # 추가 추천
    # =========================

    if weather_main == "Rain":

        extra_items.append({
            "name": "우산 추천",
            "img": "https://images.unsplash.com/photo-1520975922284-8b456906c813?auto=format&fit=crop&w=300&q=80"
        })

    if wind_speed >= 5:

        extra_items.append({
            "name": "바람막이 추천",
            "img": "https://images.unsplash.com/photo-1542060748-10c28b62716f?auto=format&fit=crop&w=300&q=80"
        })

    if pm >= 3:

        extra_items.append({
            "name": "마스크 추천",
            "img": "https://images.unsplash.com/photo-1584515933487-779824d29309?auto=format&fit=crop&w=300&q=80"
        })

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
        extra_items=extra_items,

        style_name=style_name,
        style_desc=style_desc,
        mood_message=mood_message,

        style_img=style_img,

        icon_url=icon_url,
        city_name=city_name,

        selected_style=selected_style,

        error=error
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
