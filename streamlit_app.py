import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta

# 画面の基本設定
st.set_page_config(page_title="救急AI病院ナビ", page_icon="🚑", layout="centered")

# 日本時間の現在時刻を自動取得
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST)
is_weekend = now.weekday() >= 5  # 5:土曜, 6:日曜
is_night = now.hour < 8 or now.hour >= 18
auto_off_hours = is_weekend or is_night

st.title("🚑 救急AI 病院ランキング・ナビ")
st.caption(f"現在時刻：{now.strftime('%Y/%m/%d %H:%M')}（{'夜間・休日体制' if auto_off_hours else '平日日中体制'}を自動検知）")

st.divider()

# 1. 入力（救急隊が現場でポチッと選ぶ）
st.subheader("1. 現場状況のクイック入力")

# 重症度を一番押しやすい横並びラジオボタンで配置
severity = st.radio(
    "患者の重症度・緊急度",
    ["🟢 軽症（一次）", "🟡 中等症（二次）", "🔴 重症・生命危機（三次）"],
    horizontal=True
)

col1, col2 = st.columns(2)
with col1:
    symptom = st.selectbox(
        "主な症状・診療科",
        ["内科系（発熱・腹痛など）", "外科・外傷（骨折・出血など）", "循環器・脳神経（胸痛・麻痺など）", "小児科"]
    )
    weather = st.radio("現在の天気", ["☀️ 晴れ・曇り", "☔ 雨・雪（悪天候）"], horizontal=True)

with col2:
    event = st.checkbox("🎪 周辺でお祭り・大型イベント開催中")
    # 自動判定結果を初期値にしつつ、テスト用に手動変更も可能に
    night_holiday = st.checkbox("🌙 夜間・休日扱いとして計算", value=auto_off_hours)

st.divider()

# 2. 計算（AIの予測ロジック：フェーズ3でここを本物の機械学習モデルに差し替えます）
hospitals = [
    {
        "病院名": "中央総合医療センター",
        "距離": "1.2 km",
        "基本受入率": 85,
        "得意": "循環器・脳神経（胸痛・麻痺など）",
        "規模": "大",
        "三次対応": True,
        "電話番号": "03-0000-0001",
        "検索キーワード": "東京都立広尾病院"  # マップ検索用の仮名称
    },
    {
        "病院名": "さくら市民病院",
        "距離": "2.5 km",
        "基本受入率": 80,
        "得意": "内科系（発熱・腹痛など）",
        "規模": "中",
        "三次対応": False,
        "電話番号": "03-0000-0002",
        "検索キーワード": "東京医療センター"
    },
    {
        "病院名": "みなと救急クリニック",
        "距離": "0.8 km",
        "基本受入率": 75,
        "得意": "外科・外傷（骨折・出血など）",
        "規模": "小",
        "三次対応": False,
        "電話番号": "03-0000-0003",
        "検索キーワード": "三軒茶屋病院"
    },
    {
        "病院名": "あおば大学病院",
        "距離": "4.1 km",
        "基本受入率": 90,
        "得意": "すべて",
        "規模": "大",
        "三次対応": True,
        "電話番号": "03-0000-0004",
        "検索キーワード": "昭和大学病院"
    },
    {
        "病院名": "みどりこども・総合病院",
        "距離": "3.0 km",
        "基本受入率": 82,
        "得意": "小児科",
        "規模": "中",
        "三次対応": False,
        "電話番号": "03-0000-0005",
        "検索キーワード": "国立成育医療研究センター"
    },
]

results = []
for h in hospitals:
    prob = h["基本受入率"]
    
    # ① 重症度によるマッチング
    if "重症" in severity:
        if h["三次対応"]:
            prob += 10
        else:
            prob -= 55  # 三次非対応の病院は受け入れ困難と判定
    elif "軽症" in severity and h["規模"] == "大":
        prob -= 10  # 大病院は軽症だと断られやすい（二次・一次優先）

    # ② 症状と病院の得意分野が一致すれば確率アップ
    if h["得意"] == symptom or h["得意"] == "すべて":
        prob += 8
    else:
        prob -= 10
        
    # ③ イベント時は中小病院が混雑しやすいと仮定
    if event and h["規模"] != "大":
        prob -= 15
        
    # ④ 悪天候時は全体的に受入率が少し下がると仮定
    if "雨・雪" in weather:
        prob -= 5
        
    # ⑤ 夜間・休日は小規模病院の受入率が大きく下がる
    if night_holiday and h["規模"] == "小":
        prob -= 25

    # 確率を5%〜99%の範囲に収める
    prob = max(5, min(99, prob))
    
    results.append({
        "病院名": h["病院名"],
        "AI予測 受入確率": prob,
        "現場からの距離": h["距離"],
        "主な対応": h["得意"],
        "三次救急": "対応可" if h["三次対応"] else "二次まで",
        "電話番号": h["電話番号"],
        "マップURL": f"https://www.google.com/maps/search/?api=1&query={h['検索キーワード']}"
    })

# 確率が高い順に並べ替え
df = pd.DataFrame(results).sort_values(by="AI予測 受入確率", ascending=False).reset_index(drop=True)
df.index = df.index + 1

# 3. 表示（画面に出ること）
st.subheader("2. おすすめ受入病院ランキング（TOP 3）")

# 上位3病院をスマホで押しやすいカード形式で表示
medals = ["🥇 第1候補", "🥈 第2候補", "🥉 第3候補"]
for i in range(3):
    row = df.iloc[i]
    with st.container(border=True):
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f"#### {medals[i]}：{row['病院名']}")
            st.caption(f"距離：{row['現場からの距離']} ｜ {row['三次救急']} ｜ 得意：{row['主な対応']}")
        with c2:
            st.metric(label="受入予測確率", value=f"{row['AI予測 受入確率']}%")
        
        # ワンタップ連携ボタン（電話＆Googleマップ）
        btn1, btn2 = st.columns(2)
        with btn1:
            st.link_button(f"📞 受入要請 ({row['電話番号']})", f"tel:{row['電話番号']}", use_container_width=True)
        with btn2:
            st.link_button("🗺️ 搬送ルートを開く", row["マップURL"], use_container_width=True)

st.divider()

# 全病院の一覧表も下部に表示
with st.expander("📊 周辺すべての病院データ一覧を見る"):
    st.dataframe(
        df[["病院名", "AI予測 受入確率", "現場からの距離", "三次救急", "主な対応"]],
        column_config={
            "AI予測 受入確率": st.column_config.ProgressColumn(
                "AI予測 受入確率 (%)",
                format="%d%%",
                min_value=0,
                max_value=100,
            ),
        },
        use_container_width=True
    )