# cyberwar_dashboard.py

import streamlit as st
import pandas as pd
import os
import time
import datetime

st.set_page_config(page_title="CyberWar AI Dashboard", layout="wide")

st.title("🛡️ CyberWar AI - Monitoring Dashboard")

log_path = "/var/log/suricata/fast.log"
q_table_path = "q_table.json"

# Section 1 : Logs Suricata
def display_suricata_logs():
    st.subheader("📄 Logs Suricata (Défenseur)")
    if os.path.exists(log_path):
        with open(log_path, "r") as file:
            lines = file.readlines()[-20:]  # Dernières lignes
        st.text("".join(lines))
    else:
        st.warning("Fichier de log introuvable.")



# Section 3 : IP bloquées
@st.cache_data(ttl=60)
def get_blocked_ips():
    result = os.popen("sudo iptables -L INPUT -n --line-numbers").read()
    lines = [line for line in result.split("\n") if "DROP" in line]
    return lines

def display_blocked_ips():
    st.subheader("🚫 IPs bloquées")
    blocked = get_blocked_ips()
    if blocked:
        st.code("\n".join(blocked))
    else:
        st.success("Aucune IP bloquée pour le moment.")

# Affichage dynamique
with st.expander("🔁 Actualisation automatique (chaque 10 sec)"):
    if st.button("Lancer le live refresh"):
        for _ in range(30):  # 5 minutes de surveillance
            with st.spinner("Mise à jour en cours..."):
                display_suricata_logs()
                
                display_blocked_ips()
                time.sleep(10)
                st.rerun()

# Affichage manuel
st.divider()
display_suricata_logs()
 
display_blocked_ips()