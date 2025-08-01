from parts.gripper import Gripper
from parts.controllers.assemblycontroller import AssemblyController
from parts.emio import Emio
from utils.header import addHeader, addSolvers


def createScene(rootnode,
                camera
                ):
    #create a Sofa scene
    
    from module.moveemio import MoveEmio

    settings, modelling, simulation = addHeader(rootnode, inverse=True)
    addSolvers(simulation, rayleighStiffness=0.1)
    rootnode.ConstraintSolver.epsilon.value = 0.1

    rootnode.dt = 0.01
    rootnode.gravity = [0., -9810., 0.]

    # Add Emio to the scene
    emio = Emio(name="Emio",
                legsName=["tictactoeleg"],
                legsModel=["beam"],
                legsPositionOnMotor=["counterclockwisedown", "clockwisedown", "counterclockwisedown", "clockwisedown"],
                centerPartName="whitepart",  # choose the gripper as the center part
                centerPartType="deformable",  # the gripper is deformable
                centerPartModel="beam",
                centerPartClass=Gripper,  # specify that the center part is a Gripper
                platformLevel=2,
                extended=True)
    if not emio.isValid():
        return

    simulation.addChild(emio)
    emio.attachCenterPartToLegs()
    emio.addObject(AssemblyController(emio))

    # Add effector
    emio.effector= emio.CenterPart.addChild("TipEffector")
    emio.effector.addObject("MechanicalObject", template="Rigid3", position=[0, 0, 0, 0, 0, 0, 1] * 2)
    emio.effector.addObject("RigidMapping", rigidIndexPerPoint=[29, 39]) # Create a target that emio will follow between the gripper's extremities
   
    # Target
    effectorTarget = modelling.addChild('Target')
    effectorTarget.addObject('EulerImplicitSolver', firstOrder=True)
    effectorTarget.addObject('CGLinearSolver', iterations=50, tolerance=1e-10, threshold=1e-10)
    effectorTarget.addObject('MechanicalObject', template='Rigid3',
                             position=[[0, -160, 0, 0, 0, 0, 1]],
                             showObject=True, showObjectScale=20)

    # Add inverse components and GUI
    emio.addInverseComponentAndGUI(effectorTarget.getMechanicalState().position.linkpath, barycentric=True, withGUI=False)

    TCP = modelling.addChild("TCP")
    TCP.addObject("MechanicalObject", template="Rigid3", position=emio.effector.EffectorCoord.barycenter.linkpath)

    # Our position controller that communicate with the tictactoe game
    emio.CenterPart.TipEffector.EffectorCoord.maxSpeed.value = 100
    emio.CenterPart.Effector.Distance.PositionEffector.maxSpeed.value = 100
    rootnode.addObject(MoveEmio(target=effectorTarget, 
                                emio=emio, 
                                camera=camera))

    return rootnode
