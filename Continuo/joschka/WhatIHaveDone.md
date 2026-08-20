I am working on a quadruped that will do search and rescue missions. 

What I need to do for now : setup lidar, then publish a grid to the /lidar topic (PointCloud or Float32MutliArray) the grid can change in function of the policy.
# Day 1
I familarised my self with all the pdfs they gave me.
Meet Dr. Alex and all the other student. Get an idea what I shout do: setup the lidar, connect it to /lidar in ros and then use the "neck" to map the environement in 3d.
Connected the lidar (ouster OS0 64) with ethernet cable to pc.

# Day 2
Setup Docker and ros noetic to work (display issues)
Did not update the lidar firmware just used an old version of https://github.com/ouster-lidar/ouster-ros.git
Can see the lidar in gz (see video 30/06/2026)
Launch with `mitacs_ouster.launch`

# Day 3
I have made the lidar publish a grid of 1.6 x 1m with (rows x cols) 17 x 11 points with a resolution of 0.1. (see video 02/07/2026). I can update if the policy is croutch (it adds a point on the back so that it can see the ceiling). It needs to see in front (from 0 to 1.6m). So that it ignores left, right and his back. I need to becarfull that the the points that it gets are always perfectly parrallel points to the ground (because the RL is trained so).

To get the grid with all the points that I'm getting from lidar I use this formula : $i_{row} = \lfloor \frac{x - x_{min}}{x_{max} - x_{min}} \times N_{rows} \rfloor$  
x (in meters) the actual points that the lidar is seeing. $x_{min}$ and $x_{max}$ (m) the "seeing" zone. $N_{rows}$ number of rows. $i_{row}$ the number of column.

Corrected so that the lidar think it always faces the ground. You can visualise the Float32MutliArray on /lidarvisu and see with the grid with more points on lidarcap

## Mesure that the lidar doesn't break the limit of 1m/s at 
### Alpha 0.2
=== RÉSULTATS DE L'ANALYSE DU BRUIT (Sans les 0.0 purs) ===
Transitions analysées            : 42914
Transitions ignorées (Vides)     : 50399
----------------------------------------
Vitesse de saut max (Positif)    : 1.141 m/s
Vitesse de saut max (Négatif)    : -2.060 m/s
Vitesse moyenne de fluctuation   : 0.015 m/s
----------------------------------------
❌ TEST ÉCHOUÉ : Le seuil de +- 1 m/s a été dépassé !
   -> Nombre de dépassements : 14 fois (0.03% des vraies mesures)

### Alpha 0.25 (appart)
=== RÉSULTATS DE L'ANALYSE DU BRUIT (Sans les 0.0 purs) ===
Transitions analysées            : 38980
Transitions ignorées (Vides)     : 4932
----------------------------------------
Vitesse de saut max (Positif)    : 1.371 m/s
Vitesse de saut max (Négatif)    : -1.333 m/s
Vitesse moyenne de fluctuation   : 0.016 m/s
----------------------------------------
❌ TEST ÉCHOUÉ : Le seuil de +- 1 m/s a été dépassé !
   -> Nombre de dépassements : 19 fois (0.05% des vraies mesures)

### Alpha 0.50
=== RÉSULTATS DE L'ANALYSE DU BRUIT (Sans les 0.0 purs) ===
Transitions analysées            : 42914
Transitions ignorées (Vides)     : 50399
----------------------------------------
Vitesse de saut max (Positif)    : 3.146 m/s
Vitesse de saut max (Négatif)    : -5.431 m/s
Vitesse moyenne de fluctuation   : 0.039 m/s
----------------------------------------
❌ TEST ÉCHOUÉ : Le seuil de +- 1 m/s a été dépassé !
   -> Nombre de dépassements : 164 fois (0.38% des vraies mesures)

### Alpha 1
=== RÉSULTATS DE L'ANALYSE DU BRUIT (Sans les 0.0 purs) ===
Transitions analysées            : 41010
Transitions ignorées (Vides)     : 52303
----------------------------------------
Vitesse de saut max (Positif)    : 8.242 m/s
Vitesse de saut max (Négatif)    : -7.312 m/s
Vitesse moyenne de fluctuation   : 0.092 m/s
----------------------------------------
❌ TEST ÉCHOUÉ : Le seuil de +- 1 m/s a été dépassé !
   -> Nombre de dépassements : 792 fois (1.93% des vraies mesures)

At alpha 0.20 we get 0.2s to react to 90% of obstacle and 0.08s as mean reaction time. 0.2s corresponds to 50Hz which is the speed at which the sim moves. So we will take alpha = 0.20

# Day 4 (03/07)
Beggining to use the nucleo board. I have made the motor move now I want to control them and send the messages to ros.

# Day 5 (06/07)
Getting the nucleo to work with the old code. I found it I had to flash it back but now the angles wont begging computed correctly. To make the stm board work you need to unplug the encoder so they would initialise at the wring values.
There is a problem with the code idk what but see "*Motor_Performance_Analysis*" graphs but they don't make any sens to me.

# Day 6 (07/07)
Trying to get the neck to work. I tryied the default version with putty but it doesn't work. I don't get why it doesn't listen to the serial.
I undestand it's the motor driver that is faulty. The second output ins't working.

# Day 7 (08/07)
It's not the motor dirver fault. I tryied a simple move back and forward script and everything was working great.
I am reimplmenting everything on arduino IDE and it's working. 
The encoder are still not very friendly. These are absolut magnetic SPI.

It's now working but there is a lot of wigle room so eventhoug the motor moves the outside parts doesn't. So I unmounted the motor and tied the srews

# Day 8 09/07
It's working see *Working_Motor_Performance_Analysis_14.xlsx*.

I am now sending the motors info to ros. 
I had to **change some pins** because I had to find output with some clock (SCK).
I moved 

# Day 9 10/07
Today I need to combine the lidar and Orbita.
Updating ouster lidar firmware from v2.5.2 to v2.5.3
But I had to downgrade in my dockerfile the ouster-ros.
It works from my pc with ros to the nucleo that makes the lidar neck move.

I need to somehow make the lidar fit the simulation but the problem is that the lidar of the sim comes from above the robot and the real lidar is at the front of the robot. 
So I have multiple choises :
1) I map the env with slam and give the map in real time to the rl. So I have to send the zone around the robot as a grid.
2) Move the head to map a max of the env and assume that the rest is flat.

The problem is that the lidar is at the front. It can't perfectly see everything around it so it can't produce the real grid for the rl policy. I will map the env so that the robot can use it eventhoug it can't actively see it.
Question for Stefan:
1) How can I simulate the robot in a rougth env and add a lidar on it (urdf?)
    i) How to make the robot turn on it self/go somewhere
2) I will assume that every point I did not see is flat
3) Move the neck a maximum to get more info at the start

# Day 10 (13/07)
Today I am putting the quadruped into simulation. I updated the urdf to add the lidar. Then I will use [grid_map](https://github.com/ANYbotics/grid_map) to construct a height map of the environement. 
Launch with `elevation_mapping.launch`

# Day 11 (14/07)
For now I spawn the robot urdf and I publish my grid map on `/elevation_mapping/elevation_map`. I can now see elevation points on rviz. I publish the grid on `/lidar`.
1) I had to adjust the pid gains.
2) The order for the rl is `["FL_HAA", "FR_HAA", "HL_HAA", "HR_HAA", "FL_HFE", "FR_HFE", "HL_HFE", "HR_HFE", "FL_KFE", "FR_KFE", "HL_KFE", "HR_KFE", "HL_AFE", "HR_AFE"]`
3) The joint position actions scale is 0.5
4) The default angles are: "FL_HAA": 0.0, "FR_HAA": 0.0, "HL_HAA": 0.0, "HR_HAA": 0.0, "FL_HFE": 0.4102, "FR_HFE": 0.4102, "HL_HFE": -0.6981, "HR_HFE": -0.6981, "FL_KFE": -1.2716, "FR_KFE": -1.2716, "HL_KFE": 1.676, "HR_KFE": 1.676, "HL_AFE": -1.7219, "HR_AFE": -1.7219

Test with just the flat policy.

# Day 12 (15/07)
Trying to setup Luis simulation to see what he did. The commands are : 
`roslaunch quadruped_gazebo gazebo.launch
roslaunch quadruped_gazebo spawn_control.launch
roslaunch quadruped_control bringup_rl.launch`
I copied Luis files and you can launch the luis config with lidar with `roslaunch mitacs luis_bringup.launch`
I took his code and added the mapping part over it so that the robot creates an elevation map.

The pipe line for the simulated lidar is :
1) URDF : <sensor type="ray" name="ouster_sensor"> combined with <plugin name="gazebo_ros_laser_controller" filename="libgazebo_ros_velodyne_laser.so"> which is published on `/ouster/points`
2) You need to create the TF tree which is done with odom_to_tf.py and robot_state_publisher publishes to the `world` TF
3) With the /ouster/points you can calculate the world position of each point
4) Creation of the 2.5d grid which is published on /elevation_mapping/elevation_map

If you want the points to go farther you have to modify `length_in_x` in elevation_mapping.yaml

# Day 13 (16/07)
Luis configured the pid for just walking and for the flat policy.
Tuning for rough policy.

# Day 14 (17/07)
I think I have a good pid. I created a simple script to move each part individualy `manual_joint_tuner.py`.
I have one leg that is up I don't know why.

I have to tune tow legs front and back because robot is mirror for this I can make the robot go up and down and then for haa make one leg move at a time on the side but other legs a bit out so that the robot doesn't fall.

# Day 15 (20/07)
I made `stance_tuner.py` I could tune my pid for the legs. 
See *HL_HFE_KFE.png*, *FL_HFE_KFE.png*, *HL_AFE.png* and *HL_HAA.png*.
But the robot still falls when I tell him to go forward. I use the same urdf that was used for the rl.
**I undestood I gave the wrong start positions.**

# Day 16 (21/07)
Still not walking strait.
I visualised the output of *joint_positions_rough_with_flat_terrain.csv* with `replay_policy.py` to see how the robot should walk.
I also visualised the output of the flat and the rough policy with the same data `joint_positions.csv` see *compareson_flat_rough_same_data* folder.
**I put the same data but I don't have the same output for the same policy**

# Day 17 (22/07)
I am trying to pin down what is the problem I think that I don't have the same policy as in isaac sim because why else would I have different output with same input.
I have the same policy as in isaac sim (2ae2ad6d363eb7d1a739e867d2a003f9 2025-09-15_13-06-21_fixed-slope-2.onnx) md5 checksum
**I had the joint in the wrong order** now it's working. Like I have the same output with the same input for *flat* and *rough*! It also works with lidar data set to 0. So did I show that the robot will work whithout a lidar on a flat terrain? See `same_input&output.png`.
But it still doesn't work in gz with rough policy

# Day 18 (23/07)
I will use florent package.
I broke in multiple piceses the urdf: 
- `continuo.urdf.xacro`: the main file that includes the other files
- `materials.xacro`: def the materials
- `sensors.xacro`: link and joints for the lidar and imu
- `transmissions.xacro`: for the transmissions that makes the link between the URDF joints and the PIDs
- `legs.xacro`: All the legs stuff (inertial, visual, collision, link, joint)
I switch to florent package it's kindof working but the robot isn't walking

# Day 19 (27/07)
Let's find why he isn't walking.
From what I understand `gazebo_ros_control` is applying PIDs. I am retuning the PIDs for each joint. I have an RMSE very small on almost all joints around 0.01. On a static movement.
The legs move very quickly when the robot touches the ground. I try adding a smooth value but it did not fix. So I looked at the action that the rl policy gave me and they seem good. 
**I have a big gap between target position (= q0 + rl_output * scale) and real position**

I need to try on isaac sim if I have the same issue. Because I know the policy is good. Mabe a gazebo issue.

# Day 20 (27/07)
I noticed that the robot uses so much torque to move enven in the air (see *in_air* folder and see *in_air.png*). I tested with multiple aplha values (i start my test at 3s). 
For alpha :
- 0.5 4 legs that hit 120nm limit.
- 0.4 6 legs (wtf)
- 0.3 3
- 0.2 2
0.2 or 0.3 seems to be good. But the robot still can't manage to go forward.

I took the isaac sim configs on effort for the urdf, the velocity, the pid. But the robot still wont walk it just falls under his weight. The robot does 31.6kg (torso: 15.3; legs: 16.3). So we have 31.6*9.81=310 N. 310/4 = 77.5 N for each leg. But when walking only 2 legs need to have the weight so 155 N. The max N * m the robot has is 20 (urdf). Therefore my toque will be 20 = x * 155 <=> x = 0.13 m.

But even with 120 torque the robot takes max 40 Nm (with p: 50, d: 1 as in isaac sim) so the legs moves 0.26 m approximately.

There is a high chance it's the IMU that makes the rl panic.

# Day 21 (28/07)
I talked with dr alex and he said that I can be a missmatch between the frequency of the policy and the sim. But `rospy.Rate(50)` assures that what is executed in the loop (sending rl_target, policy takes it's decision, exporting to csv) is done every 50Hz and at the same time.

For /joint_targets_rl I get : average rate: 50.000 min: 0.017s max: 0.023s std dev: 0.00184s window: 39
For /{jname}_position_controller/command I get average rate: 50.086 min: 0.017s max: 0.023s std dev: 0.00181s window: 30
So it seems to be publishing and reading at the right rate.

I saved a lot of performance (150% to 15%) for policy_node.py by :
1) Putting onnx on a single thread
2) Adding throttle_model_states in gazebo.launch
**This makes the robot walk**

The lidar doesn't goes to the policy I need to fix that. Fixed switch to type: laser in `elevation_mapper.yaml`. But I need to stil test it with the robot in the air.
The /lidar data is not right the /ouster is good and I can't figure out if /elevation_mapping/elevation_map is good or not but I think there is a problem there.

# Day 22 (29/07)
I found the problem: the points are good but they are kept in memory even if the object isn't there. Because to update there needs to be an object behind the deleted object for the deleted object to disapear. 
**So I had to put the lidar pointing to the ground.**
I made the real time factor much better (the performance of the sim) by lowering the lidar quality.
I installed my sim on the ContinuO pc.

# Day 23 (30/07)
I am tuning pid for the legs of the robot for them to not vibrate.
In isaac sim the robot legs take time to move where it wants so it takes long steps. In my sim the legs vibrate very quickly.
I forgot to put q - q0 in joint_pos.
**Now the robot walks really good!!!!!**

# Day 24 (31/07)
I have the certitude that the lidar works how it should now.
I talked today with dr Alex to know what I should do next. The conclusion I have to gather as much information with the lidar as possible. I can do it how I want. I can do reinforcement learning or good old engeering. I want to do rl. I want first to move the hole body and keep the 4 contact points of the legs at the same position, so they don't move at all. Then modify the policy and add the fact that the robot can move it's neck.

# Day 25 (04/08)
I am installing isaac sim with docker because the continuo pc is on ubuntu 20.04. Generated USD form usdf.
What I need to do 1. install isaac sim & lab 2. convert urdf to usd 3. train the legs not to move 4. train the robot to move it's body where I want. 5. Add the abylity to rotate it's neck.

TODO ajouter la possibilité au lidar de tourner.

# Day 26 (05/08)
I finnaly installed isaac sim & lab. But it's very finicky.

**TODO : on the sim I have to put back the imu in the code because for now I use a magic trick.**
I started a bit of rl

# Day 27 (06/08)
Implementation of the rl.
I implemented a
1) Reward: 
    i) +5 for reaching the target that I want the head to reach it growth exponentialy.
2) Punition
    i) -2 Feet mouvement
    ii) -0.2 Each joint deviation
    iii) -0.5 haa and afe deviation
    iv) -0.05 action rate to high (for jitter)
    v) -0.001 excessive speed
    vi) -0.00000025 excessive acceleration
    vii) -0.00001 for torq so that the quadruped learns to move less
3) Death (-200)
    --i) If a feet moves quicker then 0.05 m/s-- this would kill the robot every time
    --ii) if the any other part then the feet touches the ground.--

What I need to look for is : mean reward
I added Domain Randomization Methods but not Learning with Disturbances.

## How does this rl work ?
It's a closed loop. You 
1) Observe (get info from motors, distance to goal...).
2) Get and take action to the motor that the ai sent you
3) Environement, isaac lab calculate consequences for your mouvement
4) Take the reward.

It worked good (see video 06/08). But I wasn't fully satisfied so I changed somethings.
Firstly now I use a velocity controller instead of a static position goal. New challenges appear with that. The robot need to know when to stop going forward and stay on it's feets even if it means getting less reward.
Now I have Noise Injection, Domain Randomization, System Disturbances

Want I did is remove every death penalty and replaced it with a penality for illegal contacts for shoulder and upper leg.

# Day 28 (07/08)
I am still tuning the rl. Doubled the reward for reaching target. First I train the target to be within -0.5 to 0.5 and then after it quind of works I put -1.5 to 1.5. So that the robot learns how to move a bit a then far away.

But I am reading a [Isaac Sim-to-Real: Reinforcement Learning based Locomotion for Quadrupeds](https://arxiv.org/abs/2607.18135) about zero shot sim-to-real. What I learned is that putting noise in observation, do domain randomization (make the floor a bit more slipery for example), modifing the center of mass. Will help the robot to be more stable.
A notable thing they did in the research paper is that they **recorded real movement from the robot and trained a small neural network** on it. So that the output of the rl is fead into this small network and that the observation are given y this network which simulates better the real behaviour of the motors.
Anothere thing that they did is **train the policy at 50Hz but on the real robot it runs at 100Hz**.

Now reading the sim-to-sim nvidia isaac lab documentation page.
You can implement a robot schema to never have to bother about the joint order of each backend.
I am learning about predictor and corrector, Kalman filter, teacher student,

I think that using a **teacher student approch is much better for all the lidar and imu stuff on the real ContinuO**.
I had a problem that the robot wouldn't follow my commands. It spawned had it's legs extended like in the urdf, then the observation said that the legs are in the ground and the terminaison reward kicked in to say stop everything. So now I give a grace period of 50 frames let's see how it will now learn.
I found this because I just removed the terminaison code and my episod length went through the roof.

# Day 29 (10/08)
The rl trained for 50 000 iteration. It looks good (*see saved_policy_josch/GoodTest1/*) but it's not good engough. I added a bigget penalty for 
- feet velocity: 0.5 --> 5.0
- action rate: 0.05 --> 0.5
- dof_acc: 2.5e-7 --> 1.0e-4
I also added my torax to the custom base translation penality, so that the robot can turn it's chest but not move it.

In the paper [Extrem Parkour with Legged Robot](https://arxiv.org/abs/2309.14341) which has been created by CMU / UC berkley in 2023 which uses a teacher student approach. ROA is used to predict sensors so that the robot can walk on different terrain. It's done durring learning. The paper also uses an interesting approach that **the robot choses the final path**. The human uses a joystick to tell him the direction but an algorithme decides at the end where to go.
I want to read after [Learning Agile and Dynamic Motor Skills for Legged Robots](https://arxiv.org/pdf/1901.08652).
It's **better to have a depth camera for parkour and indor locomotion**.

I have reintruduced the kill after touching the ground with it's upper/middle legs. Durin this test the robot is to scared to move so it just did a hug to the ground and refused to move.
This time I had to wait until 1100 to 1200 steps to see real improvements.
I added the fact that if the torso is at 0.5 it will get a new reward.

In [Learning Agile and Dynamic Motor Skills for Legged Robots](https://arxiv.org/pdf/1901.08652) we learn that the biggest and novel idea is that you have to create a small neural network (**Actuator Net**) to predict the torque of the real motors. I have to use a teacher student approach for the lidar and imu because of State Estimation Drift. SED is used because it's much more reliable and quicker then constructing your own elevation map. And it's hard to simulate a lidar drift.

# Day 30 (11/08)
I came this morning to weird graphs after 20k the rl started again to do illegal touches so I upped reward track to 25, base height to 5, penality terminal 2000, feet velocity and base translation to 2.
I removed the base height reward and added SHANK to illegal contacts. I also modified actor_hidden_dims and critic_hidden_dims to [256, 128, 64] to improve training speed.
I tryied to remove everything and just keep terminaison and heigh reward but the robot couldn't still get up. So I try again and remove shank from illegal contacts.
even more simple now no more termination

# Day 31 (12/08)
I think I found the pb because I changed the urdf position to have a more crouched position when I instentiate with the old init values it would make the robot legs go everywhere so I modified them to 0.

I talked with Dr. Alex and he said that we will keep the old crusty motors that run at 10 Hz. So I will need to 
1) Create a neural network that predicts motor torque
2) Create a teacher student for lidar and imu
3) Retrain the policy while taking account of my new addition and Florents conclusions.

There was also an issue that in the usd the foot and legs where one single object so it got illegal contacts all the time.

Now I will build my actuator net but I need to make a test rig. 

# Day 32 (13/08)
I am making the data of the actuator net data in air. See video (on phone 13/08)

# Day 33 (14/08)
I have collected data in the air now I have to do it on the ground. I always have a motor failling when getting back to default position. For a full day I am trying to get the data but the motors keep always failling.

# Day 34 (17/08)
I want to get that motor data but I have to find a better way to collect data.
Sometimes I get some motors that just stop working and I can't restart the motors so I have to restart everytime the pc.
For the test bench I attach a weight to the end of the leg. It can't lift 3.6, 1.5kg seems good. I also did 1kg (see *actuator_net_squt_data_Xk* in continuo control/Obs). See video form 17/08.²
The can of the hind left can isn't working correctly... See graph in odt file.
I took the mesures on front right leg and back left leg.

# Day 35 (18/08)
My inputs of my actuator net are pos_error = Target - Actual, actual_vel, actual_pos.
The output is: actual_current. Because of $Torque = Current * Motor_Const$ 
Because I got 3 entries and I give a history of 6 steps = 18 neurons in entry
Then I got 3 hidden layers of 64 neurons each.

Using "Learning agile and dynamic motor skills for legged robots" (Jemin Hwangbo et al., Science Robotics, Janvier 2019) methods here are the results of my training: 

* RMD_X8_PRO_V2_1to6:
 - RMSE : 1.692 amps
 - MAE  : 1.276 amps
 - R²   : 0.638

RMSE for:
1) Default Isaac : Kp=50.0, Kd=1.0 : 6.238 amps
2) Gazebo : Kp=120.0, Kd=3.0 : 8.703 A
RMSE = (pos_error * Kp) - (vel * Kd)

* RMD_X8_PRO_V2_1to9:
 - RMSE : 1.660
 - MAE  : 1.352
 - R²   : 0.702

1) Default Isaac : Kp=50.0, Kd=1.0 : 11.810 amps
2) Gazebo : Kp=120.0, Kd=3.0 : 13.249 A
Let's analyse a bit. Since my graphs (see *Continuo/actuator_net/saved/*) goes from -10 to 5 so a 15 amps amplitude my MAE (mean absolute error) is only 1.3 amps. I clamped output current at 15 in the results are not absurd.

I launch the training on the desktop. Flat policy has only 1500 iteration with 4 096 robots.
Rough has 95 200 iteration and other 50k+.

# Day 35 (19/08)
The training was done on 80% of the data set and the nn was tested on the last 20% of the data set

          Rang         | Modèle / Configuration            | Gain Moyen |      RMSE Moyen     |    R² Moyen
  ---------------------|-----------------------------------|------------|---------------------|---------------
            1          | GELU_128*4_learn_0.0005_batch_128 |    7.31x   |       1.348 A       |        0.787
            2          | GELU_64*4_learn_0.0005_batch_128  |    7.24x   |       1.360 A       |        0.783
            3          | GELU_64*4                         |    7.17x   |       1.374 A       |        0.779
            4          | learn_rate_0.0005                 |    7.01x   |       1.403 A       |        0.770
            5          | 64*4                              |    6.72x   |       1.465 A       |        0.750
            6          | learn_rate_0.005                  |    6.71x   |       1.468 A       |        0.749
            7          | batch_128                         |    6.23x   |       1.598 A       |        0.702
            8          | 128*3                             |    6.03x   |       1.656 A       |        0.679
            9          | Huber_alpha_1                     |    6.02x   |       1.663 A       |        0.676
           10          | Huber_alpha_3                     |    5.91x   |       1.687 A       |        0.667
           11          | weight_decay                      |    5.91x   |       1.696 A       |        0.662
           12          | Huber_alpha_0_5                   |    5.84x   |       1.715 A       |        0.655
           13          | L1Loss                            |    5.76x   |       1.743 A       |        0.643
           14          | batch_1024                        |    5.28x   |       1.889 A       |        0.582
           15          | batch_2048                        |    4.70x   |       2.108 A       |        0.481


To train teacher student for 
- IUM : [RMA: Rapid Motor Adaptation for Legged Robots](https://arxiv.org/pdf/2107.04034)
- Lidar [Learning robust perceptive locomotion for quadrupedal robots in the wild](https://arxiv.org/pdf/2201.08117)
Let's train a student teacher policy.
I have the code (see *Yma-Mitacs_ContinuO_IsaacLab*)
