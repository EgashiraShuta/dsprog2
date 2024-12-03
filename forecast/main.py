import flet as ft
import requests
import json

# 地域リストを取得する関数
def load_regions():
    with open("forecast.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

# 天気予報を取得する関数
def fetch_weather(region_code):
    url = f"https://www.jma.go.jp/bosai/forecast/data/forecast/{region_code}.json"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

# メインアプリケーション
def main(page: ft.Page):
    page.title = "天気予報アプリ"
    page.scroll = "adaptive"

    data = load_regions()
    centers = data["centers"]
    offices = data["offices"]
    weather_display = ft.Column()  # 天気予報の表示用

    # 天気データを表示する関数
    def show_weather(region_code):
        weather_data = fetch_weather(region_code)
        weather_display.controls.clear()

        if weather_data:
            for forecast in weather_data:
                publishing_office = forecast.get("publishingOffice", "不明")
                report_time = forecast.get("reportDatetime", "不明")
                time_defines = forecast["timeSeries"][0].get("timeDefines", [])
                areas = forecast["timeSeries"][0].get("areas", [])

                weather_display.controls.append(
                    ft.Text(f"発表元: {publishing_office}, 発表日時: {report_time}", size=16, weight="bold")
                )

                for i, area in enumerate(areas):
                    area_name = area["area"]["name"]
                    weathers = area.get("weathers", ["不明"])
                    weather_display.controls.append(
                        ft.Text(f"{i + 1}. 地域: {area_name}")
                    )
                    for t, weather in enumerate(weathers):
                        weather_display.controls.append(
                            ft.Text(f"    時間: {time_defines[t]}, 天気: {weather}")
                        )
        else:
            weather_display.controls.append(ft.Text("天気予報データの取得に失敗しました。"))

        page.update()

    # 地方ごとに県リストを作成
    region_list = []

    def toggle_visibility(button, pref_list):
        pref_list.visible = not pref_list.visible
        button.text = "▲" if pref_list.visible else "▼"
        page.update()

    for center_code, center in centers.items():
        # 地方内の県リストを作成
        prefectures = ft.Column(controls=[
            ft.ListTile(
                title=ft.Text(offices[pref_code]["name"]),
                subtitle=ft.Text(offices[pref_code]["enName"]),
                data=pref_code,
                on_click=lambda e: show_weather(e.control.data),
            )
            for pref_code in center["children"]
        ])
        prefectures.visible = False  # 初期状態では非表示

        toggle_button = ft.TextButton(text="▼")  # ボタンを先に定義
        toggle_button.on_click = lambda e, p=prefectures, b=toggle_button: toggle_visibility(b, p)

        # 地方を表すUIを構築
        region_list.append(
            ft.Column([
                ft.Row([ft.Text(center["name"], size=18, weight="bold"), toggle_button]),
                prefectures
            ])
        )

    # UI要素をページに追加
    page.add(
        ft.Row([
            ft.ListView(controls=region_list, expand=1),  # 地方→県の階層構造
            ft.Column([ft.Text("天気予報", size=20), weather_display], expand=2),
        ])
    )

ft.app(target=main)