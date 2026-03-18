# Smart Rollator Project - Complete ROS 2 Implementation

This is a complete ROS 2 Humble implementation of a Smart Rollator (robotic mobility aid) with gait recognition.

## Project Structure

```
ROLLATOR/
├── src/
│   └── rollator_ws/
│       ├── rollator_sensor/          # Arducam depth camera driver
│       ├── rollator_ros/             # ROS 2 interfaces (msgs, srvs)
│       ├── rollator_motor/           # Motor controller
│       ├── rollator_gait/            # Gait recognition engine
│       └── rollator_launch/          # Launch files and configs
├── build/                            # Build artifacts (auto-generated)
├── install/                          # Installed packages (auto-generated)
└── log/                              # Build logs (auto-generated)
```

## Architecture Overview

The project follows a strict modular architecture:

### 1. **Sensor Module** (`rollator_sensor`)
- **Pure Driver**: `arducam_driver.py` - No ROS dependencies
  - Raw camera operations
  - 3D coordinate extraction from depth maps
  - Depth filtering and ground plane detection
- **ROS Node**: `arducam_node.py` - ROS wrapper
  - Publishes RGB images, depth maps, and point clouds

### 2. **Motor Control Module** (`rollator_motor`)
- **Pure Driver**: `motor_driver.py` - No ROS dependencies
  - Differential drive motor control
  - Serial communication with motor controller
  - Velocity commands and state reading
- **ROS Node**: `motor_controller_node.py` - ROS wrapper
  - Subscribes to `cmd_vel` (Twist messages)
  - Publishes motor state and current readings

### 3. **Gait Recognition Module** (`rollator_gait`)
- **Pure Engine**: `gait_analyzer.py` - No ROS dependencies
  - 3D coordinate processing (X, Y, Z in mm)
  - Leg keypoint detection (hip, knee, ankle, foot)
  - Gait phase detection (stance vs swing)
  - Biomechanical metrics calculation:
    - Stride length, cadence, step width
    - Joint angles (knee, hip flexion)
    - Symmetry and stability indices
- **ROS Node**: `gait_analyzer_node.py` - ROS wrapper
  - Subscribes to point cloud data
  - Publishes gait metrics and keypoints

### 4. **ROS Communication** (`rollator_ros`)
- Custom message types:
  - `GaitMetrics.msg` - Gait analysis results
- Service definitions:
  - `ExecuteGait.srv` - Execute gait patterns
  - `CalibrateSensor.srv` - Sensor calibration

### 5. **Launch System** (`rollator_launch`)
- Main launch file: `rollator.launch.py` - All nodes
- Sensor-only launch: `sensor_only.launch.py` - For testing

## Dependencies

### System Requirements
- **OS**: Ubuntu 22.04 LTS (or compatible)
- **ROS**: ROS 2 Humble (Kitte Kaiju)
- **Hardware**: Jetson Nano, Arducam ToF/Depth camera, Motor controller
- **Python**: 3.10+

### Required Packages

```bash
# ROS 2 core
sudo apt install ros-humble-desktop
sudo apt install ros-humble-dev-tools

# Build tools
sudo apt install build-essential python3-colcon-common-extensions

# Additional dependencies
pip install numpy opencv-python cv-bridge
sudo apt install ros-humble-cv-bridge
```

## Installation

### 1. Clone or Extract Project

```bash
# The project is already in your workspace
cd ~/Desktop/ROLLATOR
```

### 2. Install Dependencies

```bash
cd ~/Desktop/ROLLATOR

# Install ROS 2 and build tools
sudo apt update
sudo apt install -y \
    ros-humble-desktop \
    build-essential \
    cmake \
    git \
    python3-colcon-common-extensions \
    python3-rosdep

# Install Python dependencies
pip install numpy opencv-python

# Install ROS 2 development tools
sudo apt install -y ros-humble-dev-tools
```

### 3. Build Project

```bash
cd ~/Desktop/ROLLATOR

# Source ROS 2 setup
source /opt/ros/humble/setup.bash

# Install dependencies using rosdep
rosdep install -i --from-path src --rosdistro humble -y

# Build workspace
colcon build --symlink-install

# Source install
source install/setup.bash
```

## Running the System

### Option 1: Full System (All Nodes)

```bash
source ~/Desktop/ROLLATOR/install/setup.bash
ros2 launch rollator_launch rollator.launch.py
```

**Parameters**:
```bash
# Specify camera index
ros2 launch rollator_launch rollator.launch.py camera_index:=0

# Specify motor port
ros2 launch rollator_launch rollator.launch.py motor_port:=/dev/ttyUSB0

# Specify publish rate
ros2 launch rollator_launch rollator.launch.py publish_rate:=30
```

### Option 2: Sensor and Gait Analysis Only

```bash
source ~/Desktop/ROLLATOR/install/setup.bash
ros2 launch rollator_launch sensor_only.launch.py
```

### Option 3: Individual Nodes

```bash
source ~/Desktop/ROLLATOR/install/setup.bash

# Terminal 1: Sensor node
ros2 run rollator_sensor arducam_node

# Terminal 2: Motor controller node
ros2 run rollator_motor motor_controller_node

# Terminal 3: Gait analyzer node
ros2 run rollator_gait gait_analyzer_node
```

## ROS 2 Topics and Services

### Published Topics

#### From Sensor (`arducam_node`)
- `camera/rgb/image` (sensor_msgs/Image) - RGB video stream
- `camera/depth/image` (sensor_msgs/Image) - Depth map
- `camera/depth/points` (sensor_msgs/PointCloud2) - 3D point cloud
- `camera/camera_info` (sensor_msgs/CameraInfo) - Camera calibration

#### From Motor Controller (`motor_controller_node`)
- `motor_state` (std_msgs/Float32MultiArray) - [left_vel, right_vel] m/s
- `motor_current` (std_msgs/Float32MultiArray) - [left_current, right_current] A
- `motor_temperature` (std_msgs/Float32) - Temperature °C

#### From Gait Analyzer (`gait_analyzer_node`)
- `gait/metrics` (std_msgs/Float32MultiArray) - All metrics [stride, cadence, ...]
- `gait/stride_length` (std_msgs/Float32) - Stride length mm
- `gait/cadence` (std_msgs/Float32) - Steps per minute
- `gait/symmetry` (std_msgs/Float32) - Symmetry index (0-1)
- `gait/stability` (std_msgs/Float32) - Stability index (0-1)
- `gait/phase` (std_msgs/String) - Gait phase (STANCE/SWING)
- `gait/keypoints` (std_msgs/Float32MultiArray) - 3D keypoints

### Subscribed Topics

#### By Motor Controller (`motor_controller_node`)
- `cmd_vel` (geometry_msgs/Twist) - Velocity commands

#### By Gait Analyzer (`gait_analyzer_node`)
- `camera/depth/points` (sensor_msgs/PointCloud2) - From sensor

## Gait Metrics Explanation

The gait analyzer computes the following metrics:

| Metric | Unit | Description |
|--------|------|-------------|
| Stride Length | mm | Distance covered in one full gait cycle |
| Cadence | steps/min | Number of steps per minute |
| Step Width | mm | Distance between left and right foot |
| Knee Flexion | degrees | Maximum knee angle during swing |
| Hip Flexion | degrees | Hip angle relative to vertical |
| Gait Velocity | mm/s | Walking speed |
| Symmetry Index | 0-1 | Left-right symmetry (1 = perfect) |
| Stability Index | 0-1 | Overall gait smoothness |

## Configuration Files

Located in `rollator_launch/config/`:

1. **camera_calibration.yaml**
   - Camera intrinsic parameters
   - Depth range settings
   - ROI parameters for leg detection

2. **motor_config.yaml**
   - Motor port and baudrate
   - Velocity limits and scaling
   - Safety thresholds

## Hardware Setup

### Jetson Nano Setup
```bash
# SSH into Jetson Nano
ssh jetson@<jetson-ip>

# Install ROS 2 Humble (ARM64)
# Follow: https://docs.ros.org/en/humble/Installation.html

# Install OpenCV with CUDA support for performance
# Install torch/torchhvision for optional ML features
```

### Camera Connection (Arducam ToF)
- Connect via USB to Jetson Nano
- Verify connection: `ls /dev/video*`
- Note the device index (usually `/dev/video0`)

### Motor Controller Connection
- Connect via USB-to-Serial adapter
- Verify connection: `ls /dev/ttyUSB*`
- Update `motor_config.yaml` with correct port

## Testing and Debugging

### Monitor ROS 2 Graph
```bash
ros2 run rqt_graph rqt_graph
```

### Echo Topics
```bash
# Watch gait metrics
ros2 topic echo /gait/metrics

# Watch motor state
ros2 topic echo /motor_state

# Watch point cloud
ros2 topic echo /camera/depth/points
```

### Launch with Debug Output
```bash
# Verbose logging
export RCUTILS_LOGGING_USE_STDOUT=1
export RCUTILS_LOG_LEVEL=DEBUG
ros2 launch rollator_launch rollator.launch.py
```

### List All Parameters
```bash
ros2 param list
```

### Get/Set Parameters
```bash
ros2 param get /arducam_node camera_index
ros2 param set /motor_controller_node max_velocity 0.5
```

## Performance Optimization

### For Jetson Nano (Limited Resources)

1. **Reduce Point Cloud Resolution**
   - Edit `camera_calibration.yaml`: decrease resolution
   - Example: 320x240 instead of 640x480

2. **Reduce Publishing Rate**
   ```bash
   ros2 launch rollator_launch rollator.launch.py publish_rate:=15
   ```

3. **Enable CUDA Acceleration**
   - Compile OpenCV with CUDA support
   - Use GPU-accelerated depth processing

4. **Profile Performance**
   ```bash
   # CPU usage
   ros2 topic hz /camera/depth/points
   top -p $(pgrep -f arducam_node)
   ```

## Advanced Usage

### Custom Gait Patterns

The motor controller supports arbitrary velocity commands:

```python
# Example: Forward with left turn
from geometry_msgs.msg import Twist
import rclpy

node = rclpy.create_node('example')
pub = node.create_publisher(Twist, 'cmd_vel', 10)

msg = Twist()
msg.linear.x = 0.5  # m/s forward
msg.angular.z = 0.2  # rad/s turn left
pub.publish(msg)
```

### Sensor Calibration

To calibrate the camera:

```bash
# Use ROS 2 camera_calibration tool
ros2 run camera_calibration cameracalibrator --size 8x6 --square 0.108 image:=/camera/rgb/image camera:=/camera
```

Update the intrinsic parameters in `camera_calibration.yaml`.

## Troubleshooting

### Camera Not Detected
```bash
# Check USB devices
lsusb | grep -i arducam

# Check video devices
ls /dev/video*

# Test with OpenCV
python3 -c "import cv2; cap = cv2.VideoCapture(0); print(cap.read())"
```

### Motor Controller Not Responding
```bash
# Check serial port
ls /dev/ttyUSB*

# Test serial connection
minicom -D /dev/ttyUSB0 -b 115200
```

### ROS 2 Build Errors
```bash
# Clean build
cd ~/Desktop/ROLLATOR
rm -rf build install log
colcon build --symlink-install

# Check for missing dependencies
rosdep install -i --from-path src --rosdistro humble -y
```

## File Structure

See directory tree at top of this document.

Key files:
- `rollator_sensor/rollator_sensor/arducam_driver.py` - Core camera driver
- `rollator_motor/rollator_motor/motor_driver.py` - Core motor control
- `rollator_gait/rollator_gait/gait_analyzer.py` - Gait recognition engine
- `rollator_launch/launch/rollator.launch.py` - Main launcher

## Future Enhancements

- [ ] Add ML-based pose estimation
- [ ] Implement trajectory prediction
- [ ] Add force feedback control
- [ ] Real-time 3D visualization (RViz)
- [ ] Cloud-based data logging and analysis
- [ ] Mobile app for remote monitoring
- [ ] Battery management system
- [ ] Emergency stop safety logic

## Contributing

To add new features:

1. Keep modules separated by function
2. Never mix sensor/motor/gait logic with ROS code
3. Write pure Python drivers, wrap with ROS nodes
4. Test individually before integration
5. Update this README

## License

MIT License - See LICENSE file

## Contact

Smart Rollator Team
developer@rollator.local

## References

- ROS 2 Documentation: https://docs.ros.org/en/humble/
- Gait Analysis: https://en.wikipedia.org/wiki/Gait_analysis
- Jetson Nano: https://developer.nvidia.com/jetson-nano
- Arducam: https://www.arducam.com/

---

**Last Updated**: March 2026
**Status**: Fully Implemented - Ready for Integration Testing
