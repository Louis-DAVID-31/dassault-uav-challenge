from pymavlink import mavutil
import time

# 1. Connexion au contrôleur de vol
# (Remplacez '/dev/serial0' par le port qui a fonctionné lors de votre test !)
PORT = '/dev/ttyAMA0'
BAUD = 115200

print(f"Connexion à ArduPilot sur {PORT}...")
master = mavutil.mavlink_connection(PORT, baud=BAUD)

# 2. Attente du Heartbeat pour s'assurer que la carte est prête
print("En attente du Heartbeat...")
master.wait_heartbeat()
print("Connexion établie avec le drone !")

# 3. Fonction pour changer de mode
def change_flight_mode(mode_name):
    # Vérifie si le mode demandé existe dans ArduPilot
    if mode_name not in master.mode_mapping():
        print(f"Erreur : Le mode {mode_name} n'existe pas.")
        return False

    # Récupère l'ID interne du mode (ex: GUIDED = 15 pour ArduPlane)
    mode_id = master.mode_mapping()[mode_name]
    
    print(f"Envoi de l'ordre : Passage en mode {mode_name}...")
    
    # Envoi de la commande MAVLink pour forcer le mode
    master.set_mode(mode_id)

    # 4. Boucle de vérification
    # On écoute les prochains Heartbeats pour voir si le changement a été accepté
    while True:
        # On attend un nouveau message Heartbeat (bloquant, max 1 seconde)
        msg = master.recv_match(type='HEARTBEAT', blocking=True, timeout=1.0)
        if msg:
            # master.flightmode est mis à jour automatiquement par pymavlink
            current_mode = master.flightmode
            print(f"Mode actuel de l'avion : {current_mode}")
            
            if current_mode == mode_name:
                print(f"Succès ! L'avion est maintenant en mode {mode_name}.")
                return True
            else:
                print("En attente de la confirmation du changement...")
                # On renvoie la commande au cas où le paquet ait été perdu
                master.set_mode(mode_id)
                time.sleep(0.5)

# --- Exécution du scénario ---

# On peut demander le mode GUIDED (ou RTL, MANUAL, AUTO...)
change_flight_mode('GUIDED')

# La suite de votre programme (envoi de coordonnées, etc.) viendra ici !
print("Le Raspberry Pi a maintenant le contrôle de la navigation.")
