#!/bin/bash
# Build script for Windows (PowerShell)

# This script is for building on Windows with WSL or native ROS setup

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$WORKSPACE_DIR = $SCRIPT_DIR

Write-Host "=== Smart Rollator Build Script (Windows) ===" -ForegroundColor Yellow

# Check if ROS 2 environment is set
if ($null -eq $env:ROS_DISTRO) {
    Write-Host "Sourcing ROS 2 Humble setup..." -ForegroundColor Yellow
    # Adjust path based on your ROS 2 installation
    & "C:\opt\ros\humble\setup.ps1" | Out-Null
}

Write-Host "Workspace: $WORKSPACE_DIR" -ForegroundColor Yellow
Set-Location $WORKSPACE_DIR

# Build workspace
Write-Host "Building workspace..." -ForegroundColor Yellow
colcon build --symlink-install --parallel-workers 4

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build successful!" -ForegroundColor Green
    Write-Host "Source this to use: .\install\setup.ps1" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Green
    Write-Host "1. Source the workspace: .\install\setup.ps1"
    Write-Host "2. Configure camera_calibration.yaml and motor_config.yaml"
    Write-Host "3. Launch: ros2 launch rollator_launch rollator.launch.py"
} else {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}
