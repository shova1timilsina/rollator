"""
Motor Controller Driver - Pure Motor Control Logic (Non-ROS)
Handles motor commands and velocity control
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class MotorCommand:
    """Represents a motor command."""

    left_velocity: float  # m/s or RPM
    right_velocity: float  # m/s or RPM
    duration: float = 0.0  # seconds (0 = indefinite)


@dataclass
class MotorState:
    """Represents the current motor state."""

    left_velocity: float
    right_velocity: float
    left_current: float  # Amperes
    right_current: float  # Amperes
    temperature: float  # Celsius
    is_moving: bool


class MotorController:
    """
    Pure motor controller driver for Smart Rollator.
    No ROS dependencies - pure motor control logic.
    Supports differential drive with left/right motors.
    """

    def __init__(
        self,
        port: str = "/dev/ttyUSB0",
        baudrate: int = 115200,
        max_velocity: float = 1.0,
    ):
        """
        Initialize motor controller.

        Args:
            port: Serial port for motor controller (e.g., /dev/ttyUSB0)
            baudrate: Serial communication baudrate
            max_velocity: Maximum velocity in m/s
        """
        self.port = port
        self.baudrate = baudrate
        self.max_velocity = max_velocity

        # Motor state
        self.current_state = MotorState(
            left_velocity=0.0,
            right_velocity=0.0,
            left_current=0.0,
            right_current=0.0,
            temperature=0.0,
            is_moving=False,
        )

        # Serial connection (mock for now)
        self.serial_conn = None
        self.is_connected = False

    def connect(self) -> bool:
        """Connect to motor controller via serial. Returns True on success."""
        try:
            # In production, use pyserial:
            # import serial
            # self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=1)
            # For now, simulate connection
            self.is_connected = True
            print(f"Connected to motor controller at {self.port}")
            return True
        except Exception as e:
            print(f"Error connecting to motor controller: {e}")
            return False

    def disconnect(self):
        """Disconnect from motor controller."""
        if self.serial_conn is not None:
            self.serial_conn.close()
        self.is_connected = False

    def set_velocity(self, left_vel: float, right_vel: float) -> bool:
        """
        Set left and right motor velocities.

        Args:
            left_vel: Left motor velocity (-max_velocity to max_velocity)
            right_vel: Right motor velocity (-max_velocity to max_velocity)

        Returns:
            True if command was sent successfully
        """
        if not self.is_connected:
            print("Error: Not connected to motor controller")
            return False

        # Clamp velocities
        left_vel = max(-self.max_velocity, min(self.max_velocity, left_vel))
        right_vel = max(-self.max_velocity, min(self.max_velocity, right_vel))

        try:
            # Build command (example protocol - adapt to your controller)
            # Format: [MOTOR_CMD][LEFT_H][LEFT_L][RIGHT_H][RIGHT_L][CRC]
            left_raw = self._velocity_to_raw(left_vel)
            right_raw = self._velocity_to_raw(right_vel)

            command = bytearray([0x01])  # Motor command
            command.extend(left_raw.to_bytes(2, byteorder="big", signed=True))
            command.extend(right_raw.to_bytes(2, byteorder="big", signed=True))
            command.append(self._calculate_crc(command))

            # Send command via serial (simulated)
            if self.serial_conn:
                self.serial_conn.write(command)

            # Update state
            self.current_state.left_velocity = left_vel
            self.current_state.right_velocity = right_vel
            self.current_state.is_moving = (
                left_vel != 0.0 or right_vel != 0.0
            )

            return True
        except Exception as e:
            print(f"Error sending motor command: {e}")
            return False

    def stop(self) -> bool:
        """Stop both motors. Returns True on success."""
        return self.set_velocity(0.0, 0.0)

    def move_forward(self, velocity: float) -> bool:
        """
        Move forward at given velocity.

        Args:
            velocity: Forward velocity (0 to max_velocity)

        Returns:
            True on success
        """
        velocity = max(0.0, min(self.max_velocity, velocity))
        return self.set_velocity(velocity, velocity)

    def move_backward(self, velocity: float) -> bool:
        """
        Move backward at given velocity.

        Args:
            velocity: Backward velocity (0 to max_velocity)

        Returns:
            True on success
        """
        velocity = max(0.0, min(self.max_velocity, velocity))
        return self.set_velocity(-velocity, -velocity)

    def turn_left(self, velocity: float) -> bool:
        """
        Turn left in place (differential drive).

        Args:
            velocity: Turning velocity

        Returns:
            True on success
        """
        return self.set_velocity(-velocity, velocity)

    def turn_right(self, velocity: float) -> bool:
        """
        Turn right in place (differential drive).

        Args:
            velocity: Turning velocity

        Returns:
            True on success
        """
        return self.set_velocity(velocity, -velocity)

    def read_state(self) -> Optional[MotorState]:
        """
        Read current motor state from controller.

        Returns:
            MotorState or None if read failed
        """
        if not self.is_connected:
            return None

        try:
            # In production, send query command and parse response
            # For now, return simulated state
            return self.current_state
        except Exception as e:
            print(f"Error reading motor state: {e}")
            return None

    def _velocity_to_raw(self, velocity: float) -> int:
        """Convert velocity (m/s) to raw motor command value."""
        # Scale velocity to raw value (e.g., -32768 to 32767 for 16-bit)
        raw_value = int((velocity / self.max_velocity) * 32767)
        return max(-32768, min(32767, raw_value))

    def _calculate_crc(self, data: bytearray) -> int:
        """Calculate simple CRC8 checksum."""
        crc = 0
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ 0x07) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc

    def __del__(self):
        """Cleanup on object destruction."""
        self.disconnect()
