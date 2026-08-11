import os
import time
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

os.environ.setdefault("OPENWEATHER_API_KEY", "test-key")

import app as weather_app


class WeatherAlertTests(unittest.TestCase):

    NOW = 1_700_000_000

    def active_alert(self, event):

        return {
            "event": event,
            "description": "",
            "start": self.NOW - 60,
            "end": self.NOW + 60,
        }

    def test_all_supported_alert_types_are_mapped(self):

        events = [
            ("폭염주의보", "폭염주의보"),
            ("한파주의보", "한파주의보"),
            ("호우주의보", "호우주의보"),
            ("강풍주의보", "강풍주의보"),
            ("태풍주의보", "태풍주의보"),
            ("건조주의보", "건조주의보"),
            ("오존주의보", "오존주의보"),
            ("황사주의보", "황사주의보"),
        ]

        for event, expected in events:

            with self.subTest(event=event):

                notice = weather_app.build_weather_alert_notice(
                    [self.active_alert(event)],
                    "포천시",
                    now_ts=self.NOW,
                )

                self.assertIn(expected, notice["text"])
                self.assertEqual(notice["level"], "advisory")
    def test_explicit_korean_advisory_beats_english_description(self):

        level, label = weather_app.get_alert_level(
            "폭염주의보 heat warning details"
        )

        self.assertEqual(level, "advisory")
        self.assertEqual(label, "주의보")
    def test_warning_is_prioritized_over_advisory(self):

        notice = weather_app.build_weather_alert_notice(
            [
                self.active_alert("폭염주의보"),
                self.active_alert("호우경보"),
            ],
            "포천시",
            now_ts=self.NOW,
        )

        self.assertEqual(notice["level"], "warning")
        self.assertEqual(notice["text"], "⚠️ 포천시 호우경보 발효")

    def test_expired_and_unsupported_alerts_are_ignored(self):

        expired = self.active_alert("강풍경보")
        expired["end"] = self.NOW - 1

        notice = weather_app.build_weather_alert_notice(
            [expired, self.active_alert("Marine Notice")],
            "포천시",
            now_ts=self.NOW,
        )

        self.assertIsNone(notice)

    def test_api_failure_returns_none(self):

        with patch.object(weather_app, "fetch_json", return_value=(None, 500)):

            notice = weather_app.get_weather_alert_notice(
                37.8949,
                127.2002,
                "포천시",
            )

        self.assertIsNone(notice)

    def test_today_shows_alert_and_future_date_shows_dust(self):

        alert = {
            "text": "⚠️ 포천시 폭염주의보 발효",
            "level": "advisory",
        }

        with weather_app.app.test_request_context("/"):

            today_html = weather_app.render_safe_template(
                temp=30,
                pm_text="좋음",
                weather_alert=alert,
                selected_date="2026-08-11",
                today_date="2026-08-11",
            )
            future_html = weather_app.render_safe_template(
                temp=30,
                pm_text="좋음",
                weather_alert=alert,
                selected_date="2026-08-12",
                today_date="2026-08-11",
            )

        self.assertIn("포천시 폭염주의보 발효", today_html)
        self.assertNotIn("미세먼지 좋음", today_html)
        self.assertNotIn("포천시 폭염주의보 발효", future_html)
        self.assertIn("미세먼지 좋음", future_html)


    def test_gps_today_route_replaces_dust_with_alert(self):

        current_weather = {
            "name": "Pocheon",
            "coord": {"lat": 37.8949, "lon": 127.2002},
            "main": {
                "temp": 31,
                "feels_like": 33,
                "temp_min": 28,
                "temp_max": 34,
                "humidity": 62,
            },
            "weather": [{"main": "Clear", "icon": "01d"}],
            "wind": {"speed": 2.5},
        }

        def fake_fetch(url):

            if "/geo/1.0/reverse" in url:

                return ([{
                    "name": "Pocheon",
                    "local_names": {"ko": "포천시"},
                }], 200)

            if "/data/2.5/weather" in url:

                return current_weather, 200

            if "/data/2.5/forecast" in url:

                return {"list": []}, 200

            if "/data/2.5/air_pollution" in url:

                return {"list": [{"components": {"pm2_5": 18}}]}, 200

            if "/data/3.0/onecall" in url and "exclude=current" in url:

                return ({
                    "alerts": [{
                        "event": "폭염경보",
                        "description": "",
                        "start": int(time.time()) - 60,
                        "end": int(time.time()) + 3600,
                    }]
                }, 200)

            if "/data/3.0/onecall" in url:

                return {"current": {"uvi": 7}}, 200

            raise AssertionError(url)

        today = (
            datetime.utcnow() + timedelta(hours=9)
        ).strftime("%Y-%m-%d")

        with patch.object(
            weather_app,
            "fetch_json",
            side_effect=fake_fetch,
        ):

            response = weather_app.app.test_client().get(
                f"/?lat=37.8949&lon=127.2002&date={today}"
            )

        body = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("포천시 폭염경보 발효", body)
        self.assertNotIn("미세먼지 좋음", body)

if __name__ == "__main__":
    unittest.main()