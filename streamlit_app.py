import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
from sklearn.ensemble import RandomForestClassifier

# 画面の基本設定
st.set_page_config(page_title="救急AI病院ナビ", page_icon="🚑", layout="centered")

# 日本時間の現在時刻を自動取得
JST = timezone(timedelta(hours=+9), 'JST')
now = datetime.now(JST)
is_weekend = now.weekday() >= 5
is_night = now.hour < 8 or now.hour >= 18
auto_off_hours = is_weekend or is_night

# AIモデルの学習（起動時に過去データCSVを読み込んで自動学習）
@st.cache_resource
def train_ai_model():
    df_past = pd.read_csv("past_records.csv")
    # 文字データをAIが計算できる数値（ダミー変数）に変換
    X = pd.get_dummies(df_past[["hospital", "severity", "symptom", "weather", "event", "night_holiday"]])
    y = df_past["accepted"]
    
    # ランダムフォレスト（決定木AI）で学習
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model, X.columns

model, model_columns = train_ai_model()

st.title("🚑 救急AI 病院ランキング・ナビ")
st.caption(f"現在時刻：{now.strftime('%Y/%m/%d %H:%M')}（{'夜間・休日体制' if auto_off_hours else '平日日中体制'}を自動検知）")
st.info("🧠 過去の搬送・受入実績データ（past_records.csv）を学習したAIモデルが稼働中です")

st.divider()

# 1. 入力（救急隊が現場でポチッと選ぶ）
st.subheader("1. 現場状況のクイック入力")

severity_label = st.radio(
    "患者の重症度・緊急度",
    ["🟢 軽症（一次）", "🟡 中等症（二次）", "🔴 重症・生命危機（三次）"],
    horizontal=True
)
# AI学習データと表記を合わせる
severity_map = {"🟢 軽症（一次）": "軽症", "🟡 中等症（二次）": "中等症", "🔴 重症・生命危機（三次）": "重症"}
severity = severity_map[severity_label]

col1, col2 = st.columns(2)
with col1:
    symptom_label = st.selectbox(
        "主な症状・診療科",
        ["内科系（発熱・腹痛など）", "外科・外傷（骨折・出血など）", "循環器・脳神経（胸痛・麻痺など）", "小児科"]
    )
    symptom = symptom_label.split("（")[0]  # 「内科系」などの部分だけ抽出
    
    weather_label = st.radio("現在の天気", ["☀️ 晴れ・曇り", "☔ 雨・雪（悪天候）"], horizontal=True)
    weather = "晴れ" if "晴れ" in weather_label else "雨"

with col2:
    event = 1 if st.checkbox("🎪 周辺でお祭り・大型イベント開催中") else 0
    night_holiday = 1 if st.checkbox("🌙 夜間・休日扱いとして計算", value=auto_off_hours) else 0

st.divider()

# 2. 計算（学習済みAIによる受入確率の推論）
hospitals = [
    {"病院名": "中央総合医療センター", "距離": "1.2 km", "得意": "循環器・脳神経", "三次対応": "対応可", "電話番号": "03-0000-0001", "検索キーワード": "東京都立広尾病院"},
    {"病院名": "さくら市民病院", "距離": "2.5 km", "得意": "内科系", "三次対応": "二次まで", "電話番号": "03-0000-0002", "検索キーワード": "東京医療センター"},
    {"病院名": "みなと救急クリニック", "距離": "0.8 km", "得意": "外科・外傷", "三次対応": "二次まで", "電話番号": "03-0000-0003", "検索キーワード": "三軒茶屋病院"},
    {"病院名": "あおば大学病院", "距離": "4.1 km", "得意": "全科・三次救急", "三次対応": "対応可", "電話番号": "03-0000-0004", "検索キーワード": "昭和大学病院"},
    {"病院名": "みどりこども・総合病院", "距離": "3.0 km", "得意": "小児科", "三次対応": "二次まで", "電話番号": "03-0000-0005", "検索キーワード": "国立成育医療研究センター"},
]

results = []
for h in hospitals:
    # 現在の現場状況を1行のデータにする
    input_df = pd.DataFrame([{
        "hospital": h["病院名"],
        "severity": severity,
        "symptom": symptom,
        "weather": weather,
        "event": event,
        "night_holiday": night_holiday
    }])
    
    # 学習時と同じ形式に変換（足りない列は0で埋める）
    input_encoded = pd.get_dummies(input_df).reindex(columns=model_columns, fill_value=0)
    
    # AIが「accepted = 1（受入成功）」になる確率を計算
    prob = int(round(model.predict_proba(input_encoded)[0][1] * 100))
    
    results.append({
        "病院名": h["病院名"],
        "AI予測 受入確率": prob,
        "現場からの距離": h["距離"],
        "主な対応": h["得意"],
        "三次救急": h["三次対応"],
        "電話番号": h["電話番号"],
        "マップURL": f"https://www.google.com/maps/search/?api=1&query={h['検索キーワード']}"
    })

# 確率が高い順に並べ替え
df = pd.DataFrame(results).sort_values(by="AI予測 受入確率", ascending=False).reset_index(drop=True)
df.index = df.index + 1

# 3. 表示（画面に出ること）
st.subheader("2. AI予測 おすすめ受入病院ランキング（TOP 3）")

medals = ["🥇 第1候補", "🥈 第2候補", "🥉 第3候補"]
for i in range(3):
    row = df.iloc[i]
    with st.container(border=True):
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown(f"#### {medals[i]}：{row['病院名']}")
            st.caption(f"距離：{row['現場からの距離']} ｜ {row['三次救急']} ｜ 得意：{row['主な対応']}")
        with c2:
            st.metric(label="AI受入予測確率", value=f"{row['AI予測 受入確率']}%")
        
        btn1, btn2 = st.columns(2)
        with btn1:
            st.link_button(f"📞 受入要請 ({row['電話番号']})", f"tel:{row['電話番号']}", use_container_width=True)
        with btn2:
            st.link_button("🗺️ 搬送ルートを開く", row["マップURL"], use_container_width=True)

st.divider()

with st.expander("📊 AIが学習した過去の受入データ（past_records.csv）を見る"):
    st.dataframe(pd.read_csv("past_records.csv"), use_container_width=True)