"""
verification_engine.py

Core verification engine for CraneIQ.

This module compares the detected rigger gesture against the
simulated crane operator action and determines whether the
operator responded correctly.

It only works with gestures, actions and timestamps.
"""

from enum import Enum
import time


class VerificationState(Enum):
    IDLE = "IDLE"
    UNCERTAIN = "UNCERTAIN"
    WAITING_FOR_RESPONSE = "WAITING_FOR_RESPONSE"
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    DELAYED_ACTION = "DELAYED_ACTION"
    NO_ACTION = "NO_ACTION"


class VerificationEngine:
    def __init__(
        self,
        response_window=3.0,   # was 1.5 — loosened for solo/manual testing.
                                # Revert to 1.5 for your final two-person demo recording.
        timeout_window=8.0,    # was 4.0 — gives time to alt-tab + press a key solo.
                                # Revert to 4.0 for your final two-person demo recording.
        hold_time=2.0,
    ):
        self.response_window = response_window
        self.timeout_window = timeout_window
        self.hold_time = hold_time

        self.reset()

    def reset(self):
        """Reset engine to initial state."""

        self.current_state = VerificationState.IDLE

        self.expected_gesture = None
        self.gesture_time = None

        self.operator_action = None
        self.action_time = None

        self.resolved_time = None

    # -------------------------------------------------------------

    def register_gesture(self, gesture, timestamp=None):
        """
        Register a newly confirmed gesture.

        Should be called whenever the ML model confirms a gesture.
        """

        if timestamp is None:
            timestamp = time.time()

        # NEW: don't let a new gesture interrupt a result that's still
        # being displayed on screen/dashboard. Without this, holding the
        # same gesture a moment too long after a MATCH/MISMATCH resolves
        # could immediately re-trigger a new cycle and cut the result
        # display short before hold_time finishes.
        if self.has_result() and self.resolved_time is not None:
            if timestamp - self.resolved_time < self.hold_time:
                return

        # Ignore duplicate confirmed gestures while
        # already waiting for an operator response.
        if (
            gesture == self.expected_gesture
            and self.current_state == VerificationState.WAITING_FOR_RESPONSE
        ):
            return

        if gesture == "IDLE":
            self.current_state = VerificationState.IDLE
            return

        if gesture == "UNCERTAIN":
            self.current_state = VerificationState.UNCERTAIN
            return

        self.expected_gesture = gesture
        self.gesture_time = timestamp

        self.operator_action = None
        self.action_time = None

        self.current_state = VerificationState.WAITING_FOR_RESPONSE

    # -------------------------------------------------------------

    def register_action(self, action, timestamp=None):
        """
        Register a crane operator action.
        """

        if timestamp is None:
            timestamp = time.time()

        if self.expected_gesture is None:
            return

        if self.current_state != VerificationState.WAITING_FOR_RESPONSE:
            return

        self.operator_action = action
        self.action_time = timestamp

        elapsed = timestamp - self.gesture_time

        if action == self.expected_gesture:

            if elapsed <= self.response_window:

                self.current_state = VerificationState.MATCH

            elif elapsed <= self.timeout_window:

                self.current_state = VerificationState.DELAYED_ACTION

            else:

                self.current_state = VerificationState.NO_ACTION

        else:

            self.current_state = VerificationState.MISMATCH

        self.resolved_time = timestamp

    # -------------------------------------------------------------

    def update(self, timestamp=None):
        """
        Call periodically.

        Handles timeout and automatic reset after
        displaying the verification result.
        """

        if timestamp is None:
            timestamp = time.time()

        if self.current_state == VerificationState.WAITING_FOR_RESPONSE:

            elapsed = timestamp - self.gesture_time

            if elapsed >= self.timeout_window:

                self.current_state = VerificationState.NO_ACTION
                self.resolved_time = timestamp

        elif self.current_state in (
            VerificationState.MATCH,
            VerificationState.MISMATCH,
            VerificationState.DELAYED_ACTION,
            VerificationState.NO_ACTION,
        ):

            if (
                self.resolved_time is not None
                and timestamp - self.resolved_time >= self.hold_time
            ):
                self.reset()

    # -------------------------------------------------------------

    def get_state(self):
        """Return current verification state."""

        return self.current_state.value

    # -------------------------------------------------------------

    def get_result(self):
        """
        Return current engine data.

        Suitable for logging and dashboard display.
        """

        return {
            "timestamp": time.time(),
            "gesture": self.expected_gesture,
            "operator_action": self.operator_action,
            "verification_state": self.current_state.value,
            "gesture_timestamp": self.gesture_time,
            "action_timestamp": self.action_time,
        }

    # -------------------------------------------------------------

    def is_waiting(self):
        """True if waiting for operator response."""

        return self.current_state == VerificationState.WAITING_FOR_RESPONSE

    # -------------------------------------------------------------

    def has_result(self):
        """True if verification has completed."""

        return self.current_state in (
            VerificationState.MATCH,
            VerificationState.MISMATCH,
            VerificationState.DELAYED_ACTION,
            VerificationState.NO_ACTION,
        )


# -----------------------------------------------------------------

if __name__ == "__main__":

    engine = VerificationEngine()

    print("\n=== CraneIQ Verification Engine Demo ===\n")

    print("Gesture detected: STOP")

    engine.register_gesture("STOP")

    print(engine.get_state())

    time.sleep(1)

    print("\nOperator presses STOP")

    engine.register_action("STOP")

    print(engine.get_state())

    print(engine.get_result())

    print("\nWaiting for automatic reset...")

    while True:

        engine.update()

        print(engine.get_state())

        if engine.get_state() == "IDLE":
            print("\nEngine reset complete.")
            break

        time.sleep(0.5)