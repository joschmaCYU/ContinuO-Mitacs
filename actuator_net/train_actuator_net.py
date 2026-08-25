import os
import glob
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import math

# ==========================================
# 1. PARAMÈTRES ET MAPPING MATÉRIEL
# ==========================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FOLDER = os.path.join(SCRIPT_DIR, "data")
HISTORY_STEPS = 6
BATCH_SIZE = 128
EPOCHS = 50
LEARNING_RATE = 0.0005
TEST_SPLIT = 0.2

# Mapping basé sur ton tableau (Screenshot_20260818_175529.png)
MOTOR_MAPPING = {
    1: "RMD_X8_PRO_V2_1to9",
    2: "RMD_X8_PRO_V2_1to9",
    10: "RMD_X8_PRO_V2_1to9",
    11: "RMD_X8_PRO_V2_1to9",
    12: "RMD_X8_PRO_V2_1to9",
    13: "RMD_X8_PRO_V2_1to9",
    3: "RMD_X8_PRO_H_V3_1to6",
    4: "RMD_X8_PRO_H_V3_1to6",
    5: "RMD_X8_PRO_H_V3_1to6",
    6: "RMD_X8_PRO_H_V3_1to6",
    14: "RMD_X8_PRO_H_V3_1to6",
    15: "RMD_X8_PRO_H_V3_1to6",
    16: "RMD_X8_PRO_H_V3_1to6",
    17: "RMD_X8_PRO_H_V3_1to6",
}


# ==========================================
# 2. ARCHITECTURE DU RÉSEAU ET WRAPPER ISAAC
# ==========================================
class ActuatorNet(nn.Module):
    def __init__(self, input_size):
        super(ActuatorNet, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, 128),
            nn.GELU(),
            nn.Linear(128, 128),
            nn.GELU(),
            nn.Linear(128, 128),
            nn.GELU(),
            nn.Linear(128, 1),
        )

    def forward(self, x):
        return self.net(x)


class IsaacWrappedNet(nn.Module):
    def __init__(self, core_model, scaler_X, scaler_Y):
        super().__init__()
        self.core = core_model
        self.register_buffer("mean_X", torch.FloatTensor(scaler_X.mean_))
        self.register_buffer("scale_X", torch.FloatTensor(scaler_X.scale_))
        self.register_buffer("mean_Y", torch.FloatTensor(scaler_Y.mean_))
        self.register_buffer("scale_Y", torch.FloatTensor(scaler_Y.scale_))

    def forward(self, x):
        x_scaled = (x - self.mean_X) / self.scale_X
        y_scaled = self.core(x_scaled)
        y_real = (y_scaled * self.scale_Y) + self.mean_Y
        return y_real


# ==========================================
# 3. LECTURE ET REGROUPEMENT DES DONNÉES
# ==========================================
def load_and_group_data():
    csv_files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"Aucun fichier CSV trouvé dans {DATA_FOLDER}")

    print(f"📁 Chargement de {len(csv_files)} fichiers CSV (Air + Sol mélangés)...")

    all_dataframes = []
    for file in csv_files:
        df = pd.read_csv(file)
        all_dataframes.append(df)

    master_df = pd.concat(all_dataframes, ignore_index=True)

    # Ajout de la colonne 'motor_type' selon le dictionnaire
    master_df["motor_type"] = master_df["motor_id"].map(MOTOR_MAPPING)

    # Vérification des IDs inconnus
    inconnus = master_df[master_df["motor_type"].isna()]["motor_id"].unique()
    if len(inconnus) > 0:
        print(f"⚠️ ATTENTION : IDs non reconnus trouvés dans le CSV : {inconnus}")
        master_df = master_df.dropna(subset=["motor_type"])

    # Dictionnaire pour stocker les données traitées par type de moteur
    processed_data_by_type = {}

    # Traitement chronologique par ID, regroupé ensuite par type
    for motor_type, type_df in master_df.groupby("motor_type"):
        all_X_type = []
        all_Y_type = []

        for motor_id, motor_df in type_df.groupby("motor_id"):
            # Il est crucial de trier chronologiquement chaque session de test séparément
            # Pour simplifier, on suppose que le timestamp reprend à zéro à chaque test,
            # on utilise donc l'index original préservé avant le groupby global si possible,
            # ou on trie par fichier source. Ici on trie par timestamp.
            motor_df = motor_df.sort_values("timestamp").reset_index(drop=True)

            motor_df["pos_error"] = motor_df["target_pos"] - motor_df["actual_pos"]

            feature_cols = []
            for i in range(HISTORY_STEPS):
                motor_df[f"pos_error_t-{i}"] = motor_df["pos_error"].shift(i)
                motor_df[f"vel_t-{i}"] = motor_df["actual_vel"].shift(i)
                motor_df[f"actual_pos_t-{i}"] = motor_df["actual_pos"].shift(i)
                feature_cols.extend(
                    [f"pos_error_t-{i}", f"vel_t-{i}", f"actual_pos_t-{i}"]
                )

            motor_df = motor_df.dropna()

            X_motor = motor_df[feature_cols].values
            Y_motor = motor_df["actual_current"].values.reshape(-1, 1)

            all_X_type.append(X_motor)
            all_Y_type.append(Y_motor)

        if all_X_type:
            processed_data_by_type[motor_type] = (
                np.vstack(all_X_type),
                np.vstack(all_Y_type),
            )

    return processed_data_by_type, feature_cols


# ==========================================
# 4. BOUCLE D'ENTRAÎNEMENT PRINCIPALE
# ==========================================
def main():
    data_by_type, feature_cols = load_and_group_data()

    for motor_type, (X, Y) in data_by_type.items():
        print("\n" + "=" * 50)
        print(f"🚀 ENTRAÎNEMENT DU MODÈLE : {motor_type}")
        print(f"📊 Échantillons totaux : {X.shape[0]}")
        print("=" * 50)

        X_train, X_test, Y_train, Y_test = train_test_split(
            X, Y, test_size=TEST_SPLIT, random_state=42
        )

        scaler_X = StandardScaler()
        X_train_scaled = scaler_X.fit_transform(X_train)
        X_test_scaled = scaler_X.transform(X_test)

        scaler_Y = StandardScaler()
        Y_train_scaled = scaler_Y.fit_transform(Y_train)
        Y_test_scaled = scaler_Y.transform(Y_test)

        X_train_t = torch.FloatTensor(X_train_scaled)
        Y_train_t = torch.FloatTensor(Y_train_scaled)
        X_test_t = torch.FloatTensor(X_test_scaled)
        Y_test_t = torch.FloatTensor(Y_test_scaled)

        train_dataset = TensorDataset(X_train_t, Y_train_t)
        train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)

        model = ActuatorNet(input_size=X.shape[1])
        criterion = nn.HuberLoss(delta=1.0)
        optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

        for epoch in range(EPOCHS):
            model.train()
            train_loss = 0.0

            for batch_X, batch_Y in train_loader:
                optimizer.zero_grad()
                predictions = model(batch_X)
                loss = criterion(predictions, batch_Y)
                loss.backward()
                optimizer.step()
                train_loss += loss.item()

            model.eval()
            with torch.no_grad():
                val_predictions = model(X_test_t)
                val_loss = criterion(val_predictions, Y_test_t).item()

            if (epoch + 1) % 10 == 0 or epoch == 0:
                print(
                    f"Epoch [{epoch + 1}/{EPOCHS}] | Train Loss: {train_loss / len(train_loader):.4f} | Val Loss: {val_loss:.4f}"
                )

        # --- Visualisation ---
        model.eval()
        with torch.no_grad():
            preds_scaled = model(X_test_t).numpy()

        preds_real = scaler_Y.inverse_transform(preds_scaled)
        Y_test_real = scaler_Y.inverse_transform(Y_test_scaled)

        # --- CALCUL DES MÉTRIQUES DE L'IA ---
        rmse = np.sqrt(mean_squared_error(Y_test_real, preds_real))
        mae = mean_absolute_error(Y_test_real, preds_real)
        r2 = r2_score(Y_test_real, preds_real)

        print(f"\n📊 RÉSULTATS SCIENTIFIQUES POUR {motor_type} :")
        print(f"   - RMSE : {rmse:.3f} Ampères")
        print(f"   - MAE  : {mae:.3f} Ampères")
        print(f"   - R²   : {r2:.3f}")

        # --- LE TEST DE HWANGBO (BASELINE) ---
        print(f"\n🔬 TEST DE RÉFÉRENCE (BASELINE PD) POUR {motor_type}")

        # Extraction des variables brutes (avant normalisation StandardScaler)
        # Colonne 0 = Erreur de position, Colonne 1 = Vitesse
        pos_error_test = X_test[:, 0]
        vel_test = X_test[:, 1]

        # Tes 3 profils de test (Isaac et Réel utilisent mathématiquement les mêmes gains de base)
        profiles = {
            "Profil Initial (ISAAC) / Réel (CAN)": {"Kp": 50.0, "Kd": 1.0},
            "Profil Ajusté (GAZEBO)": {"Kp": 120.0, "Kd": 3.0},
        }

        for nom, gains in profiles.items():
            kp = gains["Kp"]
            kd = gains["Kd"]

            KT = 0
            if motor_type == "RMD_X8_PRO_V2_1to9":
                KT = 3.75 / 8
            elif motor_type == "RMD_X8_PRO_H_V3_1to6":
                KT = 13 / 5

            DEG_TO_RAD = math.pi / 180.0

            # Calcul du courant/couple idéal généré par l'équation mathématique pure
            torque_ideal = (pos_error_test * DEG_TO_RAD * kp) - (
                vel_test * DEG_TO_RAD * kd
            )
            courant_ideal_amperes = torque_ideal / KT
            courant_ideal_amperes_clamped = np.clip(courant_ideal_amperes, -15.0, 15.0)

            # Calcul du RMSE de cette équation idéale par rapport à la réalité
            rmse_ideal = np.sqrt(
                mean_squared_error(Y_test_real, courant_ideal_amperes_clamped)
            )

            print(f"RMSE du {nom} (Kp={kp}, Kd={kd}) : {rmse_ideal:.3f} Ampères")

            if rmse_ideal > rmse:
                ratio = rmse_ideal / rmse
                print(
                    f"   -> L'Actuator Net est {ratio:.1f}x plus précis que l'équation mathématique !"
                )
            else:
                print(f"   -> L'équation est meilleure que l'IA (Très rare)")

        print("-" * 60)
        plot_limit = min(500, len(Y_test_real))
        plt.figure(figsize=(12, 5))
        plt.plot(
            Y_test_real[:plot_limit], label="Courant Réel", color="#e74c3c", alpha=0.8
        )
        plt.plot(
            preds_real[:plot_limit],
            label="Courant Prédit",
            color="#2c3e50",
            linestyle="--",
        )
        plt.title(f"Évaluation : {motor_type}")
        plt.legend()

        # Sauvegarde du graphique
        plot_filename = f"eval_{motor_type}.png"
        plt.savefig(plot_filename)
        print(f"📉 Graphique sauvegardé sous : {plot_filename}")
        plt.close()

        # --- Exportation Modèle Enveloppé ---
        wrapped_model = IsaacWrappedNet(model, scaler_X, scaler_Y)
        wrapped_model.eval()

        dummy_input_raw = torch.randn(1, X.shape[1])
        traced_script_module = torch.jit.trace(wrapped_model, dummy_input_raw)

        model_filename = f"actuator_net_{motor_type}.pt"
        traced_script_module.save(model_filename)
        print(f"💾 Modèle Isaac Lab généré : {model_filename}\n")


if __name__ == "__main__":
    main()
