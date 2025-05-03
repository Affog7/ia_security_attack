import streamlit as st
import pandas as pd
import json
import matplotlib.pyplot as plt
import seaborn as sns

# Chargement des fichiers
@st.cache_data
def load_rewards():
    with open("rewards.json") as f:
        return pd.DataFrame(json.load(f))

@st.cache_data
def load_logs():
    with open("log_actions.json") as f:
        return pd.DataFrame(json.load(f))

# Interface
st.title("📊 Visualisation de l'apprentissage par renforcement")
st.markdown("Analyse des résultats issus du fichier `attack_agent.py`.")

# Charger les données
rewards_df = load_rewards()
logs_df = load_logs()

# Affichage des récompenses
st.subheader("📈 Récompense par épisode")
fig1, ax1 = plt.subplots()
sns.lineplot(data=rewards_df, x="episode", y="reward", marker="o", ax=ax1)
ax1.set_ylabel("Récompense")
ax1.set_xlabel("Épisode")
st.pyplot(fig1)

# Évolution d'epsilon
st.subheader("📉 Évolution de l'exploration (epsilon)")
fig2, ax2 = plt.subplots()
sns.lineplot(data=rewards_df, x="episode", y="epsilon", marker="o", color="orange", ax=ax2)
ax2.set_ylabel("Epsilon")
ax2.set_xlabel("Épisode")
st.pyplot(fig2)

# Détails des actions
st.subheader("📋 Détail des actions (par épisode)")
episode_choice = st.slider("Sélectionner un épisode :", 1, rewards_df["episode"].max(), 1)
episode_data = logs_df[logs_df["episode"] == episode_choice]

st.dataframe(episode_data[["step", "action", "reward", "success", "strategy", "epsilon"]])

# Fréquence des actions
st.subheader("🔍 Fréquence des actions (toutes les étapes)")
fig3, ax3 = plt.subplots()
sns.countplot(data=logs_df, y="action", order=logs_df["action"].value_counts().index, ax=ax3)
ax3.set_xlabel("Nombre d'occurrences")
st.pyplot(fig3)

# Taux de réussite par action
st.subheader("✅ Taux de succès par action")
success_rate = logs_df.groupby("action")["success"].mean().reset_index()
success_rate["success (%)"] = (success_rate["success"] * 100).round(2)

fig4, ax4 = plt.subplots()
sns.barplot(data=success_rate, x="success (%)", y="action", ax=ax4)
st.pyplot(fig4)