"""
Gait Recognition Engine - Pure Algorithm (Non-ROS)
Analyzes legs and thighs using 3D Cartesian coordinates
"""

import numpy as np
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass, field
from enum import Enum
from collections import deque


class GaitPhase(Enum):
    """Gait cycle phases."""

    STANCE = 1  # Foot on ground
    SWING = 2  # Foot in air
    LOADING_RESPONSE = 3  # Initial contact to foot flat
    TERMINAL_SWING = 4  # End of swing phase
    UNKNOWN = 0


@dataclass
class LegKeypoints:
    """3D coordinates for leg keypoints (in mm)."""

    hip: Optional[np.ndarray] = None  # Hip joint
    knee: Optional[np.ndarray] = None  # Knee joint
    ankle: Optional[np.ndarray] = None  # Ankle joint
    foot: Optional[np.ndarray] = None  # Foot/ground contact point
    confidence: float = 0.0  # Detection confidence (0-1)

    def is_valid(self) -> bool:
        """Check if all keypoints are detected."""
        return all(
            kp is not None for kp in [self.hip, self.knee, self.ankle, self.foot]
        )


@dataclass
class GaitMetrics:
    """Metrics computed from gait analysis."""

    stride_length_mm: float = 0.0  # Distance in mm
    cadence_steps_per_min: float = 0.0  # Steps per minute
    step_width_mm: float = 0.0  # Distance between feet
    knee_flexion_deg: float = 0.0  # Knee angle in degrees
    hip_flexion_deg: float = 0.0  # Hip angle in degrees
    gait_velocity_mm_s: float = 0.0  # Walking speed
    phase_left: GaitPhase = GaitPhase.UNKNOWN
    phase_right: GaitPhase = GaitPhase.UNKNOWN
    symmetry_index: float = 0.0  # Left-right symmetry (0-1)
    stability_index: float = 0.0  # Overall stability (0-1)


@dataclass
class GaitFrame:
    """Single frame of gait data."""

    timestamp_us: int  # Microseconds
    left_leg: LegKeypoints = field(default_factory=LegKeypoints)
    right_leg: LegKeypoints = field(default_factory=LegKeypoints)
    metrics: GaitMetrics = field(default_factory=GaitMetrics)


class GaitAnalyzer:
    """
    Pure gait recognition engine.
    Analyzes 3D leg motion and extracts biomechanical metrics.
    Focuses on legs and thighs only.
    """

    def __init__(self, history_size: int = 30, sampling_rate_hz: int = 30):
        """
        Initialize gait analyzer.

        Args:
            history_size: Number of frames to keep in history
            sampling_rate_hz: Camera sampling rate
        """
        self.history_size = history_size
        self.sampling_rate_hz = sampling_rate_hz
        self.frame_history: deque = deque(maxlen=history_size)

        # Gait cycle detection
        self.step_count_left = 0
        self.step_count_right = 0
        self.last_stance_time_left = 0
        self.last_stance_time_right = 0

    def process_frame(
        self,
        timestamp_us: int,
        left_hip: np.ndarray,
        left_knee: np.ndarray,
        left_ankle: np.ndarray,
        left_foot: np.ndarray,
        right_hip: np.ndarray,
        right_knee: np.ndarray,
        right_ankle: np.ndarray,
        right_foot: np.ndarray,
        left_conf: float = 1.0,
        right_conf: float = 1.0,
    ) -> GaitFrame:
        """
        Process a single frame of gait data.

        Args:
            timestamp_us: Frame timestamp in microseconds
            left_hip/knee/ankle/foot: 3D coordinates (mm) for left leg
            right_hip/knee/ankle/foot: 3D coordinates (mm) for right leg
            left_conf/right_conf: Detection confidence (0-1)

        Returns:
            GaitFrame with computed metrics
        """
        # Create leg keypoints
        left_leg = LegKeypoints(
            hip=left_hip,
            knee=left_knee,
            ankle=left_ankle,
            foot=left_foot,
            confidence=left_conf,
        )

        right_leg = LegKeypoints(
            hip=right_hip,
            knee=right_knee,
            ankle=right_ankle,
            foot=right_foot,
            confidence=right_conf,
        )

        # Compute metrics
        metrics = self._compute_metrics(left_leg, right_leg, timestamp_us)

        # Create frame
        frame = GaitFrame(
            timestamp_us=timestamp_us,
            left_leg=left_leg,
            right_leg=right_leg,
            metrics=metrics,
        )

        # Add to history
        self.frame_history.append(frame)

        return frame

    def _compute_metrics(
        self, left_leg: LegKeypoints, right_leg: LegKeypoints, timestamp_us: int
    ) -> GaitMetrics:
        """Compute gait metrics from leg keypoints."""
        metrics = GaitMetrics()

        if not left_leg.is_valid() or not right_leg.is_valid():
            return metrics

        # Compute joint angles
        left_knee_angle = self._compute_angle(
            left_leg.hip, left_leg.knee, left_leg.ankle
        )
        right_knee_angle = self._compute_angle(
            right_leg.hip, right_leg.knee, right_leg.ankle
        )

        left_hip_angle = self._compute_hip_angle(left_leg.hip, left_leg.knee)
        right_hip_angle = self._compute_hip_angle(right_leg.hip, right_leg.knee)

        metrics.knee_flexion_deg = (left_knee_angle + right_knee_angle) / 2.0
        metrics.hip_flexion_deg = (left_hip_angle + right_hip_angle) / 2.0

        # Compute stride metrics
        metrics.stride_length_mm = self._compute_stride_length(left_leg, right_leg)
        metrics.step_width_mm = abs(
            left_leg.foot[0] - right_leg.foot[0]
        )  # X distance between feet

        # Detect gait phases
        metrics.phase_left = self._detect_phase(left_leg)
        metrics.phase_right = self._detect_phase(right_leg)

        # Compute velocity
        if len(self.frame_history) > 1:
            prev_frame = self.frame_history[0]
            dt_s = (timestamp_us - prev_frame.timestamp_us) / 1e6

            if dt_s > 0:
                left_vel = np.linalg.norm(
                    left_leg.foot - prev_frame.left_leg.foot
                ) / (dt_s + 1e-6)
                right_vel = np.linalg.norm(
                    right_leg.foot - prev_frame.right_leg.foot
                ) / (dt_s + 1e-6)
                metrics.gait_velocity_mm_s = (left_vel + right_vel) / 2.0

        # Compute symmetry
        metrics.symmetry_index = self._compute_symmetry(left_leg, right_leg)

        # Compute stability
        metrics.stability_index = self._compute_stability()

        # Estimate cadence
        metrics.cadence_steps_per_min = self._estimate_cadence()

        return metrics

    def _compute_angle(self, p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> float:
        """
        Compute angle at p2 formed by p1-p2-p3.

        Args:
            p1, p2, p3: 3D points

        Returns:
            Angle in degrees
        """
        v1 = p1 - p2
        v2 = p3 - p2

        cos_angle = np.dot(v1, v2) / (
            np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6
        )
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle_rad = np.arccos(cos_angle)
        angle_deg = np.degrees(angle_rad)

        return angle_deg

    def _compute_hip_angle(self, hip: np.ndarray, knee: np.ndarray) -> float:
        """Compute hip flexion angle with vertical reference."""
        # Vector from hip to knee
        v = knee - hip

        # Vertical reference (negative Y is up in camera frame)
        vertical = np.array([0.0, -1.0, 0.0])

        cos_angle = np.dot(v, vertical) / (np.linalg.norm(v) + 1e-6)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        angle_rad = np.arccos(cos_angle)
        angle_deg = np.degrees(angle_rad)

        return angle_deg

    def _compute_stride_length(
        self, left_leg: LegKeypoints, right_leg: LegKeypoints
    ) -> float:
        """Compute stride length as distance between foot positions."""
        if len(self.frame_history) < 2:
            return 0.0

        # Find frames with left foot contact
        stride_distance = 0.0
        for i in range(len(self.frame_history) - 1):
            frame = self.frame_history[i]
            # Simplified: use horizontal distance between feet as proxy
            stride_distance = np.linalg.norm(
                left_leg.foot[:2] - right_leg.foot[:2]
            )

        return stride_distance * 2.0  # Approximate stride as 2x step length

    def _detect_phase(self, leg: LegKeypoints) -> GaitPhase:
        """
        Detect gait phase (stance or swing).

        Simple heuristic: if foot is low (close to ground plane), it's stance.
        """
        if leg.foot is None:
            return GaitPhase.UNKNOWN

        # Threshold for "ground contact" (Z > 50mm means foot is raised)
        ground_threshold_mm = 100.0

        if leg.foot[2] < ground_threshold_mm:
            return GaitPhase.STANCE
        else:
            return GaitPhase.SWING

    def _compute_symmetry(
        self, left_leg: LegKeypoints, right_leg: LegKeypoints
    ) -> float:
        """
        Compute left-right symmetry index (0-1).
        1.0 = perfect symmetry, 0.0 = no symmetry.
        """
        if not left_leg.is_valid() or not right_leg.is_valid():
            return 0.0

        # Compute segment lengths
        left_thigh = np.linalg.norm(left_leg.knee - left_leg.hip)
        right_thigh = np.linalg.norm(right_leg.knee - right_leg.hip)

        left_shank = np.linalg.norm(left_leg.ankle - left_leg.knee)
        right_shank = np.linalg.norm(right_leg.ankle - right_leg.knee)

        # Symmetry as ratio of asymmetry
        thigh_diff = abs(left_thigh - right_thigh) / (left_thigh + right_thigh + 1e-6)
        shank_diff = abs(left_shank - right_shank) / (left_shank + right_shank + 1e-6)

        symmetry = 1.0 - (thigh_diff + shank_diff) / 2.0
        return max(0.0, min(1.0, symmetry))

    def _compute_stability(self) -> float:
        """
        Compute stability index based on motion smoothness.
        Measures variance in joint positions.
        """
        if len(self.frame_history) < 3:
            return 0.5

        # Collect knee positions
        knee_positions = []
        for frame in self.frame_history:
            if frame.left_leg.knee is not None:
                knee_positions.append(frame.left_leg.knee)
            if frame.right_leg.knee is not None:
                knee_positions.append(frame.right_leg.knee)

        if len(knee_positions) < 3:
            return 0.5

        knee_positions = np.array(knee_positions)

        # Compute variance (lower variance = more stable)
        variance = np.var(knee_positions, axis=0).mean()

        # Normalize (threshold at 1000 mm²)
        stability = 1.0 - min(1.0, variance / 1000.0)

        return max(0.0, min(1.0, stability))

    def _estimate_cadence(self) -> float:
        """
        Estimate cadence from frame history.
        Count stance phase transitions.
        """
        if len(self.frame_history) < 2:
            return 0.0

        # Count phase transitions
        transitions = 0
        for i in range(1, len(self.frame_history)):
            prev_phase = self.frame_history[i - 1].metrics.phase_left
            curr_phase = self.frame_history[i].metrics.phase_left

            if prev_phase != curr_phase and curr_phase == GaitPhase.STANCE:
                transitions += 1

        # Estimate cadence (steps x 60 / time)
        if len(self.frame_history) > 1:
            time_s = (
                self.frame_history[-1].timestamp_us
                - self.frame_history[0].timestamp_us
            ) / 1e6
            if time_s > 0:
                cadence = (transitions * 60.0) / time_s
                return max(0.0, cadence)

        return 0.0

    def get_average_metrics(self) -> GaitMetrics:
        """Get average metrics over entire history."""
        if not self.frame_history:
            return GaitMetrics()

        metrics = GaitMetrics()

        stride_lengths = [f.metrics.stride_length_mm for f in self.frame_history]
        cadences = [f.metrics.cadence_steps_per_min for f in self.frame_history]
        step_widths = [f.metrics.step_width_mm for f in self.frame_history]
        symmetries = [f.metrics.symmetry_index for f in self.frame_history]

        if stride_lengths:
            metrics.stride_length_mm = np.mean([s for s in stride_lengths if s > 0])
        if cadences:
            metrics.cadence_steps_per_min = np.mean([c for c in cadences if c > 0])
        if step_widths:
            metrics.step_width_mm = np.mean([s for s in step_widths if s > 0])
        if symmetries:
            metrics.symmetry_index = np.mean(symmetries)

        return metrics
