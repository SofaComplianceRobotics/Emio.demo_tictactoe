import numpy as np


class PIController():
    """
    This class implements a PI controller to correct the position of the gripper
    """
    def __init__(self, dt):
        self.dt = dt

        self.ki = 0.08
        self.kp = 0.08
        self.max_integral = 0.08
        
        self.prev_position = [0., 0., 0.]
        self.new_position = [0., 0., 0.]

    def closeLoop(self, position_target, position_real, position_simu):
        """
        Close loop PI controller adjust the real position to the desired position 
        """

        error = position_target - position_real
        self.new_position = self.prev_position + self.ki * error * self.dt
        self.new_position = np.clip(self.new_position, -self.max_integral, self.max_integral)
        
        position_target = position_simu + self.kp * error + self.new_position 
        self.prev_position = self.new_position

        return position_target
