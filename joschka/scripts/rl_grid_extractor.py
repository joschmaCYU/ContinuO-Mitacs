#!/usr/bin/env python3
import rospy
import numpy as np
from grid_map_msgs.msg import GridMap
from std_msgs.msg import Float32MultiArray
from sensor_msgs.msg import PointCloud2
import sensor_msgs.point_cloud2 as pc2
from std_msgs.msg import Header


class GridExtractor:
    def __init__(self):
        rospy.init_node("rl_grid_extractor", anonymous=True)

        # Dimensions requises par l'environnement RL
        self.target_rows = 17  # X (Avant/Arrière)
        self.target_cols = 11  # Y (Gauche/Droite)

        self.pub = rospy.Publisher("/lidar", Float32MultiArray, queue_size=1)
        self.sub = rospy.Subscriber(
            "/elevation_mapping/elevation_map", GridMap, self.map_callback
        )
        self.pub_vis_lidar = rospy.Publisher("/lidar_visu", PointCloud2, queue_size=1)
        rospy.loginfo("Extracteur RL prêt (17x11). En attente des données...")

    def map_callback(self, msg):
        try:
            layer_idx = msg.layers.index("elevation")
            size_x = msg.data[layer_idx].layout.dim[0].size
            size_y = msg.data[layer_idx].layout.dim[1].size
            resolution = msg.info.resolution

            raw_data = np.array(msg.data[layer_idx].data)
            raw_data = np.nan_to_num(raw_data, nan=0.0)
            grid = raw_data.reshape((size_x, size_y), order="F")

            grid = np.roll(grid, -msg.inner_start_index, axis=0)
            grid = np.roll(grid, -msg.outer_start_index, axis=1)

            # ==========================================
            # 1. CORRECTION DU "MICROSCOPE" (ÉCHELLE PHYSIQUE)
            # ==========================================
            # L'IA s'attend à un espacement standard de 10 cm (0.1m)
            rl_spacing = 0.1
            step = max(1, int(round(rl_spacing / resolution)))

            # Taille totale en pixels de la zone étendue
            span_x = (self.target_rows - 1) * step + 1
            span_y = (self.target_cols - 1) * step + 1

            start_x = (size_x - span_x) // 2
            start_y = (size_y - span_y) // 2

            sub_grid = grid[
                start_x : start_x + span_x : step,
                start_y : start_y + span_y : step,
            ]

            sub_grid = np.flip(sub_grid, axis=(0, 1))
            sub_grid_t = sub_grid.T
            flat_z = sub_grid_t.flatten(order="C")

            out_msg = Float32MultiArray()
            out_msg.data = flat_z.tolist()
            self.pub.publish(out_msg)

            # ==========================================
            # 2. CORRECTION DE L'ILLUSION RVIZ (REPÈRE GLOBAL)
            # ==========================================
            # On calcule les coordonnées par rapport au centre global de la map
            robot_x = msg.info.pose.position.x
            robot_y = msg.info.pose.position.y

            # On recrée les axes (en tenant compte du np.flip précédent)
            x_local = (
                np.arange(self.target_rows) - (self.target_rows - 1) / 2.0
            ) * rl_spacing
            y_local = (
                np.arange(self.target_cols) - (self.target_cols - 1) / 2.0
            ) * rl_spacing

            x_coords = robot_x + x_local[::-1]
            y_coords = robot_y + y_local[::-1]

            grid_x, grid_y = np.meshgrid(x_coords, y_coords, indexing="ij")

            flat_x = grid_x.T.flatten(order="C")
            flat_y = grid_y.T.flatten(order="C")

            points_3d = np.column_stack((flat_x, flat_y, flat_z)).tolist()

            header = Header()
            header.stamp = rospy.Time.now()
            # On remet le repère global d'origine (souvent 'odom' ou 'map')
            header.frame_id = msg.info.header.frame_id

            if len(points_3d) > 0 and hasattr(self, "pub_vis_lidar"):
                cloud_msg = pc2.create_cloud_xyz32(header, points_3d)
                self.pub_vis_lidar.publish(cloud_msg)

        except Exception as e:
            rospy.logerr(f"Erreur dans map_callback: {e}")


if __name__ == "__main__":
    try:
        GridExtractor()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
