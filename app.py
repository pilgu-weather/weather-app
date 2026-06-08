from flask import Flask, render_template, request, jsonify, abort
import requests
from datetime import datetime, timedelta
import random
import os
import re
import sqlite3
import html

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_DB_PATH = os.getenv(
    "FEEDBACK_DB_PATH",
    os.path.join(
        BASE_DIR,
        "weatherfit_feedback.db"
    )
)

API_KEY = os.getenv("OPENWEATHER_API_KEY")

print(
    "OPENWEATHER_API_KEY exists:",
    bool(API_KEY)
)

if not API_KEY:

    raise ValueError(
        "OPENWEATHER_API_KEY environment variable is missing."
    )


@app.route("/health")
def health():

    return "ok", 200


def get_feedback_db():

    db_dir = os.path.dirname(FEEDBACK_DB_PATH)

    if db_dir:

        os.makedirs(db_dir, exist_ok=True)

    return sqlite3.connect(
        FEEDBACK_DB_PATH,
        timeout=10
    )


def init_feedback_db():

    with get_feedback_db() as conn:

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS recommendation_feedbacks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                mode TEXT,
                city_name TEXT,
                temp REAL,
                feels_like REAL,
                effective_temp REAL,
                weather_main TEXT,
                outfit_title TEXT,
                outfit_desc TEXT,
                rating TEXT,
                reason TEXT,
                page_url TEXT,
                user_agent TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS outfit_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                mode TEXT,
                city_name TEXT,
                temp REAL,
                weather_main TEXT,
                outfit_title TEXT,
                outfit_desc TEXT,
                outfit_id TEXT,
                outfit_image_url TEXT,
                report_reason TEXT,
                page_url TEXT,
                user_agent TEXT
            )
            """
        )

        report_columns = [
            column[1]
            for column in conn.execute(
                "PRAGMA table_info(outfit_reports)"
            ).fetchall()
        ]

        if "outfit_id" not in report_columns:

            conn.execute(
                "ALTER TABLE outfit_reports ADD COLUMN outfit_id TEXT"
            )

        if "outfit_image_url" not in report_columns:

            conn.execute(
                "ALTER TABLE outfit_reports ADD COLUMN outfit_image_url TEXT"
            )


def now_timestamp():

    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def get_request_payload():

    payload = request.get_json(silent=True) or {}

    if not isinstance(payload, dict):

        return {}

    return payload


@app.route("/feedback", methods=["POST"])
def save_feedback():

    payload = get_request_payload()

    try:

        init_feedback_db()

        with get_feedback_db() as conn:

            conn.execute(
                """
                INSERT INTO recommendation_feedbacks (
                    created_at,
                    mode,
                    city_name,
                    temp,
                    feels_like,
                    effective_temp,
                    weather_main,
                    outfit_title,
                    outfit_desc,
                    rating,
                    reason,
                    page_url,
                    user_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now_timestamp(),
                    payload.get("mode"),
                    payload.get("city_name"),
                    payload.get("temp"),
                    payload.get("feels_like"),
                    payload.get("effective_temp"),
                    payload.get("weather_main"),
                    payload.get("outfit_title"),
                    payload.get("outfit_desc"),
                    payload.get("rating"),
                    payload.get("reason"),
                    payload.get("page_url"),
                    request.headers.get("User-Agent", "")
                )
            )

    except Exception as error:

        print("SQLite feedback insert failed:", error)

        return jsonify({"ok": False}), 500

    return jsonify({"ok": True})


@app.route("/report", methods=["POST"])
def save_report():

    payload = get_request_payload()

    try:

        init_feedback_db()

        with get_feedback_db() as conn:

            conn.execute(
                """
                INSERT INTO outfit_reports (
                    created_at,
                    mode,
                    city_name,
                    temp,
                    weather_main,
                    outfit_title,
                    outfit_desc,
                    outfit_id,
                    outfit_image_url,
                    report_reason,
                    page_url,
                    user_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now_timestamp(),
                    payload.get("mode"),
                    payload.get("city_name"),
                    payload.get("temp"),
                    payload.get("weather_main"),
                    payload.get("outfit_title"),
                    payload.get("outfit_desc"),
                    payload.get("outfit_id"),
                    payload.get("outfit_image_url"),
                    payload.get("report_reason"),
                    payload.get("page_url"),
                    request.headers.get("User-Agent", "")
                )
            )

    except Exception as error:

        print("SQLite report insert failed:", error)

        return jsonify({"ok": False}), 500

    return jsonify({"ok": True})


def fetch_feedback_rows():

    init_feedback_db()

    with get_feedback_db() as conn:

        conn.row_factory = sqlite3.Row

        feedbacks = conn.execute(
            """
            SELECT
                id,
                created_at,
                mode,
                city_name,
                temp,
                feels_like,
                effective_temp,
                weather_main,
                outfit_title,
                outfit_desc,
                rating,
                reason,
                page_url,
                user_agent
            FROM recommendation_feedbacks
            ORDER BY id DESC
            LIMIT 100
            """
        ).fetchall()

        reports = conn.execute(
            """
            SELECT
                id,
                created_at,
                mode,
                city_name,
                temp,
                weather_main,
                outfit_title,
                outfit_desc,
                outfit_id,
                outfit_image_url,
                report_reason,
                page_url,
                user_agent
            FROM outfit_reports
            ORDER BY id DESC
            LIMIT 100
            """
        ).fetchall()

    return feedbacks, reports


def render_admin_table(rows, columns):

    header = "".join(
        f"<th>{html.escape(column)}</th>"
        for column in columns
    )

    body_rows = []

    for row in rows:

        cells = []

        for column in columns:

            value = str(row[column] or "")
            escaped_value = html.escape(value)

            if column == "outfit_image_url" and value:

                cells.append(
                    "<td>"
                    f"<a href=\"{escaped_value}\" target=\"_blank\">"
                    f"<img class=\"admin-thumb\" src=\"{escaped_value}\" "
                    "alt=\"신고 이미지\">"
                    "</a>"
                    f"<div class=\"admin-image-link\">{escaped_value}</div>"
                    "</td>"
                )

            else:

                cells.append(f"<td>{escaped_value}</td>")

        cells = "".join(cells)

        body_rows.append(f"<tr>{cells}</tr>")

    if not body_rows:

        body_rows.append(
            f"<tr><td colspan=\"{len(columns)}\">No data</td></tr>"
        )

    return (
        "<table>"
        f"<thead><tr>{header}</tr></thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        "</table>"
    )


@app.route("/admin/feedback")
def admin_feedback():

    admin_key = os.getenv("ADMIN_KEY")

    if not admin_key or request.args.get("key") != admin_key:

        abort(403)

    feedback_columns = [
        "id",
        "created_at",
        "mode",
        "city_name",
        "temp",
        "feels_like",
        "effective_temp",
        "weather_main",
        "outfit_title",
        "outfit_desc",
        "rating",
        "reason",
        "page_url",
        "user_agent"
    ]

    report_columns = [
        "id",
        "created_at",
        "mode",
        "city_name",
        "temp",
        "weather_main",
        "outfit_title",
        "outfit_desc",
        "outfit_id",
        "outfit_image_url",
        "report_reason",
        "page_url",
        "user_agent"
    ]

    feedbacks, reports = fetch_feedback_rows()

    return f"""
    <!doctype html>
    <html lang="ko">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Weather Fit Feedback</title>
        <style>
            body {{
                margin: 0;
                padding: 24px;
                font-family: -apple-system, BlinkMacSystemFont, sans-serif;
                background: #101216;
                color: #f5f5f7;
            }}
            h1, h2 {{
                margin: 0 0 16px;
            }}
            section {{
                margin-top: 28px;
            }}
            .table-wrap {{
                overflow-x: auto;
                border: 1px solid rgba(255,255,255,0.14);
                border-radius: 14px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                min-width: 980px;
            }}
            th, td {{
                padding: 10px 12px;
                border-bottom: 1px solid rgba(255,255,255,0.10);
                text-align: left;
                vertical-align: top;
                font-size: 13px;
            }}
            th {{
                position: sticky;
                top: 0;
                background: #1c1f24;
                font-size: 12px;
            }}
            td {{
                color: rgba(255,255,255,0.82);
            }}
            .admin-thumb {{
                width: 72px;
                height: 96px;
                object-fit: cover;
                object-position: center top;
                border-radius: 10px;
                display: block;
                margin-bottom: 8px;
            }}
            .admin-image-link {{
                max-width: 220px;
                word-break: break-all;
                color: rgba(255,255,255,0.62);
                font-size: 11px;
            }}
        </style>
    </head>
    <body>
        <h1>Weather Fit Feedback</h1>

        <section>
            <h2>추천 평가 목록</h2>
            <div class="table-wrap">
                {render_admin_table(feedbacks, feedback_columns)}
            </div>
        </section>

        <section>
            <h2>신고 목록</h2>
            <div class="table-wrap">
                {render_admin_table(reports, report_columns)}
            </div>
        </section>
    </body>
    </html>
    """


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


ALERT_EVENT_MAP = [
    (["\\ud3ed\\uc5fc", "heat"], "\\ud3ed\\uc5fc"),
    (["\\ud55c\\ud30c", "cold", "freeze", "frost"], "\\ud55c\\ud30c"),
    (["\\ud638\\uc6b0", "heavy rain", "rainstorm", "flood"], "\\ud638\\uc6b0"),
    (["\\uac15\\ud48d", "wind", "gale"], "\\uac15\\ud48d"),
    (["\\ud0dc\\ud48d", "typhoon", "tropical cyclone"], "\\ud0dc\\ud48d"),
    (["\\uac74\\uc870", "dry", "fire weather", "red flag"], "\\uac74\\uc870"),
    (["\\uc624\\uc874", "ozone"], "\\uc624\\uc874"),
    (["\\ud669\\uc0ac", "yellow dust", "dust", "sand"], "\\ud669\\uc0ac"),
]


def decode_alert_text(value):

    return value.encode("utf-8").decode("unicode_escape")


def normalize_alert_area(city_name):

    if not city_name:

        return ""

    return re.sub(
        r"\s+",
        " ",
        str(city_name)
    ).strip()


def get_alert_level(event_text):

    lower_text = event_text.lower()
    warning_text = decode_alert_text("\\uacbd\\ubcf4")

    if warning_text in event_text or "warning" in lower_text:

        return "warning", warning_text

    return "advisory", decode_alert_text("\\uc8fc\\uc758\\ubcf4")


def get_alert_type(event_text):

    lower_text = event_text.lower()

    for keywords, label in ALERT_EVENT_MAP:

        for keyword in keywords:

            decoded_keyword = decode_alert_text(keyword)

            if (
                decoded_keyword in event_text
                or keyword in lower_text
            ):

                return decode_alert_text(label)

    return None


def get_weather_alert_notice(lat, lon, city_name):

    if lat is None or lon is None:

        return None

    alert_url = (
        f"https://api.openweathermap.org/data/3.0/onecall"
        f"?lat={lat}&lon={lon}"
        f"&exclude=current,minutely,hourly,daily"
        f"&appid={API_KEY}"
    )

    alert_data, alert_status_code = fetch_json(alert_url)

    if alert_status_code != 200 or not alert_data:

        return None

    alerts = alert_data.get("alerts", [])

    if not isinstance(alerts, list):

        return None

    for alert in alerts:

        if not isinstance(alert, dict):

            continue

        event_text = " ".join([
            str(alert.get("event", "")),
            str(alert.get("description", ""))
        ])

        alert_type = get_alert_type(event_text)

        if not alert_type:

            continue

        level, level_text = get_alert_level(event_text)
        area = normalize_alert_area(city_name)
        prefix = decode_alert_text("\\u26a0\\ufe0f")
        suffix = decode_alert_text("\\ubc1c\\ud6a8")

        if area:

            text = f"{prefix} {area} {alert_type}{level_text} {suffix}"

        else:

            text = f"{prefix} {alert_type}{level_text} {suffix}"

        return {
            "text": text,
            "level": level
        }

    return None


def get_uv_index(lat, lon):

    if lat is None or lon is None:

        return None

    uv_url = (
        f"https://api.openweathermap.org/data/3.0/onecall"
        f"?lat={lat}&lon={lon}"
        f"&exclude=minutely,hourly,daily,alerts"
        f"&appid={API_KEY}"
    )

    uv_data, uv_status_code = fetch_json(uv_url)

    if uv_status_code != 200 or not uv_data:

        return None

    current = uv_data.get("current", {})

    return current.get("uvi")


def render_safe_template(**overrides):

    context = {
        "mode": "today",
        "temp": None,
        "temp_min": None,
        "temp_max": None,
        "feels_like": 0,
        "effective_temp": None,
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
        "weather_alert": None,
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
    wind_speed,
    temp_gap=0,
    day_temp=None,
    effective_temp=None,
    effective_temp_reasons=None,
    uv_index=None
):

    rain_messages = [
        "비 예보가 있어요. 우산과 젖어도 부담 없는 신발을 챙겨주세요.",
        "오늘은 비에 대비해 겉옷을 더하면 좋아요.",
        "빗길이 예상돼요. 긴 바지와 미끄럽지 않은 신발을 추천해요.",
        "우산을 들기 좋은 날이에요. 가벼운 겉옷도 함께 챙겨주세요.",
        "비가 오면 체감이 낮아져요. 얇은 옷보다는 한 겹 더해보세요.",
        "습한 날씨라 통풍이 필요해요.",
        "어두운 컬러와 실용적인 겉옷이 잘 맞아요.",
        "비 오는 날엔 가벼운 레이어드와 레인부츠가 든든해요.",
    ]

    thunder_messages = [
        "천둥 가능성이 있어요. 외출은 짧게, 겉옷은 든든하게 챙겨주세요.",
        "강한 비가 올 수 있어요. 우산과 방수 겉옷이 실용적이에요.",
        "날씨 변화가 거칠 수 있어요. 활동성 좋은 긴 옷을 추천해요.",
        "천둥 예보가 있어요. 미끄럽지 않은 신발을 골라주세요.",
        "비바람이 강해요. 얇은 옷은 피해주세요.",
        "비바람이 강할 수 있어요. 짧은 하의보다는 긴 하의가 좋아요.",
        "방수성과 보온감을 함께 챙겨주세요.",
        "외출 전 날씨를 한 번 더 확인하고 우산을 준비해주세요.",
        "강한 소나기에 대비해 젖어도 티가 덜 나는 컬러를 추천해요.",
    ]

    wind_messages = [
        "바람이 강해요. 가벼운 겉옷을 꼭 챙겨주세요.",
        "체감이 더 낮을 수 있어요. 긴 소매가 안정적이에요.",
        "바람 부는 날엔 얇은 옷 하나보다 레이어드가 좋아요.",
        "흩날리는 소재보다 몸에 편하게 잡히는 옷을 추천해요.",
        "강풍에는 짧은 하의보다 긴 하의가 더 편해요.",
        "오늘은 바람막이나 레이어드 셔츠를 추천해요.",
        "바람 때문에 쌀쌀하게 느껴질 수 있어요. 한 겹 더해보세요.",
        "가벼운 겉옷을 더하면 편안한 날이 될거예요.",
        "실제 온도보다 차갑게 느껴질 수 있어요.",
    ]

    gap_messages = [
        "일교차가 커요. 입고 벗기 쉬운 레이어드가 좋아요.",
        "아침과 낮의 온도 차가 있어요. 얇은 겉옷을 챙겨주세요.",
        "낮엔 가볍고 아침엔 쌀쌀할 수 있어요. 레이어드가 좋아요.",
        "큰 일교차엔 긴 소매와 가벼운 겉옷을 추천해요.",
        "온도 변화가 큰 날이에요. 너무 짧은 코디는 피하는 게 좋아요.",
        "아침저녁을 생각하면 한 겹 더하는 편이 안전해요.",
        "일교차가 있는 날엔 니트나 레이어드 셔츠가 잘 맞아요.",
        "큰 온도 차에 대비해 겉옷을 들고 나가면 좋아요.",
    ]

    effective_feels_like_messages = [
        "체감온도가 낮은 날이에요. 실제 기온보다 조금 따뜻하게 입는 게 좋아요.",
        "숫자보다 몸으로 느끼는 온도가 낮아요. 얇은 옷만 입기엔 애매한 날이에요.",
        "체감온도를 보면 한 겹 더 챙기는 쪽이 안정적이에요.",
        "기온은 괜찮아 보여도 체감은 더 서늘해요. 긴팔이나 가벼운 아우터를 추천해요.",
        "오늘은 체감온도 기준으로 보면 살짝 보수적으로 입는 게 좋아요.",
    ]

    effective_wind_messages = [
        "해가 있어도 바람이 강해요. 얇은 긴팔이나 가벼운 아우터를 추천해요.",
        "바람 때문에 실제보다 쌀쌀하게 느껴질 수 있어요. 가볍게 걸칠 옷을 챙겨보세요.",
        "바람을 생각하면 짧고 얇은 옷만으로는 애매할 수 있어요.",
        "기온은 괜찮아도 바람이 체감을 낮춰요. 한 겹 더하는 쪽이 좋아요.",
        "오늘은 바람 기준으로 코디를 조금 따뜻하게 잡는 게 좋아요.",
    ]

    effective_gap_messages = [
        "일교차가 큰 날이에요. 낮엔 가볍게, 저녁엔 걸칠 옷을 챙겨보세요.",
        "아침저녁 온도 차가 있어요. 레이어드하기 좋은 코디를 추천해요.",
        "낮 기온만 보고 얇게 입으면 저녁에 쌀쌀할 수 있어요.",
        "온도 변화가 큰 날이라 벗고 입기 쉬운 옷이 좋아요.",
        "일교차를 보면 얇은 옷 하나보다는 가벼운 레이어드가 더 맞아요.",
    ]

    effective_mixed_messages = [
        "바람과 일교차 때문에 실제보다 쌀쌀하게 느껴질 수 있어요.",
        "체감온도와 바람을 보면 얇은 옷만 입기엔 애매한 날이에요.",
        "오늘은 체감 요소가 겹쳐서 추천을 더 따뜻하게 잡았어요.",
        "바람, 체감온도, 일교차를 함께 보면 가볍게만 입기엔 조심스러운 날이에요.",
    ]

    uv_messages = [
        "자외선이 강한 날이에요. 야외활동 시 햇볕을 주의하세요.",
        "맑은 날씨만큼 자외선도 강해요.",
        "기온은 높지 않아도 햇볕은 강하게 느껴질 수 있어요.",
        "한낮 외출 시 모자나 선글라스가 도움이 될 수 있어요.",
        "햇볕이 강한 시간대에는 그늘을 활용해보세요.",
        "자외선이 강해 피부가 쉽게 자극받을 수 있어요.",
        "맑고 화창하지만 자외선은 높은 편이에요.",
        "외출이 길다면 자외선 차단을 고려해보세요.",
    ]

    temperature_messages = {
        "hot": [
            "무더운 날이에요. 통풍 좋은 소재와 밝은 컬러를 추천해요.",
            "햇볕이 강하게 느껴질 수 있어요. 가볍고 시원하게 입어주세요.",
            "높은 기온엔 린넨이나 얇은 코튼이 잘 어울려요.",
            "긴 외출이라면 땀 배출이 쉬운 코디가 편해요.",
            "햇빛을 생각해 가벼운 긴소매도 좋은 선택이에요.",
            "시원한 착장이 필요한 날이에요. 신발도 가볍게 골라주세요.",
            "체온이 오르기 쉬워요. 몸에 붙지 않는 핏을 추천해요.",
            "무더위엔 심플하고 통기성 좋은 옷을 추천해요.",
        ],
        "warm": [
            "따뜻한 날이에요. 가벼운 상의와 편한 하의가 잘 맞아요.",
            "기온은 높지만 실내 냉방을 생각해 얇은 겉옷도 좋아요.",
            "오늘은 가벼운 소재를 추천해요.",
            "밝은 톤과 가벼운 소재가 잘 어울리는 날이에요.",
            "활동하기 좋은 온도예요. 통풍감 있는 옷이 편해요.",
            "낮에는 따뜻해요. 얇고 여유 있는 옷을 추천해요.",
            "산뜻하게 입기 좋은 날이에요.",
        ],
        "mild": [
            "쾌적한 온도예요. 얇은 긴소매나 셔츠가 잘 맞아요.",
            "가볍지만 너무 짧지 않은 코디가 좋아요.",
            "오늘은 셔츠, 얇은 니트, 긴 팬츠 조합이 좋아요.",
            "실내외 온도 차를 생각해 가벼운 레이어드를 추천해요.",
            "선선함이 살짝 있어요. 팔을 덮는 상의가 편할 수 있어요.",
            "얇은 겉옷을 더하면 아침저녁까지 편해요.",
            "오늘은 과하게 덥지 않아 미니멀한 긴 옷이 잘 어울려요.",
        ],
        "cool": [
            "선선한 날이에요. 가벼운 자켓이나 니트를 추천해요.",
            "반팔만 입기엔 쌀쌀할 수 있어요. 긴소매가 좋아요.",
            "오늘은 가디건이나 셔츠 아우터가 든든해요.",
            "적당히 따뜻한 레이어드가 잘 맞는 날이에요.",
            "짧은 하의보다는 긴 팬츠가 더 안정적이에요.",
            "아침저녁엔 차가울 수 있어요. 겉옷을 챙겨주세요.",
            "선선한 공기에 맞춰 부드러운 니트도 좋아요.",
            "가볍게만 입으면 추울 수 있어요. 한 겹 더해보세요.",
            "오늘은 봄/가을 아우터가 자연스럽게 어울려요.",
        ],
        "cold": [
            "쌀쌀한 날이에요. 니트와 아우터를 함께 추천해요.",
            "가벼운 옷보다는 보온감 있는 레이어드가 좋아요.",
            "오늘은 코트나 두께감 있는 자켓이 잘 맞아요.",
            "목과 손목을 덮는 코디가 체감 추위를 줄여줘요.",
            "쌀쌀한 날이에요. 얇은 상의 하나는 부족할 수 있어요.",
            "보온감 있는 소재를 중심으로 입어주세요.",
            "긴 외출이라면 아우터를 꼭 챙기는 게 좋아요.",
            "오늘은 따뜻한 톤과 두께감 있는 룩이 어울려요.",
            "추위를 덜 타도 한 겹 더 입는 편이 안전해요.",
        ],
        "freezing": [
            "추운 날이에요. 보온성 높은 아우터가 필요해요.",
            "오늘은 따뜻함이 우선이에요. 두꺼운 레이어드를 추천해요.",
            "패딩이나 코트처럼 든든한 겉옷이 잘 맞아요.",
            "체감이 낮을 수 있어요. 장갑이나 머플러도 좋아요.",
            "찬 공기가 강해요. 보온 소재를 중심으로 입어주세요.",
            "외출 시간이 길다면 이너부터 따뜻하게 챙겨주세요.",
            "오늘은 스타일보다 체온 유지가 먼저예요.",
        ],
    }

    if weather_main == "Thunderstorm":

        return random.choice(thunder_messages)

    if weather_main in ["Rain", "Drizzle"]:

        return random.choice(rain_messages)

    if wind_speed >= 8:

        return random.choice(wind_messages)

    if temp_gap >= 8:

        return random.choice(gap_messages)

    effective_temp_reasons = effective_temp_reasons or {}

    if (
        day_temp is not None
        and effective_temp is not None
        and day_temp - effective_temp >= 4
    ):

        reason_count = sum(
            1
            for active in effective_temp_reasons.values()
            if active
        )

        if reason_count >= 2:

            return random.choice(effective_mixed_messages)

        if effective_temp_reasons.get("feels_like"):

            return random.choice(effective_feels_like_messages)

        if effective_temp_reasons.get("wind"):

            return random.choice(effective_wind_messages)

        if effective_temp_reasons.get("temp_gap"):

            return random.choice(effective_gap_messages)

    if uv_index is not None and uv_index >= 6:

        return random.choice(uv_messages)

    if temp >= 30:

        return random.choice(temperature_messages["hot"])

    if temp >= 25:

        return random.choice(temperature_messages["warm"])

    if temp >= 20:

        return random.choice(temperature_messages["mild"])

    if temp >= 15:

        return random.choice(temperature_messages["cool"])

    if temp >= 10:

        return random.choice(temperature_messages["cold"])

    return random.choice(temperature_messages["freezing"])


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
    uv_index = None

    lat = None
    lon = None
    has_gps_location = False

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
            has_gps_location = True

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

        uv_index = get_uv_index(
            lat,
            lon
        )

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
    rain_pops_today = []
    rain_pops_tomorrow = []

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
            forecast_pop = round((item.get("pop") or 0) * 100)

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

                        "temp": round(current_temp),

                        "is_rain": weather_type in [
                            "Rain",
                            "Drizzle",
                            "Thunderstorm"
                        ]

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

                        "temp": round(current_temp),

                        "is_rain": weather_type in [
                            "Rain",
                            "Drizzle",
                            "Thunderstorm"
                        ]

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
                    rain_pops_today.append(forecast_pop)

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
                    rain_pops_tomorrow.append(forecast_pop)

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
        rain_probability = round(
            sum(rain_pops_today) / len(rain_pops_today)
        ) if rain_pops_today else 0

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
        rain_probability = round(
            sum(rain_pops_tomorrow) / len(rain_pops_tomorrow)
        ) if rain_pops_tomorrow else 0

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

    weather_alert = None

    if (
        mode == "today"
        and has_gps_location
        and lat is not None
        and lon is not None
    ):

        weather_alert = get_weather_alert_notice(
            lat,
            lon,
            city_name
        )

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

    effective_temp_reasons = {
        "feels_like": False,
        "wind": False,
        "temp_gap": False
    }

    if feels_like is not None and feels_like < effective_temp:

        effective_temp = feels_like
        effective_temp_reasons["feels_like"] = True

    if wind_speed >= 8:

        effective_temp -= 3
        effective_temp_reasons["wind"] = True

    elif wind_speed >= 6:

        effective_temp -= 2
        effective_temp_reasons["wind"] = True

    elif wind_speed >= 4:

        effective_temp -= 1
        effective_temp_reasons["wind"] = True

    if temp_gap >= 10:

        effective_temp -= 2
        effective_temp_reasons["temp_gap"] = True

    elif temp_gap >= 6:

        effective_temp -= 1
        effective_temp_reasons["temp_gap"] = True

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
            "desc": "트렌디한 스트릿"
        },

        {
            "folder": "minimal",
            "title": "Minimal",
            "desc": "깔끔하고 미니멀한 감성룩"
        }

    ]

    if rain_mode:

        rain_recommendation = "우산 추천"

        if rain_probability < 50:

            rain_recommendation = "접이식 우산 추천"

        styles.insert(0, {

            "folder": "rain",

            "title": "Rainy day",

            "desc": f"비 예보 {rain_probability}% · {rain_recommendation}"

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

            image_candidates = [

                (
                    f"/static/styles/"
                    f"{selected_season}/"
                    f"{style['folder']}/"
                    f"{image}"
                )
                for image in image_list
            ]

            img_path = (
                f"/static/styles/"
                f"{selected_season}/"
                f"{style['folder']}/"
                f"{random_image}"
            )

        except:

            img_path = "/static/styles/default.png"
            image_candidates = [img_path]

        outfits.append({

            "title": style["title"],
            "desc": style["desc"],
            "img": img_path,
            "images": image_candidates

        })

    today_message = get_today_message(
        weather_main,
        temp,
        pm,
        wind_speed,
        temp_gap,
        day_temp,
        effective_temp,
        effective_temp_reasons,
        uv_index
    )

    return render_template(

        "index.html",

        mode=mode,

        temp=temp,
        temp_min=temp_min,
        temp_max=temp_max,
        feels_like=feels_like,
        effective_temp=effective_temp,
        humidity=humidity,
        wind_speed=wind_speed,

        pm_text=pm_text,
        weather_alert=weather_alert,
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
