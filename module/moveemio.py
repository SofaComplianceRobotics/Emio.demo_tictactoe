import os
import sys


sys.path.append(os.path.dirname(os.path.realpath(__file__))+"/../../..")
import os.path

import Sofa.Core 
import numpy as np

from module.picontroller import PIController
from emioapi import EmioMotors
from enum import Enum


class MoveEmio(Sofa.Core.Controller):
    """
    This class controlles Emio's movement
    """

    def __init__(self, target, emio, camera, *args, **kwargs):
       
        Sofa.Core.Controller.__init__(self)
        self.name = "MoveEmio"

        self.target = target
        self.emio = emio

        self.listDeltaPosition = []
        self.listDeltaGripper = []

        self.steps = 0
        self.done = True
        self.camera = camera
        self.minMotionSteps = 80

        self.PI = PIController(self.emio.getRoot().dt.value)
        self.withPI = False
        self.tipTarget = None

        # Initialize Emio motors connection
        self.emiomotors = EmioMotors()
        emioConnected = self.emiomotors.is_connected
        if not emioConnected:
            if self.emiomotors.findAndOpen() == -1:
                Sofa.msg_error("MotorController", "Could not find or connect Emio robots. Please check the connection.")


    def setGripperTarget(self, target: list[float], speed, minSteps, withPI=False):
        self.done = False
        self.minMotionSteps = minSteps
        self.steps = self.minMotionSteps
        self.withPI = withPI
        self.tipTarget = target
        self.emio.CenterPart.TipEffector.EffectorCoord.maxSpeed.value = speed
        self.target.getMechanicalState().position.value = [target + [0, 0, 0, 1]]


    def setGripperDistance(self, distance, speed, minSteps):
        self.done = False
        self.minMotionSteps = minSteps
        self.steps = self.minMotionSteps
        self.emio.CenterPart.Effector.Distance.PositionEffector.maxSpeed.value = speed
        self.emio.CenterPart.Effector.Distance.DistanceMapping.restLengths.value = [distance] 


    def updateListDelta(self, deltaPosition, deltaGripper):
        """
        Update the list of delta values.
        This function is used to keep track of the last ten delta values.
        """
        if len(self.listDeltaPosition) >= 10:
            self.listDeltaPosition.pop(0)
        self.listDeltaPosition.append(deltaPosition)

        if len(self.listDeltaGripper) >= 10:
            self.listDeltaGripper.pop(0)
        self.listDeltaGripper.append(deltaGripper)


    def getGripperFingersTipBarycenter(self):
        self.camera.update()
        positionMarkers = self.camera.trackers_pos

        tipSimulation = np.array(self.emio.CenterPart.TipEffector.EffectorCoord.barycenter.value[0:3])
        tipTarget = np.array(self.tipTarget)

        if (len(positionMarkers) != 2):
            return tipSimulation, tipTarget, tipSimulation
        
        centerReal = 0.5 * np.array(positionMarkers[0]) + 0.5 * np.array(positionMarkers[1])
        centerSimulation = np.array([0., 0., 0.])
        attachPositions = self.emio.CenterPart.LegsAttach.getMechanicalState().position.value
        for position in attachPositions:
            centerSimulation += np.array(position[0:3])
        centerSimulation /= len(attachPositions)

        tipReal = centerReal + (tipSimulation - centerSimulation)

        return tipReal, tipTarget, tipSimulation


    def onAnimateBeginEvent(self, _):
        if not self.done:

            positionEffector = self.emio.CenterPart.TipEffector.EffectorCoord
            distanceEffector = self.emio.CenterPart.Effector.Distance.PositionEffector

            position_real, position_target, position_simulation = self.getGripperFingersTipBarycenter()
            target_pid = self.PI.closeLoop(position_target=position_target,
                                            position_real=position_real,
                                            position_simu=position_simulation)
            self.target.getMechanicalState().position.value = [list(target_pid) + [0, 0, 0, 1]] if self.withPI else [list(position_target) + [0, 0, 0, 1]]
            deltaPosition = positionEffector.delta.value[0] 
            deltaGripper = distanceEffector.delta.value[0]
            self.updateListDelta(deltaPosition, deltaGripper)

            if self.steps > 0:
                self.steps -= 1
            if (abs(np.mean(np.array(self.listDeltaPosition))) < 1 and 
                abs(np.mean(np.array(self.listDeltaGripper))) < 1 and 
                self.steps <= 0):
                # 1. If the variation of delta is almost none 
                # 2. If the gripper is at its desired state
                # 3. Wait steps sequence

                # Update the current data with the new message
                self.done = True


    def onAnimateEndEvent(self, _):
        if not self.done:
            
            angles = []
            for motor in self.emio.motors:
                angles.append(motor.JointActuator.angle.value)
            self.emiomotors.angles = angles
