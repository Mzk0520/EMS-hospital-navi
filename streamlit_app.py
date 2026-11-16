import streamlit as st
import pandas as pd

# 画面の基本設定（スマホでも見やすいレイアウト）
st.set_page_config(page_title="救急AI病院ナビ", page_icon="🚑", layout="centered")

st.title("🚑 救急AI 病院ランキング・ナビ")
st.caption("現場の状況を入力すると、AIが過去の受入データから「今受け入れられやすい病院」を瞬時に予測します。")

st.divider()

# 1. 入力（救急隊がやること）
st.subheader("1. 現在の現場状況を選択")

col1, col2 = st.columns(2)
with col1:
    symptom = st.selectbox("主な症状・診療科", ["内科系（発熱・腹痛など）", "外科・外傷（骨折・出血など）", "循環器・脳神経（胸痛・麻痺など）", "小児科"])
    weather = st.radio("現在の天気", ["晴れ・曇り", "雨・雪（悪天候）"], horizontal=True)

with col2:
    event = st.checkbox("周辺でお祭り・大型イベント開催中")
    night_holiday = st.checkbox("夜間・休日時間帯")

st.divider()

# 2. 計算（AIの予測ロジック：まずはルールベースのデモモデル）
# ※今後ここに実際の過去データを学習させた機械学習モデルを組み込みます
hospitals = [
    {"病院名": "中央総合医療センター", "距離": "1.2 km", "基本受入率": 85, "得意": "循環器・脳神経（胸痛・麻痺など）", "規模": "大"},
    {"病院名": "さくら市民病院", "距離": "2.5 km", "基本受入率": 80, "得意": "内科系（発熱・腹痛など）", "規模": "中"},
    {"病院名": "みなと救急クリニック", "距離": "0.8 km", "基本受入率": 75, "得意": "外科・外傷（骨折・出血など）", "規模": "小"},
    {"病院名": "あおば大学病院", "距離": "4.1 km", "基本受入率": 90, "得意": "すべて", "規模": "大"},
    {"病院名": "みどりこども・総合病院", "距離": "3.0 km", "基本受入率": 82, "得意": "小児科", "規模": "中"},
]

results = []
for h in hospitals:
    prob = h["基本受入率"]
    
    # 症状と病院の得意分野が一致すれば確率アップ
    if h["得意"] == symptom or h["得意"] == "すべて":
        prob += 8
    else:
        prob -= 10
        
    # イベント時は中小病院が混雑しやすいと仮定
    if event and h["規模"] != "大":
        prob -= 15
        
    # 悪天候時は全体的に受入率が少し下がると仮定
    if weather == "雨・雪（悪天候）":
        prob -= 5
        
    # 夜間・休日は大規模病院以外が受け入れにくくなると仮定
    if night_holiday and h["規模"] == "小":
        prob -= 20

    # 確率を10%〜99%の範囲に収める
    prob = max(10, min(99, prob))
    
    results.append({
        "病院名": h["病院名"],
        "AI予測 受入確率": prob,
        "現場からの距離": h["距離"],
        "主な対応": h["得意"]
    })

# 確率が高い順に並べ替え
df = pd.DataFrame(results).sort_values(by="AI予測 受入確率", ascending=False).reset_index(drop=True)
df.index = df.index + 1  # 順位を1位からにする

# 3. 表示（画面に出ること）
st.subheader("2. おすすめ受入病院ランキング")

# 1位の病院を特に目立つように表示
top_hospital = df.iloc[0]
st.success(f"🥇 **第1候補：{top_hospital['病院名']}**（予測受入確率：**{top_hospital['AI予測 受入確率']}%** / 距離：{top_hospital['現場からの距離']}）")

# 全体のランキング表を表示（プログレスバー付き）
st.dataframe(
    df,
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