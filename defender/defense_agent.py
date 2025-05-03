# defense_agent.py
import pandas as pd
import joblib
import subprocess
import time
import os
from sklearn.ensemble import RandomForestClassifier
import re
import random
from sklearn.model_selection import train_test_split

# Chemin du log Suricata
log_path = "/var/log/suricata/fast.log"

# Chemin pour sauvegarder les données collectées pour réentraîner
training_data_path = "training_data.csv"

# Colonnes de features attendues
FEATURE_COLUMNS = ["port", "frequency"]  # 'alert_type' est le label

# Chargement ou entraînement du modèle Random Forest
def load_or_train_model():
    try:
        model = joblib.load("defense_model.pkl")
        print("[+] Modèle chargé.", flush=True)
    except FileNotFoundError:
        print("[!] Modèle introuvable, entraînement d'un modèle de secours...", flush=True)
        # Jeu de données fictif pour l'exemple
        data = pd.DataFrame({
            "alert_type": [0, 1, 0, 1],
            "port": [21, 22, 80, 445],
            "frequency": [5, 10, 1, 3]
        })
        labels = data["alert_type"]
        model = RandomForestClassifier()
        model.fit(data[FEATURE_COLUMNS], labels)
        joblib.dump(model, "defense_model.pkl")
        print("[+] Modèle de secours entraîné et sauvegardé.", flush=True)
    return model

# Extraction de features depuis une ligne de log
def extract_features(log_line):
    features = {}

    if ":21" in log_line:
        features["port"] = 21
    elif ":22" in log_line:
        features["port"] = 22
    elif ":80" in log_line:
        features["port"] = 80
    elif ":445" in log_line:
        features["port"] = 445
    else:
        features["port"] = 0

    features["frequency"] = 1  # Simplification : toujours 1 pour ce prototype
    return features

# Blocage d'une IP
def block_ip(ip_address):
    if re.match(r"^(\d{1,3}\.){3}\d{1,3}$", ip_address):
        print(f"[!] Blocage de l'IP suspecte : {ip_address}")
        subprocess.run(["sudo", "iptables", "-A", "INPUT", "-s", ip_address, "-j", "DROP"])
    else:
        print(f"[!] IP invalide : {ip_address}")

# Surveillance des logs
def monitor_logs(model):
    print("[+] Surveillance des attaques en cours...", flush=True)
    seen_lines = set()
    collected_data = []

    while True:
        try:
            if not os.path.exists(log_path):
                print(f"[!] Fichier log introuvable : {log_path}", flush=True)
                time.sleep(5)
                continue

            with open(log_path, "r") as f:
                lines = f.readlines()

            for line in lines:
                if line not in seen_lines:
                    seen_lines.add(line)
                    print(f"[LOG] {line.strip()}", flush=True)
                    features = extract_features(line)

                    # Pour prédiction, assure que les colonnes sont dans le bon ordre
                    df = pd.DataFrame([[features.get(col, 0) for col in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS)

                    collected_data.append(features)

                    prediction = model.predict(df)[0]

                    if prediction == 1:
                        ip = extract_source_ip(line)
                        if ip:
                            block_ip(ip)

            if len(collected_data) >= 100:
                print("[+] Réentraîner le modèle avec les nouvelles données...", flush=True)
                new_data = pd.DataFrame(collected_data)

                # Pour cette démo, on génère un label fictif (0 = safe, 1 = attack)
                new_data["alert_type"] = [random.choice([0, 1]) for _ in range(len(new_data))]

                if os.path.exists(training_data_path):
                    old_data = pd.read_csv(training_data_path)
                    combined_data = pd.concat([old_data, new_data], ignore_index=True)
                else:
                    combined_data = new_data

                X = combined_data[FEATURE_COLUMNS]
                y = combined_data["alert_type"]
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                new_model = RandomForestClassifier()
                new_model.fit(X_train, y_train)
                joblib.dump(new_model, "defense_model.pkl")
                print("[+] Modèle réentraîné et sauvegardé.", flush=True)

                combined_data.to_csv(training_data_path, index=False)
                collected_data = []

            time.sleep(5)

        except KeyboardInterrupt:
            print("\n[+] Arrêt de la surveillance.", flush=True)
            break
        except Exception as e:
            print(f"[X] Erreur dans le monitoring : {e}", flush=True)
            time.sleep(5)

# Extraction IP depuis une ligne
def extract_source_ip(log_line):
    ip_pattern = r"(\d+\.\d+\.\d+\.\d+):\d+ ->"
    match = re.search(ip_pattern, log_line)
    return match.group(1) if match else None

# Main
def main():
    model = load_or_train_model()
    monitor_logs(model)

if __name__ == "__main__":
    main()