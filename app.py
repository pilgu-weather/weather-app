from flask import Flask, render_template, request
import requests
from datetime import datetime, timedelta
import random
import os

app = Flask(__name__)

API_KEY = os.getenv("OPENWEATHER_API_KEY")

if not API_KEY:

    raise ValueError(
        "OPENWEATHER_API_KEY environment variable is missing."
    )


BACKGROUND_MAP = {
    "01d": "background/clear_day.png",
    "01n": "background/clear_night.png",
    "02d": "background/cloudy_day.png",
    "03d": "background/cloudy_day.png",
    "04d": "background/cloudy_day.png",
    "02n": "background/cloudy_night.png",
    "03n": "background/cloudy_night.png",
    "04n": "background/cloudy_night.png",
    "09d": "background/rain_day.png",
    "10d": "background/rain_day.png",
    "09n": "background/rain_night.png",
    "10n": "background/rain_night.png",
    "13d": "background/snowy_day.png",
    "13n": "background/snowy_night.png",
    "50d": "background/mist_day.png",
    "50n": "background/mist_night.png",
    "11d": "background/thunder_day.png",
    "11n": "background/thunder_night.png",
}


STYLE_SEASON_FALLBACK = {
    "spring_warm": "spring",
    "spring_cool": "spring",
    "summer_cool": "summer",
    "fall_warm": "fall",
    "fall_cool": "fall",
}


def get_background_image(icon):

    return (
        "/static/"
        + BACKGROUND_MAP.get(
            icon,
            "background/cloudy_day.png"
        )
    )


def fetch_json(url):

    try:

        response = requests.get(url, timeout=5)

        if response.status_code != 200:

            return None, response.status_code

        return response.json(), response.status_code

    except:

        return None, None


def get_first_weather(data):

    weather_list = data.get("weather", [])

    if weather_list:

        return weather_list[0]

    return {}


def round_temp(value):

    if value is None:

        return None

    return round(value)


def get_weather_context(data, fallback_name="Seoul"):

    main = data.get("main", {})
    weather = get_first_weather(data)
    wind = data.get("wind", {})
    coord = data.get("coord", {})

    temp = round(main.get("temp", 0))
    icon = weather.get("icon", "03d")

    return {
        "city_name": data.get("name") or fallback_name,
        "temp": temp,
        "temp_min": round_temp(main.get("temp_min")),
        "temp_max": round_temp(main.get("temp_max")),
        "icon": icon,
        "weather_main": weather.get("main", "Clouds"),
        "background_image": get_background_image(icon),
        "feels_like": round(main.get("feels_like", temp)),
        "humidity": main.get("humidity", 0),
        "wind_speed": wind.get("speed", 0),
        "lat": coord.get("lat"),
        "lon": coord.get("lon"),
    }


def render_safe_template(**overrides):

    context = {
        "mode": "today",
        "temp": None,
        "temp_min": None,
        "temp_max": None,
        "feels_like": 0,
        "humidity": 0,
        "wind_speed": 0,
        "pm_text": "정보 없음",
        "today_message": "",
        "outfits": [],
        "icon_url": "",
        "city_name": "",
        "weather_main": "Default",
        "background_image": get_background_image("03d"),
        "hourly_forecast": [],
        "error": None,
    }

    context.update(overrides)

    return render_template(
        "index.html",
        **context
    )


def get_style_season(month, temp):

    if 3 <= month <= 5:

        if temp >= 17:

            return "spring_warm"

        return "spring_cool"

    if 6 <= month <= 8:

        if temp <= 23:

            return "summer_cool"

        return "summer"

    if 9 <= month <= 11:

        if temp >= 17:

            return "fall_warm"

        return "fall_cool"

    return "winter"


def get_style_folder_candidates(season, style_folder):

    seasons = [season]

    fallback_season = STYLE_SEASON_FALLBACK.get(season)

    if fallback_season:

        seasons.append(fallback_season)

    return [
        (
            current_season,
            f"static/styles/{current_season}/{style_folder}"
        )
        for current_season in seasons
    ]


def get_location_name(lat, lon):

    reverse_url = (
        f"https://api.openweathermap.org/geo/1.0/reverse"
        f"?lat={lat}&lon={lon}&limit=1&appid={API_KEY}"
    )

    try:

        data, status_code = fetch_json(reverse_url)

        if status_code != 200 or not data:

            return None

        location = data[0]
        local_names = location.get("local_names", {})

        return (
            local_names.get("ko")
            or location.get("name")
        )

    except:

        return None


def get_tomorrow_weather_main(weather_types):

    if "Thunderstorm" in weather_types:

        return "Thunderstorm"

    if "Snow" in weather_types:

        return "Snow"

    if "Rain" in weather_types or "Drizzle" in weather_types:

        return "Rain"

    if (
        "Mist" in weather_types
        or "Fog" in weather_types
        or "Haze" in weather_types
    ):

        return "Mist"

    clear_count = weather_types.count("Clear")
    clouds_count = weather_types.count("Clouds")

    if clouds_count >= clear_count and clouds_count > 0:

        return "Clouds"

    if clear_count > 0:

        return "Clear"

    return "Clouds"


def get_tomorrow_icon(weather_items):

    priority_groups = [
        ["Thunderstorm"],
        ["Snow"],
        ["Rain", "Drizzle"],
        ["Mist", "Fog", "Haze"],
    ]

    for group in priority_groups:

        for item in weather_items:

            if item.get("main") in group:

                return item.get("icon", "03d")

    clear_count = 0
    clouds_count = 0

    for item in weather_items:

        if item.get("main") == "Clear":

            clear_count += 1

        if item.get("main") == "Clouds":

            clouds_count += 1

    target = "Clouds"

    if clear_count > clouds_count:

        target = "Clear"

    for item in weather_items:

        if item.get("main") == target:

            return item.get("icon", "03d")

    return "03d"


def get_today_message(
    weather_main,
    temp,
    pm,
    wind_speed
):

    if weather_main == "Thunderstorm":

        return (
            "천둥과 강한 비가 예상돼요. "
            "외출 시 안전에 주의하세요."
        )

    if weather_main in ["Rain", "Drizzle"]:

        return (
            "우산은 필수예요. "
            "방수 가능한 신발을 추천해요."
        )

    if weather_main == "Snow":

        return (
            "미끄러운 길을 조심하세요. "
            "보온성과 방수성을 함께 챙겨보세요."
        )

    if pm >= 4:

        return (
            "미세먼지가 짙어요. "
            "마스크와 아우터를 챙겨주세요."
        )

    if wind_speed >= 8:

        return (
            "바람이 강하게 불어요. "
            "가벼운 아우터를 추천해요."
        )

    if temp >= 30:

        return (
            "무더운 날씨예요. "
            "밝고 통기성 좋은 룩을 추천해요."
        )

    if temp >= 26:

        return (
            "가볍고 시원한 스타일이 잘 어울리는 날이에요."
        )

    if temp >= 17:

        return (
            "가벼운 레이어드 스타일이 잘 어울려요."
        )

    if temp >= 10:

        return (
            "아침 저녁은 선선해요. "
            "얇은 아우터를 챙겨보세요."
        )

    return (
        "보온이 중요한 날씨예요. "
        "따뜻한 아우터를 추천해요."
    )


@app.route("/", methods=["GET", "POST"])
def home():

    mode = request.args.get("mode", "today")

    temp = None
    temp_min = None
    temp_max = None
    day_temp = None

    pm = None
    pm_text = None

    outfits = []

    icon_url = None
    city_name = None
    weather_main = "Default"
    background_image = get_background_image("03d")
    feels_like = 0
    humidity = 0
    wind_speed = 0

    lat = None
    lon = None

    error = None

    hourly_forecast = []

    # =========================
    # 도시 검색
    # =========================

    if request.method == "POST":

        city = request.form.get("city", "").strip()

        if not city:

            error = "도시를 찾을 수 없습니다."

            return render_safe_template(
                mode=mode,
                error=error
            )

        weather_url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={city}&appid={API_KEY}&units=metric"
        )

        data, status_code = fetch_json(weather_url)

        if status_code != 200 or not data:

            error = "도시를 찾을 수 없습니다."

            return render_safe_template(
                mode=mode,
                error=error
            )

        weather_context = get_weather_context(data, city)

        city_name = weather_context["city_name"]
        temp = weather_context["temp"]
        icon = weather_context["icon"]
        weather_main = weather_context["weather_main"]
        background_image = weather_context["background_image"]
        feels_like = weather_context["feels_like"]
        humidity = weather_context["humidity"]
        wind_speed = weather_context["wind_speed"]

        icon_url = (
            f"https://openweathermap.org/img/wn/{icon}@2x.png"
        )

        lat = weather_context["lat"]
        lon = weather_context["lon"]

    # =========================
    # 현재 위치
    # =========================

    elif request.args.get("lat") and request.args.get("lon"):

        try:

            lat = float(request.args.get("lat"))
            lon = float(request.args.get("lon"))

        except:

            error = "위치 정보를 불러오지 못했습니다."

            return render_safe_template(
                mode=mode,
                error=error
            )

        weather_url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        )

        data, status_code = fetch_json(weather_url)

        if status_code != 200 or not data:

            error = "현재 위치 날씨를 가져오지 못했습니다."

            return render_safe_template(
                mode=mode,
                error=error
            )

        weather_context = get_weather_context(
            data,
            "현재 위치"
        )

        city_name = (
            get_location_name(lat, lon)
            or weather_context["city_name"]
            or "현재 위치"
        )

        temp = weather_context["temp"]
        icon = weather_context["icon"]
        weather_main = weather_context["weather_main"]
        background_image = weather_context["background_image"]
        feels_like = weather_context["feels_like"]
        humidity = weather_context["humidity"]
        wind_speed = weather_context["wind_speed"]

        icon_url = (
            f"https://openweathermap.org/img/wn/{icon}@2x.png"
        )

    # =========================
    # 기본 서울
    # =========================

    else:

        city = "Seoul"

        weather_url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?q={city}&appid={API_KEY}&units=metric"
        )

        data, status_code = fetch_json(weather_url)

        if status_code != 200 or not data:

            error = "날씨 정보를 가져오지 못했습니다."

            return render_safe_template(
                mode=mode,
                error=error
            )

        weather_context = get_weather_context(data, city)

        city_name = weather_context["city_name"]
        temp = weather_context["temp"]
        icon = weather_context["icon"]
        weather_main = weather_context["weather_main"]
        background_image = weather_context["background_image"]
        feels_like = weather_context["feels_like"]
        humidity = weather_context["humidity"]
        wind_speed = weather_context["wind_speed"]

        icon_url = (
            f"https://openweathermap.org/img/wn/{icon}@2x.png"
        )

        lat = weather_context["lat"]
        lon = weather_context["lon"]

    # =========================
    # Forecast API
    # =========================

    if lat is not None and lon is not None:

        forecast_url = (
            f"https://api.openweathermap.org/data/2.5/forecast"
            f"?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        )

        forecast_data, forecast_status_code = fetch_json(forecast_url)

    else:

        forecast_data = {}
        forecast_status_code = None

    if forecast_status_code != 200 or not forecast_data:

        forecast_data = {}

    kst_now = datetime.utcnow() + timedelta(hours=9)

    today = kst_now.strftime("%Y-%m-%d")

    tomorrow = (
        kst_now + timedelta(days=1)
    ).strftime("%Y-%m-%d")

    now_hour = kst_now.hour

    today_temps = []
    tomorrow_temps = []

    today_daytime = []
    tomorrow_daytime = []

    rain_today = False
    rain_tomorrow = False

    tomorrow_icon = icon_url
    tomorrow_icon_code = icon
    tomorrow_weather_types = []
    tomorrow_weather_items = []
    tomorrow_feels_like = []
    tomorrow_humidity = []
    tomorrow_wind_speed = []

    # =========================
    # HOURLY FORECAST
    # =========================

    if isinstance(forecast_data.get("list"), list):

        for item in forecast_data.get("list", []):

            if not isinstance(item, dict):

                continue

            dt_txt = item.get("dt_txt")

            if not dt_txt:

                continue

            try:

                utc_date = dt_txt.split(" ")[0]

                raw_hour = int(
                    dt_txt.split(" ")[1].split(":")[0]
                )

            except:

                continue

            # UTC → KST
            kst_hour = (raw_hour + 9) % 24

            # 날짜 보정
            forecast_date = utc_date

            if raw_hour + 9 >= 24:

                forecast_date = (
                    datetime.strptime(
                        utc_date,
                        "%Y-%m-%d"
                    ) + timedelta(days=1)
                ).strftime("%Y-%m-%d")

            item_main = item.get("main", {})
            item_weather = get_first_weather(item)

            current_temp = item_main.get("temp", temp)

            weather_type = item_weather.get("main", "Clouds")

            weather_icon = item_weather.get("icon", "03d")

            # =========================
            # TODAY → 현재 이후 + 내일 전체
            # =========================

            if mode == "today":

                if (
                    forecast_date == today
                    and kst_hour >= now_hour
                ) or (
                    forecast_date == tomorrow
                ):

                    hourly_forecast.append({

                        "time": f"{kst_hour:02d}",

                        "icon": weather_icon,

                        "temp": round(current_temp)

                    })

            # =========================
            # TOMORROW → 06~21 고정
            # =========================

            if (
                mode == "tomorrow"
                and forecast_date == tomorrow
                and kst_hour in [6, 9, 12, 15, 18, 21]
            ):

                hourly_forecast.append({

                    "time": f"{kst_hour:02d}",

                    "icon": weather_icon,

                        "temp": round(current_temp)

                })

            if (
                forecast_date == tomorrow
                and kst_hour in [6, 9, 12, 15, 18, 21]
            ):

                tomorrow_weather_types.append(weather_type)
                tomorrow_weather_items.append({
                    "main": weather_type,
                    "icon": weather_icon
                })

            # =========================
            # TODAY DATA
            # =========================

            if forecast_date == today:

                today_temps.append(current_temp)

                if 12 <= kst_hour <= 15:

                    today_daytime.append(current_temp)

                if (
                    6 <= kst_hour <= 21
                    and weather_type in [
                        "Rain",
                        "Drizzle",
                        "Thunderstorm"
                    ]
                ):

                    rain_today = True

            # =========================
            # TOMORROW DATA
            # =========================

            if forecast_date == tomorrow:

                tomorrow_temps.append(current_temp)

                if 12 <= kst_hour <= 15:

                    tomorrow_daytime.append(current_temp)
                    tomorrow_feels_like.append(
                        item_main.get("feels_like", current_temp)
                    )
                    tomorrow_humidity.append(
                        item_main.get("humidity", humidity)
                    )
                    tomorrow_wind_speed.append(
                        item.get("wind", {}).get("speed", wind_speed)
                    )
                    tomorrow_icon_code = weather_icon

                    tomorrow_icon = (
                        f"https://openweathermap.org/img/wn/{weather_icon}@2x.png"
                    )

                if (
                    6 <= kst_hour <= 21
                    and weather_type in [
                        "Rain",
                        "Drizzle",
                        "Thunderstorm"
                    ]
                ):

                    rain_tomorrow = True

    # =========================
    # TODAY MODE
    # =========================

    if mode == "today":

        if today_temps:

            temp_min = round(min(today_temps))
            temp_max = round(max(today_temps))

        else:

            temp_min = weather_context["temp_min"]
            temp_max = weather_context["temp_max"]

        if today_daytime:

            day_temp = round(
                sum(today_daytime) / len(today_daytime)
            )

        else:

            day_temp = temp

        rain_mode = rain_today

    # =========================
    # TOMORROW MODE
    # =========================

    else:

        icon_url = tomorrow_icon
        tomorrow_icon_code = get_tomorrow_icon(
            tomorrow_weather_items
        )
        background_image = get_background_image(tomorrow_icon_code)
        weather_main = get_tomorrow_weather_main(
            tomorrow_weather_types
        )

        if tomorrow_temps:

            temp_min = round(min(tomorrow_temps))
            temp_max = round(max(tomorrow_temps))

            temp = temp_max

        else:

            temp = 0
            temp_min = None
            temp_max = None

        if tomorrow_daytime:

            day_temp = round(
                sum(tomorrow_daytime) / len(tomorrow_daytime)
            )
            feels_like = round(
                sum(tomorrow_feels_like) / len(tomorrow_feels_like)
            )
            humidity = round(
                sum(tomorrow_humidity) / len(tomorrow_humidity)
            )
            wind_speed = round(
                sum(tomorrow_wind_speed) / len(tomorrow_wind_speed),
                1
            )

        else:

            day_temp = temp

        rain_mode = rain_tomorrow

    # =========================
    # 미세먼지
    # =========================

    if lat is not None and lon is not None:

        air_url = (
            f"https://api.openweathermap.org/data/2.5/air_pollution"
            f"?lat={lat}&lon={lon}&appid={API_KEY}"
        )

        air_data, air_status_code = fetch_json(air_url)

    else:

        air_data = None
        air_status_code = None

    try:

        pm25 = (
            air_data
            .get("list", [{}])[0]
            .get("components", {})
            .get("pm2_5", 0)
        )

    except:

        pm25 = 0

    # =========================
    # PM2.5 기준
    # =========================

    if air_status_code != 200 or not air_data:

        pm_text = "정보 없음"

    elif pm25 <= 59:

        pm_text = "좋음"

    elif pm25 <= 99:

        pm_text = "보통"

    elif pm25 <= 150:

        pm_text = "약간 나쁨"

    else:

        pm_text = "나쁨"

    # Dust 추천 기준
    if pm25 >= 151:

        pm = 4

    else:

        pm = 1

    # =========================
    # 계절 판단
    # =========================

    if temp_min is not None and temp_max is not None:

        temp_gap = temp_max - temp_min

    else:

        temp_gap = 0

    effective_temp = day_temp

    if effective_temp is None:

        effective_temp = temp

    if feels_like is not None:

        effective_temp = min(effective_temp, feels_like)

    if wind_speed >= 8:

        effective_temp -= 3

    elif wind_speed >= 6:

        effective_temp -= 2

    elif wind_speed >= 4:

        effective_temp -= 1

    if temp_gap >= 10:

        effective_temp -= 2

    elif temp_gap >= 6:

        effective_temp -= 1

    selected_date = today

    if mode != "today":

        selected_date = tomorrow

    season_month = datetime.strptime(
        selected_date,
        "%Y-%m-%d"
    ).month

    season = get_style_season(
        season_month,
        effective_temp
    )

    # =========================
    # 스타일
    # =========================

    styles = [

        {
            "folder": "casual",
            "title": "Casual",
            "desc": "편안하고 자연스러운 데일리룩"
        },

        {
            "folder": "urban",
            "title": "Urban",
            "desc": "도시 감성 데일리룩"
        },

        {
            "folder": "street",
            "title": "Street",
            "desc": "트렌디한 스트릿 무드"
        },

        {
            "folder": "minimal",
            "title": "Minimal",
            "desc": "깔끔하고 미니멀한 감성룩"
        }

    ]

    if rain_mode:

        styles.insert(0, {

            "folder": "rain",

            "title": "Rainy day",

            "desc": "오늘은 우산과 바람막이 추천"

        })

    if pm >= 4:

        styles.insert(0, {

            "folder": "dust",

            "title": "Dust Protection",

            "desc": "마스크와 고프코어 기반 스타일"

        })

    if (
        season.startswith("spring")
        or season.startswith("fall")
    ) and temp_gap >= 6:

        styles.insert(0, {

            "folder": "layered",

            "title": "Layered Look",

            "desc": "오늘은 가벼운 외투와 레이어드 추천"

        })

    # =========================
    # 이미지
    # =========================

    outfits = []

    for style in styles:

        try:

            image_list = []
            selected_season = season

            for candidate_season, folder_path in (
                get_style_folder_candidates(
                    season,
                    style["folder"]
                )
            ):

                if not os.path.isdir(folder_path):

                    continue

                image_list = os.listdir(folder_path)

                image_list = [

                    img for img in image_list

                    if img.endswith((
                        ".png",
                        ".jpg",
                        ".jpeg",
                        ".webp"
                    ))
                ]

                if image_list:

                    selected_season = candidate_season
                    break

            if not image_list:

                raise FileNotFoundError

            random_image = random.choice(image_list)

            img_path = (
                f"/static/styles/"
                f"{selected_season}/"
                f"{style['folder']}/"
                f"{random_image}"
            )

        except:

            img_path = "/static/styles/default.png"

        outfits.append({

            "title": style["title"],
            "desc": style["desc"],
            "img": img_path

        })

    today_message = get_today_message(
        weather_main,
        temp,
        pm,
        wind_speed
    )

    return render_template(

        "index.html",

        mode=mode,

        temp=temp,
        temp_min=temp_min,
        temp_max=temp_max,
        feels_like=feels_like,
        humidity=humidity,
        wind_speed=wind_speed,

        pm_text=pm_text,
        today_message=today_message,

        outfits=outfits,

        icon_url=icon_url,
        city_name=city_name,
        weather_main=weather_main,
        background_image=background_image,

        hourly_forecast=hourly_forecast,

        error=error
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
