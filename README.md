# Yma-Mitacs-Global-Link-UCalgary
<p align="center">
  <img width="563" height="540" alt="ContinuO" src="https://github.com/user-attachments/assets/30879ef1-416f-49a3-972a-24d325f776e6" />
</p>

**[User manual](https://github.com/joschmaCYU/ContinuO-Mitacs/blob/main/USER_MANUAL.md)**
  
### Context & Global Objective
This project (developed as part of a MITACS research internship at the University of Calgary) focuses on the control and navigation of the ContinuO quadruped robot designed for search and rescue missions. It combines Reinforcement Learning (RL) trained in Isaac Sim / Isaac Lab, simulation in ROS / Gazebo, and deployment on the physical hardware.

### High-Level Repository Structure
#### 1. actuator_net — Actuator Modeling Neural Network (Sim-to-Real Gap)
  - Objective: Bridge the sim-to-real gap by learning real motor dynamics and predicting actual torque/current from past kinematics (for RMD-X8 Pro motors).
  - Contents:
      - train_actuator_net.py: PyTorch training script for an MLP using state history to predict motor
      current.
      - data: Real test-rig datasets collected under different conditions (in-air, with 1.0 kg / 1.5 kg
      payloads).
      - saved: Benchmarked model weights across architectures, activations (GELU), loss functions (Huber, L1), and batch sizes.

#### 2. joschka — LiDAR Perception, RL Integration, Firmware & Utilities
  - RL Policies (Policy):
    - Pre-trained exported ONNX policies for varied terrains and behaviors: flat ground (flat_policy.onnx), rough terrain (rough_fixed-slope-2.onnx), etc.
  - Firmware & Electronics (arduino):
    - Embedded firmware (STM32 Nucleo / Arduino) controlling the motorized neck (Orbita mechanism) for the LiDAR, reading SPI absolute magnetic encoders, and ROS serial bridging (easy_ros).
  - Perception & 2.5D Elevation Mapping (config, scripts):
    - Pipeline using the Ouster OS0-64 LiDAR and elevation_mapping to generate a 2.5D height grid fed directly into RL policy observations.
  - Analysis & Helper Scripts (helper):
    - Joint PID tuning tools (manual_joint_tuner.py, stance_tuner.py), policy replay scripts, 2D ONNX
      simulators, and noise analyzers.

#### 3. florant — ROS Control Stack (Simulation & Real Robot)
  - f_quadruped_control:
    - Core controller (policy_node.py) running ONNX models in real-time at 50 Hz.
    - Dynamic policy switcher node (quadruped_switch_policy_node.py).
    - URDF / Xacro models, meshes (STL / DAE), Gazebo launch configurations, and controller parameters.
  - f_quadruped_real:
    - Hardware interface drivers (quadruped_leg_real_node.py) managing CAN bus communication with leg motors, IMU integration, clock synchronization, and emergency stop.
  - f_quadruped_monitoring:
    - Real-time command and robot state monitoring / visualization (commands_visu_node.py).
