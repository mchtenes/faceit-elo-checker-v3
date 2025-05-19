import streamlit as st
import requests
import json
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

# ---------------- FACEIT ELO SIRALAYICI ----------------
API_KEY = "acd076a8-b019-4744-b9af-247a8b62014b"
PLAYER_NICKNAMES = ["MeLLon_", "Malkoc02", "nyousz", "PaLaCs2", "0reily", "ctVandaL", "IRubisco", "KhalEgo"]

headers = {
    "Authorization": f"Bearer {API_KEY}"
}

def get_player_elo(nickname):
    url = f"https://open.faceit.com/data/v4/players?nickname={nickname}"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return None
    data = response.json()
    try:
        games_data = data["games"]
        if "cs2" in games_data:
            return games_data["cs2"]["faceit_elo"]
        elif "csgo" in games_data:
            return games_data["csgo"]["faceit_elo"]
    except KeyError:
        return None
    return None

# ---------------- STREAMLIT ARAYÜZ ----------------
st.title("🎮 Faceit Arayüz Paneli")

# --- ELO Butonu ---
if st.button("ELO'ları Getir"):
    elo_list = []
    for nickname in PLAYER_NICKNAMES:
        elo = get_player_elo(nickname)
        elo_list.append({
            "Oyuncu": nickname,
            "ELO": elo if elo is not None else "Bilinmiyor"
        })

    elo_list = sorted(elo_list, key=lambda x: (x["ELO"] if isinstance(x["ELO"], int) else -1), reverse=True)
    st.subheader("ELO Sıralaması")
    st.table(elo_list)

# --- Görselleştirme Butonu ---
if st.button("Veri Görselleştirici"):
    json_path = "faceit_all_players_last30.json"
    if not os.path.exists(json_path):
        st.error(f"{json_path} dosyası bulunamadı. Lütfen proje klasörüne ekleyin.")
    else:
        with open(json_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        records = []
        for player, matches in raw_data.items():
            for match in matches:
                stats = match["Stats"]
                stats["Player"] = player
                stats["MatchID"] = match["MatchID"]
                records.append(stats)

        df = pd.DataFrame(records)

        numeric_cols = [col for col in df.columns if col not in ["Player", "MatchID"]]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        players = st.multiselect("Oyuncu Seç:", options=df["Player"].unique(), default=list(df["Player"].unique()))
        metrics = st.multiselect("Metriği Seç:", options=numeric_cols, default=["K/D Ratio", "ADR"])

        if players and metrics:
            filtered_df = df[df["Player"].isin(players)]
            avg_df = filtered_df.groupby("Player")[metrics].mean().round(2)

            st.subheader("Ortalama Heatmap (3x3 Grid Yapısı, Sıralı)")
            num_metrics = len(metrics)
            cols = 3
            rows = (num_metrics + cols - 1) // cols

            fig, axes = plt.subplots(rows, cols, figsize=(cols * 5, rows * 3))
            axes = axes.flatten() if num_metrics > 1 else [axes]

            for idx, metric in enumerate(metrics):
                sorted_metric_df = avg_df[[metric]].sort_values(by=metric, ascending=False)
                sns.heatmap(
                    sorted_metric_df,
                    annot=True,
                    cmap="coolwarm",
                    fmt=".2f",
                    linewidths=0.5,
                    cbar=True,
                    ax=axes[idx]
                )
                axes[idx].set_title(metric)
                axes[idx].set_ylabel("Player")

            for j in range(len(metrics), len(axes)):
                fig.delaxes(axes[j])

            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.warning("Lütfen en az bir oyuncu ve metrik seçiniz.")
