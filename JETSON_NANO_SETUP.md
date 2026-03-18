# Smart Rollator - Jetson Nano Setup Guide

This guide provides step-by-step instructions for setting up the Smart Rollator on NVIDIA Jetson Nano with ROS 2 Humble.

## Prerequisites

- NVIDIA Jetson Nano with Ubuntu 22.04 LTS (or Jetson OS with Ubuntu 22.04 container)
- 16GB microSD card (minimum)
- Arducam ToF/Depth camera
- Motor controller via USB
- Power supply suitable for Jetson Nano + motors

## Step 1: Jetson Nano Initial Setup

### 1.1 Flash Operating System

Visit https://developer.nvidia.com/jetson-nano-developer-kit and download:
- JetPack 5.1.1 (supports Ubuntu 22.04)
- Use Balena Etcher to flash to microSD

### 1.2 First Boot

```bash
# Boot Jetson Nano and complete initial setup
# Create user account and set hostname
# Example hostname: rollator-jetson

# SSH into device
ssh rollator@rollator-jetson.local
```

### 1.3 Basic System Setup

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install build essentials
sudo apt install -y \
    build-essential \
    cmake \
    git \
    nano \
    htop \
    wget \
    curl

# Check CUDA is installed
nvcc --version  # Should show CUDA 11.x
```

## Step 2: Install ROS 2 Humble on Jetson Nano

### 2.1 Add ROS 2 Repository

```bash
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
```

### 2.2 Install ROS 2 Desktop

```bash
sudo apt install -y ros-humble-desktop

# Note: This may take 30-60 minutes on Jetson Nano due to limited resources
# Consider using desktop-minimum if space is constrained:
# sudo apt install -y ros-humble-desktop-minimal
```

### 2.3 Post-Installation

```bash
# Source ROS 2
source /opt/ros/humble/setup.bash

# Add to bashrc for automatic sourcing
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc

# Verify ROS 2
ros2 --version
```

## Step 3: Install Development Tools

```bash
# ROS 2 build tools
sudo apt install -y \
    python3-colcon-common-extensions \
    python3-rosdep \
    ros-humble-rmw-cyclonedds-cpp

# Python development
sudo apt install -y \
    python3-dev \
    python3-pip \
    python3-venv

# Install pip packages
pip install --upgrade pip
pip install numpy opencv-python opencv-contrib-python
```

## Step 4: Install Camera Dependencies

### 4.1 Arducam Setup

```bash
# Install camera libraries
sudo apt install -y \
    libopencv-dev \
    python3-opencv

# For Arducam specific setup:
cd ~/
git clone https://github.com/ArduCam/sample-code.git
cd sample-code

# Follow Arducam documentation for your specific camera model
# https://www.arducam.com/docs/

# Test camera connection
python3 -c "import cv2; cap = cv2.VideoCapture(0); print(cap.read())"
```

## Step 5: Clone Smart Rollator Project

```bash
# Clone to home directory
cd ~/
git clone <your-repo-url> ROLLATOR
# Or if using local copy, copy to ~/ROLLATOR

cd ~/ROLLATOR

# Verify structure
ls -la src/rollator_ws/
```

## Step 6: Build Smart Rollator Workspace

### 6.1 Install Dependencies

```bash
cd ~/ROLLATOR

# Initialize rosdep
sudo rosdep init
rosdep update

# Install dependencies
rosdep install -i --from-path src --rosdistro humble -y
```

### 6.2 Build

```bash
cd ~/ROLLATOR

# Make build script executable
chmod +x build.sh

# Build (this may take 10-20 minutes on Jetson Nano)
./build.sh

# Or manually:
source /opt/ros/humble/setup.bash
colcon build --symlink-install --parallel-workers 2
```

### 6.3 Source Install

```bash
# Add to bashrc
echo "source ~/ROLLATOR/install/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

## Step 7: Configure Hardware

### 7.1 Configure Camera

```bash
# Edit camera calibration
nano ~/ROLLATOR/src/rollator_ws/rollator_launch/config/camera_calibration.yaml

# Key parameters to update:
# - resolution: Match your camera (typically 640x480)
# - intrinsics: Run calibration or use Arducam specs
# - depth_range: Adjust as needed
```

### 7.2 Configure Motor Controller

```bash
# Identify serial port
ls /dev/ttyUSB*
# Should show /dev/ttyUSB0 or similar

# Edit motor config
nano ~/ROLLATOR/src/rollator_ws/rollator_launch/config/motor_config.yaml

# Key parameters:
# - port: /dev/ttyUSB0 (or your device)
# - baudrate: 115200 (adjust if needed)
# - track_width_mm: Measure your rollator
# - wheel_radius_mm: Measure your wheels
```

### 7.3 Test Hardware

```bash
# Test camera
python3 << 'EOF'
import cv2
import numpy as np

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Camera not found!")
else:
    ret, frame = cap.read()
    print(f"Camera OK! Frame shape: {frame.shape}")
    cap.release()
EOF

# Test serial port
python3 << 'EOF'
import serial
try:
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
    print(f"Serial port OK!")
    ser.close()
except Exception as e:
    print(f"Serial error: {e}")
EOF
```

## Step 8: First Run

### 8.1 Sensor-Only Test

```bash
# Start sensor and gait analysis (no motor control)
ros2 launch rollator_launch sensor_only.launch.py

# In another terminal, monitor topics:
# Terminal 2:
source ~/.bashrc
ros2 topic echo /camera/depth/points
ros2 topic echo /gait/metrics
```

### 8.2 Full System Test

```bash
# Start all nodes
ros2 launch rollator_launch rollator.launch.py \
    camera_index:=0 \
    motor_port:=/dev/ttyUSB0 \
    publish_rate:=30

# Monitor individual topics
ros2 topic echo /gait/stride_length
ros2 topic echo /motor_state
```

### 8.3 Manual Motor Test

```bash
# Create a test script
python3 << 'EOF'
import rclpy
from geometry_msgs.msg import Twist
import time

rclpy.init()
node = rclpy.create_node('motor_test')
pub = node.create_publisher(Twist, 'cmd_vel', 10)

# Test forward
msg = Twist()
msg.linear.x = 0.3
pub.publish(msg)
time.sleep(2)

# Test stop
msg.linear.x = 0.0
pub.publish(msg)

rclpy.shutdown()
EOF
```

## Step 9: Performance Tuning

### 9.1 Monitor Resources

```bash
# Check CPU/GPU usage
htop

# Monitor ROS 2 timing
ros2 topic hz /camera/depth/points
ros2 topic hz /gait/metrics

# Check disk space
df -h
df -h /dev/shm  # Shared memory (important for ROS)
```

### 9.2 Optimize for Jetson Nano

```bash
# Reduce camera resolution if needed
# Edit camera_calibration.yaml:
# resolution:
#   width: 320
#   height: 240

# Reduce publishing rate
ros2 launch rollator_launch rollator.launch.py publish_rate:=15

# Enable GPU acceleration (if available)
export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libgomp.so.1

# Monitor memory
free -h
```

### 9.3 Reduce Power Consumption

```bash
# Set CPU governor
sudo su -
echo 'powersave' | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Enable 5W mode (manual power configuration)
sudo nvpmodel -m 1  # 5W mode
# or
sudo nvpmodel -m 0  # Maximum performance (15W)

# View current mode
sudo nvpmodel -q verbose
```

## Step 10: Deployment

### 10.1 Create Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/rollator.service
```

Add:
```ini
[Unit]
Description=Smart Rollator ROS 2 System
After=network.target

[Service]
Type=simple
User=rollator
WorkingDirectory=/home/rollator
Environment="PATH=/home/rollator/ROLLATOR/install/bin:/opt/ros/humble/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="LD_LIBRARY_PATH=/home/rollator/ROLLATOR/install/lib:/opt/ros/humble/lib:/usr/lib/aarch64-linux-gnu"
Environment="ROS_DOMAIN_ID=0"
ExecStart=/opt/ros/humble/bin/ros2 launch rollator_launch rollator.launch.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable rollator
sudo systemctl start rollator

# Check status
sudo systemctl status rollator

# View logs
sudo journalctl -u rollator -f
```

### 10.2 SSH Remote Monitoring

```bash
# From another machine on same network
ssh rollator@rollator-jetson.local

# Monitor system
ros2 topic echo /gait/metrics
ros2 topic echo /motor_state
```

## Troubleshooting on Jetson Nano

### Out of Memory
```bash
# Jetson Nano has limited RAM (4GB typical)
# Solution: Reduce buffer sizes or use swap
sudo swapon --show  # Check swap
```

### Slow Build
```bash
# Use parallel workers
# Edit build.sh or run:
colcon build --symlink-install --parallel-workers 2
```

### Camera Permission Denied
```bash
# Add user to video group
sudo usermod -a -G video $USER
newgrp video
# Logout and login again
```

### Serial Port Permission Denied
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER
newgrp dialout
```

### CUDA Not Available to Python
```bash
# Verify CUDA is installed for Python
python3 -c "import torch; print(torch.cuda.is_available())"

# If not available, rebuild packages with CUDA support
```

## Maintenance

### Regular Updates
```bash
# Update ROS 2
sudo apt update
sudo apt upgrade ros-humble-* -y

# Update project
cd ~/ROLLATOR
git pull origin main
colcon build --symlink-install
```

### Backup Configuration
```bash
# Backup calibration settings
cp ~/ROLLATOR/src/rollator_ws/rollator_launch/config/*.yaml ~/backups/

# Backup system configuration
sudo cp -r /etc/systemd/system/rollator.service ~/backups/
```

## Performance Benchmarks

Expected performance on Jetson Nano:

| Metric | Value |
|--------|-------|
| Camera FPS | 30 Hz |
| Gait Update Rate | 30 Hz |
| Motor Update Rate | 10 Hz |
| CPU Usage | 60-80% |
| Memory Usage | 1.5-2.0 GB |
| Latency (sensor to motor) | ~100-200 ms |

## Next Steps

1. Calibrate camera using ROS 2 camera_calibration tool
2. Tune motor parameters based on physical rollator
3. Collect gait data for analysis
4. Implement additional features (UI, logging, etc.)

## Additional Resources

- NVIDIA Jetson Nano: https://developer.nvidia.com/jetson-nano
- ROS 2 Humble: https://docs.ros.org/en/humble/
- Arducam Documentation: https://www.arducam.com/docs/
- JetPack 5.1: https://developer.nvidia.com/jetpack

---

For issues or questions, refer to the main README.md or create an issue in the project repository.
