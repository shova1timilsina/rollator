# Smart Rollator - Quick Reference Guide

## Quick Start (5 minutes)

```bash
# 1. Source ROS 2 and workspace
source /opt/ros/humble/setup.bash
source ~/ROLLATOR/install/setup.bash

# 2. Launch full system
ros2 launch rollator_launch rollator.launch.py

# 3. In another terminal, check gait
ros2 topic echo /gait/metrics

# 4. To move: publish velocity commands
ros2 topic pub /cmd_vel geometry_msgs/Twist "
linear:
  x: 0.5
  y: 0.0
  z: 0.0
angular:
  x: 0.0
  y: 0.0
  z: 0.0"
```

## Common Commands

### Build and Install
```bash
cd ~/ROLLATOR
colcon build --symlink-install
source install/setup.bash
```

### Launch Options
```bash
# Full system
ros2 launch rollator_launch rollator.launch.py

# Sensor only
ros2 launch rollator_launch sensor_only.launch.py

# With custom parameters
ros2 launch rollator_launch rollator.launch.py \
    camera_index:=0 \
    motor_port:=/dev/ttyUSB0 \
    publish_rate:=15

# With debug output
RCUTILS_LOG_LEVEL=DEBUG ros2 launch rollator_launch rollator.launch.py
```

### Monitor Topics
```bash
# List all topics
ros2 topic list

# Monitor topic frequency
ros2 topic hz /camera/depth/points

# Echo topic messages
ros2 topic echo /gait/metrics

# Publish to topic (velocity command)
ros2 topic pub /cmd_vel geometry_msgs/Twist "{linear: {x: 0.5}}"

# Record rosbag
ros2 bag record -o myrecording /gait/metrics /motor_state

# Playback rosbag
ros2 bag play myrecording
```

### Parameter Management
```bash
# List all parameters
ros2 param list

# Get parameter value
ros2 param get /arducam_node camera_index

# Set parameter value
ros2 param set /motor_controller_node max_velocity 0.5

# Save parameters
ros2 param dump /arducam_node > params.yaml

# Load parameters
ros2 param load /arducam_node params.yaml
```

### Node Management
```bash
# List running nodes
ros2 node list

# Get node info
ros2 node info /arducam_node

# Show ROS graph
ros2 run rqt_graph rqt_graph

# Show node relationship
ros2 graph /arducam_node
```

### Debugging
```bash
# Fail startup diagnostics
ros2 doctor

# Check network connectivity
ros2 test connectivity

# Profile specific node
ros2 run ros2_tracing tracepoint_provider --nodes /arducam_node

# View system resources
ros2 run system_monitor monitor --duration 60
```

## Files Your Code Modifies

### Core Algorithm
- `rollator_sensor/arducam_driver.py` - Camera + 3D extraction
- `rollator_gait/gait_analyzer.py` - Gait recognition engine
- `rollator_motor/motor_driver.py` - Motor control logic

### Configuration
- `rollator_launch/config/camera_calibration.yaml`
- `rollator_launch/config/motor_config.yaml`

### Custom Messages
- `rollator_ros/msg/GaitMetrics.msg`

## Typical Workflow

### 1. Hardware Testing
```bash
# Test in isolation
ros2 run rollator_sensor arducam_node
# Open new terminal
ros2 topic echo /camera/rgb/image

# Test motor
ros2 run rollator_motor motor_controller_node
ros2 topic pub /cmd_vel geometry_msgs/Twist "{linear: {x: 0.3}}"
```

### 2. Gait Analysis Testing
```bash
# Test sensor + gait without motor
ros2 launch rollator_launch sensor_only.launch.py

# Monitor real-time metrics
ros2 topic hz /gait/metrics
ros2 topic echo /gait/stride_length
```

### 3. Full System Integration
```bash
# Run everything
ros2 launch rollator_launch rollator.launch.py

# Monitor in separate terminal
watch -n 1 'ros2 topic echo --once /gait/metrics'
```

### 4. Data Collection
```bash
# Record for analysis
ros2 bag record -o gait_data_001 /gait/metrics /camera/depth/points /motor_state

# Later: analyze
python3 analyze_gait.py gait_data_001
```

## ROS 2 Topic Map

```
camera/rgb/image ─→ [Gait Analyzer] ─→ gait/stride_length
camera/depth/image ─→                 gait/cadence
camera/depth/points │                 gait/symmetry
camera/camera_info │                 gait/stability
                    └─→ gait/metrics
                        gait/phase
                        gait/keypoints

cmd_vel ─→ [Motor Controller] ─→ motor_state
           (Twist)               motor_current
                                motor_temperature
```

## System Architecture

```
[Jetson Nano]
    |
    ├── [Arducam ToF] ──USB──→ [Sensor Driver]
    |                          (arducam_driver.py)
    |                          |
    |                          └──ROS→ [ROS Node]
    |                             (arducam_node.py)
    |
    ├── [Motor Controller] ──Serial→ [Motor Driver]
    |                                (motor_driver.py)
    |                                |
    |                                └──ROS→ [ROS Node]
    |                                   (motor_controller_node.py)
    |
    └── [Coordination Layer]
        [Gait Analyzer] (gait_analyzer_node.py)
        (subscribes to points, publishes metrics)
```

## Performance Tips

### For Development
```bash
# Faster builds (parallel workers)
colcon build --parallel-workers $(nproc)

# Skip installation step
colcon build --symlink-install

# Build only changed packages
colcon build --packages-select rollator_gait

# Verbose output
colcon build --event-handlers console_direct+
```

### For Runtime
```bash
# Lower publishing rates when testing
ros2 launch rollator_launch rollator.launch.py publish_rate:=10

# Only launch needed nodes
ros2 launch rollator_launch sensor_only.launch.py  # No motor

# Monitor performance
watch -n 1 'ros2 topic hz /gait/metrics'
```

## Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| "Camera not found" | Check `/dev/video*`, run `lsusb \| grep Arducam` |
| "Serial port not found" | Check `/dev/ttyUSB*`, verify baudrate (115200) |
| "Build fails" | Run `rosdep install -i --from-path src --rosdistro humble -y` |
| "ROS not sourced" | `source /opt/ros/humble/setup.bash` |
| "Permission denied /dev/ttyUSB0" | `sudo usermod -a -G dialout $USER` |
| "Out of memory" | Reduce `history_size` or publish_rate |
| "Gait metrics all zeros" | Check point cloud is publishing, verify min cluster size |

## File Reference

### Source Code
```
rollator_sensor/
  ├── arducam_driver.py ......... Pure camera logic
  └── arducam_node.py ........... ROS node wrapper

rollator_motor/
  ├── motor_driver.py ........... Pure motor logic
  └── motor_controller_node.py .. ROS node wrapper

rollator_gait/
  ├── gait_analyzer.py .......... Core algorithm
  └── gait_analyzer_node.py ..... ROS node wrapper

rollator_launch/
  ├── launch/ ................... Launch files
  ├── config/ ................... YAML configs
  └── rollator_orchestrator.py .. Coordinator
```

### Configuration
```
camera_calibration.yaml ....... Camera intrinsics, depth range
motor_config.yaml ............ Motor parameters, safety limits
```

## Calibration Guide

### Camera Calibration
```bash
# Using ROS 2 camera_calibration tool
ros2 run camera_calibration cameracalibrator \
    --size 8x6 --square 0.108 \
    image:=/camera/rgb/image \
    camera:=/camera

# Update camera_calibration.yaml with results
```

### Motor Calibration
```bash
# Measure your rollator
# Update motor_config.yaml:
# - track_width_mm: Distance between wheel centers
# - wheel_radius_mm: Radius of wheels
# - max_velocity: Maximum safe speed

# Test velocity output
ros2 run rollator_motor motor_controller_node
# Measure actual speed, adjust scaling
```

## Environment Variables

```bash
# Set ROS domain ID (for multi-robot)
export ROS_DOMAIN_ID=0

# Enable detailed logging
export RCUTILS_LOG_LEVEL=DEBUG

# Use Console output instead of file
export RCUTILS_LOGGING_USE_STDOUT=1

# Find ROS packages
export ROS_PACKAGE_PATH=~/ROLLATOR/install

# Use specific middleware
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

## Next Steps

1. **Calibrate your camera** - Run camera calibration for accuracy
2. **Test hardware** - Verify camera and motor independently
3. **Collect baseline data** - Record normal gait for reference
4. **Tune parameters** - Adjust config files for your rollator
5. **Deploy** - Set up systemd service for production

---

For detailed information, see README.md or JETSON_NANO_SETUP.md
