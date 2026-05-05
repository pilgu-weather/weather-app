from flask import Flask, render_template, request
import requests

app = Flask(__name__)

API_KEY = "2fd339c206c2fa601c64bc589a4750e9"

@app.route("/", methods=["GET", "POST"])
def home():
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    temp = None
    feels_like = None
    pm = None
    pm_text = None
    outfits = []
    extra_items = []
    icon_url = None
    city_name = None

    # 💥 ✅ 1. GPS로 들어온 경우 (GET)
    # 💥 GET (현재 위치)
    if lat and lon:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        data = requests.get(url).json()

        city_name = data["name"]
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        real_temp = feels_like

        weather_main = data["weather"][0]["main"]
        wind_speed = data["wind"]["speed"]

        icon = data["weather"][0]["icon"]
        icon_url = f"https://openweathermap.org/img/wn/{icon}@2x.png"

        # 🌫 미세먼지
        air_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        air_data = requests.get(air_url).json()

        pm = air_data["list"][0]["main"]["aqi"]

        # 💥 👉 이게 빠졌던 부분이다 (코디 + 아이템)

        # 👕 코디 추천
        if real_temp >= 28:
            outfits = [
                {
                    "top": {"name": "반팔",
                            "img": "https://images.unsplash.com/photo-1520975922284-8b456906c813?auto=format&fit=crop&w=300&q=80"},
                    "bottom": {"name": "반바지",
                               "img": "https://images.unsplash.com/photo-1593030761757-71fae45fa0e7?auto=format&fit=crop&w=300&q=80"},
                    "outer": None,
                    "link": "https://www.musinsa.com"
                }
            ]

        elif real_temp >= 20:
            outfits = [
                {
                    "top": {"name": "긴팔 티",
                            "img": "https://images.unsplash.com/photo-1516826957135-700dedea698c?auto=format&fit=crop&w=300&q=80"},
                    "bottom": {"name": "긴바지",
                               "img": "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?auto=format&fit=crop&w=300&q=80"},
                    "outer": None,
                    "link": "https://www.musinsa.com"
                }
            ]

        else:
            outfits = [
                {
                    "top": {"name": "후드티",
                            "img": "https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=300&q=80"},
                    "bottom": {"name": "청바지",
                               "img": "https://images.unsplash.com/photo-1542272604-787c3835535d?auto=format&fit=crop&w=300&q=80"},
                    "outer": {"name": "자켓",
                              "img": "https://images.unsplash.com/photo-1542060748-10c28b62716f?auto=format&fit=crop&w=300&q=80"},
                    "link": "https://www.musinsa.com"
                }
            ]

        # 🌧 비
        if weather_main == "Rain":
            extra_items.append({
                "name": "우산",
                "img": "https://images.unsplash.com/photo-1520975922284-8b456906c813?auto=format&fit=crop&w=300&q=80"
            })

        # 💨 바람
        if wind_speed >= 5:
            extra_items.append({
                "name": "바람막이",
                "img": "https://images.unsplash.com/photo-1542060748-10c28b62716f?auto=format&fit=crop&w=300&q=80"
            })

        # 😷 미세먼지
        if pm >= 3:
            extra_items.append({
                "name": "마스크 추천(미세먼지)",
                "img": "https://images.unsplash.com/photo-1584515933487-779824d29309?auto=format&fit=crop&w=300&q=80"
            })

            if pm:
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

    # 💥 ✅ 2. 도시 입력 (POST)
    elif request.method == "POST":
        city = request.form["city"]

        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        data = requests.get(url).json()

        city_name = city
        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        real_temp = feels_like

        weather_main = data["weather"][0]["main"]
        wind_speed = data["wind"]["speed"]

        icon = data["weather"][0]["icon"]
        icon_url = f"https://openweathermap.org/img/wn/{icon}@2x.png"

        lat = data["coord"]["lat"]
        lon = data["coord"]["lon"]

        air_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
        air_data = requests.get(air_url).json()

        pm = air_data["list"][0]["main"]["aqi"]

        # 🔥 ❗ 미세먼지 텍스트 변환 (위치 이동됨)
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

        # 👕 코디 추천
        if real_temp >= 28:
            outfits = [
                {
                    "top": {"name": "반팔", "img": "https://images.unsplash.com/photo-1520975922284-8b456906c813?auto=format&fit=crop&w=300&q=80"},
                    "bottom": {"name": "반바지", "img": "https://images.unsplash.com/photo-1593030761757-71fae45fa0e7?auto=format&fit=crop&w=300&q=80"},
                    "outer": None,
                    "link": "https://www.musinsa.com"
                }
            ]

        elif real_temp >= 20:
            outfits = [
                {
                    "top": {"name": "긴팔 티", "img": "https://images.unsplash.com/photo-1516826957135-700dedea698c?auto=format&fit=crop&w=300&q=80"},
                    "bottom": {"name": "긴바지", "img": "https://images.unsplash.com/photo-1523381210434-271e8be1f52b?auto=format&fit=crop&w=300&q=80"},
                    "outer": None,
                    "link": "https://www.musinsa.com"
                }
            ]

        else:
            outfits = [
                {
                    "top": {"name": "후드티", "img": "https://images.unsplash.com/photo-1556821840-3a63f95609a7?auto=format&fit=crop&w=300&q=80"},
                    "bottom": {"name": "청바지", "img": "https://images.unsplash.com/photo-1542272604-787c3835535d?auto=format&fit=crop&w=300&q=80"},
                    "outer": {"name": "자켓", "img": "https://images.unsplash.com/photo-1542060748-10c28b62716f?auto=format&fit=crop&w=300&q=80"},
                    "link": "https://www.musinsa.com"
                }
            ]

        # 🌧 비
        if weather_main == "Rain":
            extra_items.append({
                "name": "우산",
                "img": "https://images.unsplash.com/photo-1520975922284-8b456906c813?auto=format&fit=crop&w=300&q=80"
            })

        # 💨 바람
        if wind_speed >= 5:
            extra_items.append({
                "name": "바람막이",
                "img": "https://images.unsplash.com/photo-1542060748-10c28b62716f?auto=format&fit=crop&w=300&q=80"
            })

        # 😷 미세먼지
        if pm >= 3:
            extra_items.append({
                "name": "마스크 추천(미세먼지)",
                "img": "https://images.unsplash.com/photo-1584515933487-779824d29309?auto=format&fit=crop&w=300&q=80"
            })

    return render_template(
        "index.html",
        temp=temp,
        feels_like=feels_like,
        pm=pm,
        pm_text=pm_text,
        outfits=outfits,
        extra_items=extra_items,
        icon_url=icon_url,
        city_name=city_name
    )

if __name__ == "__main__":
    app.run(debug=True)