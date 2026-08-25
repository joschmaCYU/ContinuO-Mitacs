import numpy as np
import onnxruntime as ort
import argparse


def get_next_step(data_file, onnx_model_path, output_file):
    # 1. Lecture de l'observation
    try:
        with open(data_file, "r") as f:
            line = f.readline().strip()
            if not line:
                print("Erreur : Le fichier d'entrée est vide.")
                return

            str_values = line.replace(",", " ").split()
            observation = np.array([float(x) for x in str_values], dtype=np.float32)

    except FileNotFoundError:
        print(f"Erreur : Fichier introuvable -> {data_file}")
        return
    except ValueError as e:
        print(f"Erreur de conversion : {e}")
        return

    # 2. Chargement du modèle ONNX
    try:
        session = ort.InferenceSession(onnx_model_path)
        input_name = session.get_inputs()[0].name
        input_data = np.expand_dims(observation, axis=0)

    except Exception as e:
        print(f"Erreur lors du chargement ONNX : {e}")
        return

    # 3. Exécution de l'inférence et écriture
    try:
        result = session.run(None, {input_name: input_data})
        action = result[0][0]

        # Formatage des valeurs avec 6 décimales
        action_str = " ".join([f"{val:.6f}" for val in action])

        # Écriture dans le fichier texte
        with open(output_file, "w") as f:
            f.write(action_str + "\n")

        print(f"Succès : {len(action)} valeurs écrites dans '{output_file}'")

        return action

    except Exception as e:
        print(f"Erreur lors de l'inférence : {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test une policy ONNX et sort le résultat dans un TXT."
    )
    parser.add_argument(
        "--data",
        type=str,
        default="obs.txt",
        help="Fichier texte d'entrée (observation)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="/root/catkin_ws/src/mitacs/florant/f_quadruped_control/policies/flat_pushing_pt2.onnx",
        help="Modèle ONNX",
    )
    parser.add_argument(
        "--out", type=str, default="action.txt", help="Fichier texte de sortie (action)"
    )

    args = parser.parse_args()

    get_next_step(args.data, args.model, args.out)
