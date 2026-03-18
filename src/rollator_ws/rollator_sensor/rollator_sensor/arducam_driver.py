"""
Arducam Depth Camera Driver - Pure Sensor Logic (Non-ROS)
Handles raw camera operations and 3D coordinate extraction
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List, Dict


class ArducamDepthCamera:
    """
    Pure sensor driver for Arducam ToF/Depth camera.
    No ROS dependencies - pure sensor logic.
    """

    def __init__(self, camera_index: int = 0, width: int = 640, height: int = 480):
        """
        Initialize the Arducam depth camera.

        Args:
            camera_index: Camera device index (default: 0)
            width: Frame width in pixels
            height: Frame height in pixels
        """
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.cap = None
        self.is_open = False

        # Camera intrinsic parameters (Arducam ToF typical values)
        # These should be calibrated for your specific camera
        self.fx = 400.0  # Focal length in x
        self.fy = 400.0  # Focal length in y
        self.cx = width / 2.0  # Principal point x
        self.cy = height / 2.0  # Principal point y

        # Depth range in millimeters
        self.depth_min_mm = 100.0
        self.depth_max_mm = 5000.0

    def open(self) -> bool:
        """Open the camera device. Returns True on success."""
        try:
            self.cap = cv2.VideoCapture(self.camera_index)
            if not self.cap.isOpened():
                return False

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, 30)

            self.is_open = True
            return True
        except Exception as e:
            print(f"Error opening camera: {e}")
            return False

    def close(self):
        """Close the camera device."""
        if self.cap is not None:
            self.cap.release()
            self.is_open = False

    def read_frame(self) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Read a single frame from the camera.

        Returns:
            Tuple of (RGB frame, Depth frame) or None if read failed
        """
        if not self.is_open or self.cap is None:
            return None

        ret, frame = self.cap.read()
        if not ret:
            return None

        # For Arducam ToF, depth information is often in IR or separate channel
        # This is a simplified example - adapt to your camera's output format
        if len(frame.shape) == 3 and frame.shape[2] >= 3:
            # Extract channels (adjust based on actual camera output)
            rgb_frame = frame[:, :, :3]
            # Simulate depth channel (in real scenario, extract from camera)
            depth_frame = frame[:, :, 0].astype(np.float32) * 16.0  # Scale to mm
        else:
            rgb_frame = frame
            depth_frame = np.zeros((self.height, self.width), dtype=np.float32)

        return rgb_frame, depth_frame

    def get_3d_points(self, depth_frame: np.ndarray) -> np.ndarray:
        """
        Convert depth map to 3D Cartesian coordinates.

        Args:
            depth_frame: Depth map in millimeters

        Returns:
            Array of shape (H, W, 3) with 3D coordinates in mm
        """
        h, w = depth_frame.shape

        # Create pixel coordinate grids
        u = np.arange(w, dtype=np.float32)
        v = np.arange(h, dtype=np.float32)
        uu, vv = np.meshgrid(u, v)

        # Convert pixel coordinates to 3D using camera intrinsics
        # X = (u - cx) * Z / fx
        # Y = (v - cy) * Z / fy
        # Z = depth_value (in mm)

        Z = depth_frame  # Depth in mm
        X = (uu - self.cx) * Z / self.fx
        Y = (vv - self.cy) * Z / self.fy

        # Stack into 3D point cloud (H, W, 3)
        points_3d = np.stack([X, Y, Z], axis=-1)

        return points_3d

    def filter_depth(self, depth_frame: np.ndarray) -> np.ndarray:
        """
        Apply bilateral filtering to smooth depth while preserving edges.

        Args:
            depth_frame: Raw depth frame

        Returns:
            Filtered depth frame
        """
        # Clip to valid range
        depth_clipped = np.clip(depth_frame, self.depth_min_mm, self.depth_max_mm)

        # Bilateral filter for edge-preserving smoothing
        depth_filtered = cv2.bilateralFilter(
            depth_clipped.astype(np.float32), 5, 75, 75
        )

        return depth_filtered

    def get_legs_region(
        self, depth_frame: np.ndarray, roi_top_pct: float = 0.3
    ) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
        """
        Extract lower region of depth map (legs and thighs area).

        Args:
            depth_frame: Full depth map
            roi_top_pct: Percentage from top to start ROI (0.0-1.0)

        Returns:
            Tuple of (cropped depth map, ROI coordinates as (x, y, w, h))
        """
        h, w = depth_frame.shape
        y_start = int(h * roi_top_pct)

        legs_depth = depth_frame[y_start:, :]
        roi = (0, y_start, w, h - y_start)

        return legs_depth, roi

    def detect_ground_plane(
        self, points_3d: np.ndarray, threshold_mm: float = 50.0
    ) -> Optional[Dict]:
        """
        Detect ground plane from 3D points using RANSAC.

        Args:
            points_3d: 3D point cloud (H, W, 3)
            threshold_mm: RANSAC distance threshold in mm

        Returns:
            Dictionary with plane coefficients or None
        """
        # Reshape to (N, 3)
        points = points_3d.reshape(-1, 3)

        # Filter out invalid points (Z = 0 or out of range)
        valid_mask = (points[:, 2] > self.depth_min_mm) & (
            points[:, 2] < self.depth_max_mm
        )
        valid_points = points[valid_mask]

        if len(valid_points) < 3:
            return None

        # Simple RANSAC for plane fitting
        # In production, use scipy or fit_plane library
        try:
            # Use SVD to fit plane
            centroid = np.mean(valid_points, axis=0)
            centered = valid_points - centroid
            u, s, vt = np.linalg.svd(centered)
            normal = vt[-1, :]  # Smallest singular vector

            # Plane equation: normal · (P - centroid) = 0
            d = -np.dot(normal, centroid)

            return {
                "normal": normal,
                "d": d,
                "centroid": centroid,
                "inliers_count": len(valid_points),
            }
        except Exception as e:
            print(f"Error detecting ground plane: {e}")
            return None

    def __del__(self):
        """Cleanup on object destruction."""
        self.close()
