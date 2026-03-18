#!/bin/bash
# Build script for Smart Rollator ROS 2 workspace

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Smart Rollator Build Script ===${NC}"

# Check if ROS 2 is sourced
if [ -z "$ROS_DISTRO" ]; then
    echo -e "${YELLOW}Sourcing ROS 2 Humble...${NC}"
    source /opt/ros/humble/setup.bash || {
        echo -e "${RED}Error: Could not source ROS 2 Humble setup${NC}"
        exit 1
    }
fi

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WORKSPACE_DIR="$SCRIPT_DIR"

echo -e "${YELLOW}Workspace: $WORKSPACE_DIR${NC}"
cd "$WORKSPACE_DIR"

# Install rosdep dependencies
echo -e "${YELLOW}Installing rosdep dependencies...${NC}"
rosdep install -i --from-path src --rosdistro humble -y || {
    echo -e "${YELLOW}Warning: Some rosdep packages may not be available${NC}"
}

# Clean previous build (optional)
if [ "$1" = "clean" ]; then
    echo -e "${YELLOW}Cleaning previous build...${NC}"
    rm -rf build install log
fi

# Build workspace
echo -e "${YELLOW}Building workspace...${NC}"
colcon build --symlink-install --parallel-workers 4

# Source install
echo -e "${GREEN}Build successful!${NC}"
echo -e "${YELLOW}Source this to use: source $WORKSPACE_DIR/install/setup.bash${NC}"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. Source the workspace: source install/setup.bash"
echo "2. Configure camera_calibration.yaml and motor_config.yaml"
echo "3. Launch: ros2 launch rollator_launch rollator.launch.py"
