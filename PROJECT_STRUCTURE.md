# Smart Rollator - Project Structure

Complete overview of all files and directories.

## Directory Tree

```
ROLLATOR/
│
├── README.md ........................ Main documentation
├── QUICK_REFERENCE.md .............. Common commands and tips
├── JETSON_NANO_SETUP.md ............ Jetson Nano installation guide
├── LICENSE .......................... MIT License
├── requirements.txt ................. Python dependencies
│
├── build.sh ......................... Linux build script
├── build.ps1 ....................... Windows build script
│
├── src/
│   └── rollator_ws/
│       │
│       ├── rollator_sensor/
│       │   ├── package.xml
│       │   ├── setup.py
│       │   ├── CMakeLists.txt (if using C++)
│       │   ├── resource/
│       │   │   └── rollator_sensor
│       │   └── rollator_sensor/
│       │       ├── __init__.py
│       │       ├── arducam_driver.py ........... Pure sensor logic
│       │       └── arducam_node.py ............ ROS wrapper node
│       │
│       ├── rollator_motor/
│       │   ├── package.xml
│       │   ├── setup.py
│       │   ├── resource/
│       │   │   └── rollator_motor
│       │   └── rollator_motor/
│       │       ├── __init__.py
│       │       ├── motor_driver.py ........... Pure motor logic
│       │       └── motor_controller_node.py .. ROS wrapper node
│       │
│       ├── rollator_gait/
│       │   ├── package.xml
│       │   ├── setup.py
│       │   ├── resource/
│       │   │   └── rollator_gait
│       │   └── rollator_gait/
│       │       ├── __init__.py
│       │       ├── gait_analyzer.py ......... Core algorithm
│       │       └── gait_analyzer_node.py .... ROS wrapper node
│       │
│       ├── rollator_ros/
│       │   ├── package.xml
│       │   ├── CMakeLists.txt
│       │   ├── msg/
│       │   │   └── GaitMetrics.msg ......... Custom message type
│       │   └── srv/
│       │       ├── ExecuteGait.srv ........ Custom service
│       │       └── CalibrateSensor.srv .... Custom service
│       │
│       └── rollator_launch/
│           ├── package.xml
│           ├── CMakeLists.txt
│           ├── launch/
│           │   ├── rollator.launch.py .... Main launch (all nodes)
│           │   └── sensor_only.launch.py . Sensor-only launch
│           ├── config/
│           │   ├── camera_calibration.yaml. Camera params
│           │   └── motor_config.yaml ..... Motor params
│           └── rollator_orchestrator.py .. System coordinator
│
├── build/ .......................... Build artifacts (auto-generated)
├── install/ ........................ Installed packages (auto-generated)
└── log/ ............................ Build logs (auto-generated)
```

## Module Descriptions

### rollator_sensor/
**Purpose**: Arducam ToF/Depth camera sensor driver
**Key Files**:
- `arducam_driver.py`: Pure Python driver (no ROS dependencies)
- `arducam_node.py`: ROS 2 node wrapper

**Publishes**:
- `/camera/rgb/image` - RGB video stream
- `/camera/depth/image` - Depth map
- `/camera/depth/points` - PointCloud2 (3D data)
- `/camera/camera_info` - Camera calibration

**Parameters**:
- `camera_index`: Camera device (default 0)
- `frame_width`: Resolution width (default 640)
- `frame_height`: Resolution height (default 480)
- `publish_rate`: Publishing frequency Hz (default 30)
- `frame_id`: TF frame identifier (default "camera_depth")

### rollator_motor/
**Purpose**: Motor controller interface and serial communication
**Key Files**:
- `motor_driver.py`: Pure motor control (no ROS dependencies)
- `motor_controller_node.py`: ROS 2 node wrapper

**Subscribes**:
- `/cmd_vel` - Twist messages for velocity commands

**Publishes**:
- `/motor_state` - Current velocities [left, right] m/s
- `/motor_current` - Motor currents [left, right] A
- `/motor_temperature` - Temperature °C

**Parameters**:
- `serial_port`: Motor controller port (default "/dev/ttyUSB0")
- `baudrate`: Serial baudrate (default 115200)
- `max_velocity`: Maximum velocity m/s (default 1.0)
- `publish_rate`: State update frequency Hz (default 10)

### rollator_gait/
**Purpose**: Gait recognition and biomechanical analysis
**Key Files**:
- `gait_analyzer.py`: Core algorithm (no ROS dependencies)
- `gait_analyzer_node.py`: ROS 2 node wrapper

**Subscribes**:
- `/camera/depth/points` - 3D point cloud from sensor

**Publishes**:
- `/gait/metrics` - All metrics as Float32MultiArray
- `/gait/stride_length` - Stride length (mm)
- `/gait/cadence` - Steps per minute
- `/gait/symmetry` - Symmetry index (0-1)
- `/gait/stability` - Stability index (0-1)
- `/gait/phase` - Current phase (STANCE/SWING)
- `/gait/keypoints` - 3D joint positions

**Parameters**:
- `history_size`: Frame history length (default 30)
- `sampling_rate`: Camera Hz (default 30)
- `legs_roi_top`: ROI top percentage (default 0.3)

### rollator_ros/
**Purpose**: ROS 2 custom messages and services
**Provides**:
- `GaitMetrics.msg` - Gait analysis message
- `ExecuteGait.srv` - Execute gait command
- `CalibrateSensor.srv` - Sensor calibration

### rollator_launch/
**Purpose**: Launch files and system configuration
**Contains**:
- `rollator.launch.py` - Full system launcher
- `sensor_only.launch.py` - Sensor-only launcher
- `camera_calibration.yaml` - Camera parameters
- `motor_config.yaml` - Motor parameters
- `rollator_orchestrator.py` - System coordinator node

## Build Artifacts (Auto-Generated)

### build/
Contains CMake build files for each package
- One subdirectory per package
- Contains cmake, lib, and source caches

### install/
Installed binaries and libraries
- `bin/` - Executable programs
- `lib/` - Shared libraries
- `share/` - Resource files (configs, launch)
- `setup.bash` - Environment setup script

### log/
Build and execution logs
- `build_YYYY-MM-DD-HH-MM-SS/` - Build logs
- `PACKAGE_build.log` - Individual package logs

## Configuration Files

### camera_calibration.yaml
Camera intrinsic and extrinsic parameters:
```yaml
camera:
  resolution: {width: 640, height: 480}
  intrinsics: {fx: 400, fy: 400, cx: 320, cy: 240}
  depth_range: {min: 100, max: 5000}
roi:
  legs_start_pct: 0.3
  margin_mm: 100
gait:
  history_size: 30
  ground_threshold_mm: 100
```

### motor_config.yaml
Motor controller parameters:
```yaml
motor:
  port: /dev/ttyUSB0
  baudrate: 115200
  max_velocity_m_s: 1.0
  track_width_mm: 400
  wheel_radius_mm: 50
```

## Message Types

### GaitMetrics.msg
Complete gait analysis results:
- `stride_length_mm` - Distance covered per cycle
- `cadence_steps_per_min` - Walking speed (frequency)
- `step_width_mm` - Distance between feet
- `knee_flexion_deg` - Knee angle
- `hip_flexion_deg` - Hip angle
- `gait_velocity_mm_s` - Walking speed (velocity)
- `symmetry_index` - Left-right symmetry (0-1)
- `stability_index` - Overall stability (0-1)
- `phase_left` - Left leg phase (STANCE/SWING)
- `phase_right` - Right leg phase (STANCE/SWING)

### ExecuteGait.srv
Command gait execution:
**Request**:
- `target_velocity_mm_s` - Desired speed
- `target_angle_deg` - Desired direction
- `duration_ms` - Command duration

**Response**:
- `success` - Command accepted
- `message` - Status message

### CalibrateSensor.srv
Trigger sensor calibration:
**Request**:
- `camera_index` - Camera to calibrate

**Response**:
- `success` - Calibration successful
- `calibration_data` - Calibration results

## Python Dependencies

Located in `requirements.txt`:
```
numpy>=1.21.0
opencv-python>=4.5.0
matplotlib>=3.4.0
pandas>=1.3.0
scipy>=1.7.0
```

## Build Scripts

### build.sh (Linux)
```bash
./build.sh          # Normal build
./build.sh clean    # Clean build
```

### build.ps1 (Windows PowerShell)
```powershell
.\build.ps1
```

Both scripts:
1. Check ROS 2 is sourced
2. Install rosdep dependencies
3. Run colcon build
4. Source install scripts

## Launch Files

### rollator.launch.py
Launches all system components:
- Arducam sensor node
- Motor controller node
- Gait analyzer node

**Parameters**:
- `camera_index=0` - Camera device
- `motor_port=/dev/ttyUSB0` - Motor port
- `publish_rate=30` - Publishing Hz

**Example**:
```bash
ros2 launch rollator_launch rollator.launch.py \
    camera_index:=0 \
    motor_port:=/dev/ttyUSB0 \
    publish_rate:=30
```

### sensor_only.launch.py
Launches sensor and gait analysis only (no motor control):
- Arducam sensor node
- Gait analyzer node

**Example**:
```bash
ros2 launch rollator_launch sensor_only.launch.py camera_index:=0
```

## Entry Points

Executable nodes defined in setup.py files:

### rollator_sensor
- `arducam_node` → `rollator_sensor.arducam_node:main`

### rollator_motor
- `motor_controller_node` → `rollator_motor.motor_controller_node:main`

### rollator_gait
- `gait_analyzer_node` → `rollator_gait.gait_analyzer_node:main`

## Module Dependencies

```
rollator_launch (top-level orchestrator)
    ├── depends on rollator_sensor
    ├── depends on rollator_motor
    ├── depends on rollator_gait
    └── depends on rollator_ros (custom messages)

rollator_sensor (independent)
    ├── depends on rclpy, sensor_msgs
    └── optionally uses OpenCV

rollator_motor (independent)
    ├── depends on rclpy, geometry_msgs
    └── optionally uses pyserial

rollator_gait (depends on data)
    ├── depends on rclpy, sensor_msgs
    ├── depends on numpy
    └── depends on rollator_ros (custom messages)

rollator_ros (defines interfaces)
    └── no dependencies (message/service definitions only)
```

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Jetson Nano (Linux)                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐                                           │
│  │ Arducam ToF  │ (USB)                                     │
│  └──────┬───────┘                                           │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────┐                                  │
│  │  arducam_driver.py   │ ◄─────── Pure driver logic       │
│  │  (no ROS deps)       │                                   │
│  └──────┬───────────────┘                                  │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────────────┐                                  │
│  │  arducam_node.py     │ ◄─────── ROS wrapper             │
│  │  (ROS 2 node)        │                                   │
│  └──────┬───────────────┘                                  │
│         │                                                    │
│         ├──→ /camera/rgb/image                             │
│         ├──→ /camera/depth/image                           │
│         ├──→ /camera/depth/points (PointCloud2)            │
│         └──→ /camera/camera_info                           │
│                                                              │
│         ┌──────────────────────────────────────────┐       │
│         │                                          │       │
│         ▼                    ┌─────────────────┐   │       │
│  ┌──────────────────────┐    │ gait_analyzer.py│   │       │
│  │ gait_analyzer_node.py│◄──│ (no ROS deps)   │◄──┘       │
│  │ (ROS 2 node)         │    └─────────────────┘           │
│  └──────┬───────────────┘                                  │
│         │                                                    │
│         ├──→ /gait/stride_length                           │
│         ├──→ /gait/cadence                                 │
│         ├──→ /gait/symmetry                                │
│         ├──→ /gait/stability                               │
│         ├──→ /gait/phase                                   │
│         └──→ /gait/keypoints                               │
│                                                              │
│  ┌────────────────────────┐                                │
│  │ rollator_orchestrator  │ ◄───────── Coordinator         │
│  │ (optional)             │                                 │
│  └────────┬───────────────┘                                │
│           │                                                  │
│           ▼                                                  │
│    /cmd_vel ──────────►                                    │
│                       │                                     │
│                       ▼                                     │
│  ┌──────────────────────────────────┐                      │
│  │  motor_controller_node.py        │                      │
│  │  (ROS 2 node)                    │                      │
│  └──────────────────┬───────────────┘                      │
│                     │                                       │
│                     ▼                                       │
│  ┌──────────────────────────────────┐                      │
│  │  motor_driver.py                 │ ◄────── Pure logic   │
│  │  (no ROS deps)                   │                      │
│  └──────────────────┬───────────────┘                      │
│                     │                                       │
│                     ▼                                       │
│  ┌──────────────────────────────────┐                      │
│  │  Motor Controller (Serial /dev/) │                      │
│  │  via USB                         │                      │
│  └──────────────────────────────────┘                      │
│                 │                                           │
│                 ▼                                           │
│          [Left Motor]  [Right Motor]                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Development Workflow

1. **Edit Pure Drivers** - Modify `*_driver.py` files
2. **Test Locally** - Write standalone tests
3. **Wrap with ROS** - Modify `*_node.py` files
4. **Build** - `colcon build --packages-select <package>`
5. **Test ROS** - Launch individual nodes
6. **Integrate** - Use launch files to combine
7. **Deploy** - Move to Jetson Nano

## Next Steps

1. Review the README.md for detailed documentation
2. Check QUICK_REFERENCE.md for common commands
3. Follow JETSON_NANO_SETUP.md for hardware setup
4. Configure camera_calibration.yaml and motor_config.yaml
5. Run `./build.sh` to compile everything
6. Test with `ros2 launch rollator_launch sensor_only.launch.py`

---

**Project Status**: Complete - All modules implemented and integrated
**Last Updated**: March 2026
