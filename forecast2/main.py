import flet as ft
import requests
import json
import sqlite3
from datetime import datetime

# DB初期化関数
def initialize_db():
    conn = sqlite3.connect("weather.db")
    cursor = conn.cursor()

    # 地域情報テーブル
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS regions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        region_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        en_name TEXT
    )
    """)

    # 天気予報テーブル
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weather_forecast (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        region_code TEXT,
        report_datetime TEXT,
        area_name TEXT,
        forecast_time TEXT,
        weather TEXT,
        FOREIGN KEY(region_code) REFERENCES regions(region_code)
    )
    """)

    conn.commit()
    conn.close()

# 天気情報をDBに保存する関数
def save_weather_to_db(region_code, weather_data):
    conn = sqlite3.connect("weather.db")
    cursor = conn.cursor()

    # 発表元と日時
    report_time = weather_data[0].get("reportDatetime", "不明")
    areas = weather_data[0]["timeSeries"][0].get("areas", [])
    time_defines = weather_data[0]["timeSeries"][0].get("timeDefines", [])

    # 天気情報をDBに挿入
    for area in areas:
        area_name = area["area"]["name"]
        weathers = area.get("weathers", ["不明"])

        for i, forecast_time in enumerate(time_defines):
            cursor.execute("""
            INSERT INTO weather_forecast (region_code, report_datetime, area_name, forecast_time, weather)
            VALUES (?, ?, ?, ?, ?)
            """, (region_code, report_time, area_name, forecast_time, weathers[i]))

    conn.commit()
    conn.close()

# 天気予報を取得する関数
def fetch_weather(region_code):
    url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{region_code}.json"
    response = requests.get(url)
    if response.status_code == 200:
        weather_data = response.json()
        save_weather_to_db(region_code, weather_data)
        return weather_data
    else:
        print(f"Error fetching weather: {response.status_code}")
        return None

# 地域データをDBに保存する関数
def save_regions_to_db(data):
    conn = sqlite3.connect("weather.db")
    cursor = conn.cursor()

    for center_code, center in data["centers"].items():
        for region_code in center["children"]:
            office = data["offices"].get(region_code, {})
            cursor.execute("""
            INSERT OR IGNORE INTO regions (region_code, name, en_name)
            VALUES (?, ?, ?)
            """, (region_code, office.get("name", ""), office.get("enName", "")))

    conn.commit()
    conn.close()

# 地域データをロード
def load_regions():
    with open("forecast.json", "r", encoding="utf-8") as f:
        return json.load(f)

# DBから天気情報を取得する関数
def get_weather_from_db(region_code):
    conn = sqlite3.connect("weather.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT area_name, report_datetime, forecast_time, weather
    FROM weather_forecast
    WHERE region_code = ?
    """, (region_code,))
    rows = cursor.fetchall()
    conn.close()

    return rows

# メインアプリケーション
def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.scroll = "adaptive"

    initialize_db()
    data = load_regions()
    save_regions_to_db(data)

    weather_display = ft.Column()

    def show_weather(region_code):
        weather_display.controls.clear()

        # 天気データがDBにない場合APIから取得
        if not get_weather_from_db(region_code):
            fetch_weather(region_code)

        # DBから天気データを表示
        rows = get_weather_from_db(region_code)
        if rows:
            for area_name, report_datetime, forecast_time, weather in rows:
                weather_display.controls.append(
                    ft.Text(f"{area_name} | {forecast_time} | {weather}")
                )
        else:
            weather_display.controls.append(ft.Text("データがありません。"))

        page.update()

    # UIの構築
    region_list = []
    for center_code, center in data["centers"].items():
        prefectures = ft.Column(controls=[
            ft.ListTile(
                title=ft.Text(data["offices"][pref_code]["name"]),
                on_click=lambda e, r=pref_code: show_weather(r)
            )
            for pref_code in center["children"]
        ])
        region_list.append(
            ft.Column([ft.Text(center["name"], size=18, weight="bold"), prefectures])
        )

    page.add(
        ft.Row([
            ft.ListView(controls=region_list, expand=1),
            ft.Column([ft.Text("天気予報", size=20), weather_display], expand=2),
        ])
    )

ft.app(target=main)
