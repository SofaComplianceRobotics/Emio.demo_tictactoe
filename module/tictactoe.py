import random
import zmq
import copy
import numpy as np
import time
import os
import cv2 as cv

import Sofa

from enum import Enum
from module.board import Board, CellState, Results
from module.emio import createScene as createEmioScene

from module.dhresults import DHResults, Classes
from module.loggerconfig import getLogger
logger = getLogger()


class Strategies(Enum):
    """
    Enum to define the strategies of the computer player
    """
    RANDOM = 'r'
    EASY = 'e'
    HARD = 'h'
    IMPOSSIBLE = 'i'


class TicTacToe () : 
    """
    This class has every methods to play tic tac toe
    """
    
    def __init__(self, boardState, dhresults: DHResults) :
        """
        Initialize the TicTacToe class

        """
        self.board = Board(boardState)
        self.dhresults = dhresults
        self.camera = self.dhresults.camera

        self.results = None
        self.humanColor = None
        self.computerColor = None

        self.width = 640
        self.height = 480
        self.path = ""
        self.photo = False
        self.photoID = 1

        self.strategies = {
                            Strategies.RANDOM.value     : self.randomStrategy,
                            Strategies.EASY.value       : self.easyStrategy,
                            Strategies.HARD.value       : lambda : self.optimalStrategy(rand=True),
                            Strategies.IMPOSSIBLE.value : lambda : self.optimalStrategy(rand=False),
                          }
        self.chosenStrategy = None
       
        self.restPosition = np.array([0, -160, 0])

        # Initialize Emio simulation
        self.simulation = Sofa.Core.Node("rootnode")
        createEmioScene(self.simulation, self.camera)
        Sofa.Simulation.init(self.simulation)
        # Emio set up animation
        for i in range(200):
            self.simulationStep()


    def displayResults(self):
        """
        Display the results of the game and make an emote if there is a winner
        """
        results = self.board.getWinner()
        if results == Results.DRAW.value : 
            logger.info("It's a draw!")
        elif results == self.humanColor:
            logger.info("Congratulations, you won!")
            self.winEmote()
        else:
            logger.info("Sorry, Emio won.")
            self.loseEmote()

        
    def displayBoard(self):
        """
        Display the board on the terminal (will be replace by the GUI)
        
        Parameter:
        -----------
        boardState      : list[list[int]]. The board state to display
        """
        self.board.display()
        

    def hasWinner(self):
        return self.board.hasWinner()
    

    def __emioPlays(self, i, j):
        position = self.board.cellToPosition(i, j)
        logger.info(f"Emio plays: ({i}, {j}, '{Classes._member_names_[self.computerColor]}')")
        return position
    

    def randomStrategy(self):
        """
        Random strategy

        Return:
        -----------
        position        : numpy.ndarray. The real world position of Emio's next move
        """

        emptyCells = [(i, j) for i in range(3) for j in range(3) if self.board.state[i][j] == CellState.EMPTY.value]
        if not emptyCells:
            return None
        while True:
            i, j = random.choice(emptyCells)
            if  self.board.state[i][j] == CellState.EMPTY.value:
                self.board.state[i][j] = self.computerColor
                return self.__emioPlays(i, j)


    def easyStrategy(self):
        """
        Strategy that lead to a draw, look only for the next move and could be counter

        Return:
        -----------
        position        : numpy.ndarray. The real world position of Emio's next move

        """

        board = Board(copy.deepcopy(self.board.state))
        # Check if emio can win
        for i in range(3):
            for j in range(3):
                if self.board.state[i][j] == CellState.EMPTY.value:
                    board.state[i][j] = self.computerColor
                    if board.getWinner() == self.computerColor:
                        self.board.state[i][j] = self.computerColor
                        return self.__emioPlays(i, j)
                    board.state[i][j] = CellState.EMPTY.value   

        # Check if the human can win
        for i in range(3):
            for j in range(3):
                if self.board.state[i][j] == CellState.EMPTY.value:
                    board.state[i][j] = self.humanColor
                    if board.getWinner() == self.humanColor:
                        self.board.state[i][j] = self.computerColor
                        return self.__emioPlays(i, j)
                    board.state[i][j] = CellState.EMPTY.value
                    

        # If no one can win on the next move, play a random move
        emptyCells = [(i, j) for i in range(3) for j in range(3) if self.board.state[i][j] == CellState.EMPTY.value]
        if emptyCells:
            i, j = random.choice(emptyCells)
            self.board.state[i][j] = self.computerColor
            return self.__emioPlays(i, j)


    def optimalStrategy(self, rand=False):
        """
        Optimal strategy, either win or make a draw

        Return:
        -----------
        position        : numpy.ndarray. The real world position of Emio's next move
        """

        board = Board(copy.deepcopy(self.board.state))
        if rand:
            n = random.randint(1, 5)
            if n==1:
                emptyCell = [(i, j) for i in range(3) for j in range(3) if self.board.state[i][j] == CellState.EMPTY.value]
                if not emptyCell:
                    return None
                while True:
                    i, j = random.choice(emptyCell)
                    logger.debug("Emio plays: ", i, j)
                    if  self.board.state[i][j] == Classes.EMPTY.value:
                        self.board.state[i][j] = self.computerColor
                        return self.__emioPlays(i, j)

        if (board.isEqual([[self.humanColor, 0, 0],  [0, self.computerColor, 0], [0, 0, self.humanColor]]) 
            or board.isEqual([[0, 0, self.humanColor], [0, self.computerColor, 0], [self.humanColor, 0, 0]])) :
            self.board.state[0][1]=self.computerColor
            return self.__emioPlays(0, 1)
        
        if board.isEqual([[0, self.humanColor, 0], [self.humanColor, self.computerColor, 0], [0, 0, 0]])  :
            self.board.state[0][0]=self.computerColor
            return self.__emioPlays(0, 0)
        
        if board.isEqual([[0, self.humanColor, 0], [0, self.computerColor, self.humanColor], [0, 0, 0]])  :
            self.board.state[0][2]=self.computerColor
            return self.__emioPlays(0, 2)
        
        if board.isEqual([[0, 0, 0], [0, self.computerColor, self.humanColor], [0, self.humanColor, 0]]) :
            self.board.state[2][2]=self.computerColor
            return self.__emioPlays(2, 2)
        
        if board.isEqual([[0, 0, 0], [self.humanColor, self.computerColor, 0], [0, self.humanColor, 0]]) :
            self.board.state[2][0]=self.computerColor
            return self.__emioPlays(2, 0)
      
        if (board.isEqual([[0, self.humanColor, 0], [0, self.computerColor, 0], [0, 0, self.humanColor]])
            or board.isEqual([[self.humanColor, 0, 0], [0, self.computerColor, self.humanColor], [0, 0, 0]])) :
            self.board.state[0][2]=self.computerColor
            return self.__emioPlays(0, 2)
        
        if (board.isEqual([[0, self.humanColor, 0], [0, self.computerColor, 0], [self.humanColor, 0, 0]])
            or board.isEqual([[0, 0, self.humanColor], [self.humanColor, self.computerColor, 0], [0, 0, 0]]))  :
            self.board.state[0][0]=self.computerColor
            return self.__emioPlays(0, 0)
        if (board.isEqual([[self.humanColor, 0, 0], [0, self.computerColor, 0], [0, self.humanColor, 0]])
             or board.isEqual([[0, 0, 0], [self.humanColor, self.computerColor, 0], [0, 0, self.humanColor]]))  :
            self.board.state[2][0]=self.computerColor
            return self.__emioPlays(0, 2)
        
        if (board.isEqual([[0, 0, self.humanColor], [0, self.computerColor, 0], [0, self.humanColor, 0]])
             or board.isEqual([[0, 0, 0], [0, self.computerColor, self.humanColor], [self.humanColor, 0, 0]]))  :
            self.board.state[2][2]=self.computerColor
            return self.__emioPlays(2, 2)
        
        # First priority : win
        for i in range(3):
            for j in range(3):
                if board.state[i][j] == CellState.EMPTY.value:
                    board.state[i][j] = self.computerColor
                    if board.getWinner() == self.computerColor:
                        self.board.state[i][j] = self.computerColor
                        return self.__emioPlays(i, j)
                    board.state[i][j] =  CellState.EMPTY.value
        
        # Second priority : block the human
        for i in range(3):
            for j in range(3):
                if board.state[i][j] == CellState.EMPTY.value:
                    board.state[i][j] = self.humanColor
                    if board.getWinner() ==  self.humanColor:
                        self.board.state[i][j] = self.computerColor
                        return self.__emioPlays(i, j)
                    board.state[i][j] = CellState.EMPTY.value

        # Third priority : play the center
        if board.state[1][1] == CellState.EMPTY.value:
            self.board.state[1][1] = self.computerColor
            return self.__emioPlays(1, 1)
        
        # Forth priority : play a corner
        for i, j in [(0,2), (0,0), (2,0), (2,2)]:
            if board.state[i][j] == CellState.EMPTY.value:
                self.board.state[i][j] = self.computerColor
                return self.__emioPlays(i, j)
        
        # Fifth priority : play a side
        for i, j in [(0,1), (1,0), (1,2), (2,1)]:
            if board.state[i][j] == CellState.EMPTY.value:
                self.board.state[i][j] = self.computerColor
                return self.__emioPlays(i, j)
        
        return None


    def chooseCubeToPlay(self, color, depth_image, cellPosition):
        """
        Choose the next cube Emio will play
        Choose the nearest cube from the camera

        Parameters:
        -----------
        color           : int. The class of Emio's pawns
        depth_image     : numpy.ndarray. The depth image returned by the camera

        Return:
        -----------
        ret             : bool. True if the position and the index have been correctly calculated, False otherwise
        index           : int. The index (in result) of the chosen cube to play
        """
        xywh = self.dhresults.xywh
        cls = self.dhresults.cls
        prob = self.dhresults.conf

        distance_min = np.finfo(np.float32).max
        index = None

        for i in range(len(cls)):
            
            # If the object is the color emio's playing
            if int(cls[i]) == color and prob[i] > 0.6:

                depth = self.getMedianDepth(i, depth_image)
                position = self.camera.image_to_simulation(int(xywh[i][0]), int(xywh[i][1]), depth)

                # If the position is valid
                if position is None:
                    logger.debug("Problem with the estimated position.")
                    continue 
                
                if not self.board.isInPlayZone(position[0], position[2]):
                    # If the object is not on the play zone

                    distance = np.linalg.norm(np.array(cellPosition)-np.array([position[0], position[2]]))
                    logger.debug(f"Found a cube to play, not in play zone: {position, Classes._member_names_[int(cls[i])], distance}")
                    # Take the closest object
                    if distance < distance_min:
                        distance_min = distance
                        index = i

        # If it has found an object to play
        if index is None:
            logger.info("Emio did not find a cube to play.")
            return None
        
        return index
        
    
    def userPlayed(self, depth_image) -> bool:
        """
        Detect change of the board state, do not detect any change if a hand is detected
        If the colors of the player is not set and a change is detected, set the color of the player
        Do not trigger if several changes are detected
        Do not detect change if the position or the depth are miscalculated
        """
        cls = self.dhresults.cls
        xywh = self.dhresults.xywh 

        playZone_cls = [] # List of classes of the detected objects in the play zone

        new_board = Board()
        new_boardstate = new_board.state # New board state after the change detection
        
        if self.dhresults.isHandDetected(): # If a hand is detected, return
            return False
        
        for i in range(len(cls)): # Loop on the detected classes
            
            depth = self.getMedianDepth(i, depth_image)
            if depth is None:
                logger.debug("Depth problem.")
                return False
            
            position = self.camera.image_to_simulation(xywh[i][0], xywh[i][1], depth)

            # If the position is not valid no change detected
            if position is None:
                logger.debug("Problem with the estimated position.")
                return False

            # We only look object in the play zone
            if self.board.isInPlayZone(position[0], position[2]):
                playZone_cls.append(cls[i]) 
                a, b = self.board.positionToCell(position[0], position[2])
                if cls[i] != Classes.EMPTY.value: 
                    new_boardstate[a][b] = int(cls[i])
                    
        changes = []
        # Check that there is only one change in the board state
        for i in range(3):
            for j in range(3):
                if self.board.state[i][j] != new_boardstate[i][j]:
                    changes.append((i, j, CellState._member_names_[new_boardstate[i][j]]))

        if len(changes)==0:
            logger.debug("No changes detected.")
            return False

        if len(changes)!=1:
            logger.debug(f"Changes: {changes}")
            logger.error("Multiple changes detected. Are you cheating?")
            return False
        
        # For first round, set the human player color
        change = changes[0]
        new_state = new_boardstate[change[0]][change[1]]
        if self.humanColor is None:
            self.humanColor = new_state 
            self.computerColor = (self.humanColor + 1) % 2 
        
        # Next rounds. If the human player color is set, check if the change is valid
        if (new_state == self.humanColor and 
            self.board.state[change[0]][change[1]] == Classes.EMPTY.value):
            self.board.state[change[0]][change[1]] = new_state
            logger.info(f"You played: {change}")
            return True
        
        return False
            

    def selectCubeToStore(self, depth_image):
        """
        Choose the next cube to be stored

        Parameters:
        -----------
        depth_image     : numpy.ndarray. The depth image returned by the camera

        Return:
        position        : numpy.ndarray. The real world coordinates of the cube
        """
        cls = self.dhresults.cls
        xywh = self.dhresults.xywh 

        for i in range(len(cls)):

            if int(cls[i]) == Classes.DOG.value or int(cls[i]) == Classes.CAT.value:

                depth = self.getMedianDepth(self.dhresult, i, depth_image)
                position = self.camera.image_to_simulation(int(xywh[i][0]), int(xywh[i][1]), depth)

                if self.board.isInPlayZone(position[0], position[2]):
                    return position
                
        return None
            

    def updateStorageState(self, depth_image):
        """
        Detect the storage zone state
        Does not detect if a hand is detected

        Parameters:
        -----------
        depth_image     : numpy.ndarray. The depth image returned by the camera
        """
        cls = self.dhresults.cls
        xywh = self.dhresults.xywh 
        for i in range(len(cls)):

            if int(cls[i]) == Classes.HAND.value: # If a hand is detected, return
                return
            
            depth = self.getMedianDepth(self.dhresults, i, depth_image)
            position = self.camera.image_to_simulation(int(xywh[i][0]), int(xywh[i][1]), depth)

            j = self.board.positionToStorage(position[0], position[2])
            if j is not None:
                self.board.storage[j] = int(cls[i])


    def isPlayZoneClear(self, depth_image) -> bool:
        """
        Detect if there is cubes on the play zone

        Parameters:
        -----------
        color           : int. The class of Emio's pawns
        depth_image     : numpy.ndarray. The depth image returned by the camera

        Return:
        -----------
        True if the play zone is empty, False otherwise
        """
        cls = self.dhresults.cls
        xywh = self.dhresults.xywh 
        
        if self.dhresults.isHandDetected(): # If there is a hand return
            return False

        for i in range(len(cls)): # Loop on the detected classes    
            # Get the position of the object
            depth = self.getMedianDepth(self.dhresults, i, depth_image)
            position = self.camera.image_to_simulation(int(xywh[i][0]), int(xywh[i][1]), depth)

            if ((int(cls[i]) == Classes.DOG.value or int(cls[i]) == Classes.CAT.value) and 
                self.board.isInPlayZone(position[0], position[2])):
                return False
        
        return True
    
   
    def makeEmioChooseColor(self):
        """
        Choose the first detected object to play with, either a dog or a cat
        
        Return:
        -----------
        True if there is a cube detected and its position has been correctly calculated, False otherwise

        classe          : int. The class assigned to Emio
        """
        cls = self.dhresults.cls
        prob = self.dhresults.conf
        index = None

        if self.dhresults.isHandDetected():  # If a hand is detected, return
            return False

        for i in range(len(cls)):
            # If the object is an emio's class object
            if (int(cls[i]) == Classes.CAT.value or int(cls[i]) == Classes.DOG.value) and prob[i] > 0.6:
                index = i
                break
                    
        # If it has found an object to play
        if index == None:
            self.humanColor = None
            self.computerColor = None
            return False
 
        self.humanColor = int(cls[index])        
        self.computerColor = (self.humanColor + 1) % 2 
        logger.info(f"Emio chose to play with {Classes._member_names_[self.computerColor]}")
        logger.info(f"You are then playing the {Classes._member_names_[self.humanColor]}")

        return True


    def getMedianDepth(self, i, depth_image) -> float:
        """
        Calculate the depth of the pixel bytaking the median of the valid depths in the bounding box

        Parameters:
        -----------
        i               : int. The index (of result) of the object
        depth_image     : numpy.ndarray. The depth image returned by the camera

        Return:
        ------------
        The median of the depth valid values if there is at least one, None otherwise 
        """
        xywh = self.dhresults.xywh[i]
        x_center, y_center, width, height = xywh
    
        x1 = max(0, int(x_center - width / 2))
        y1 = max(0, int(y_center - height / 2))
        x2 = min(depth_image.shape[1], int(x_center + width / 2))
        y2 = min(depth_image.shape[0], int(y_center + height / 2))
        depth_values = depth_image[y1:y2, x1:x2].flatten()
        
        valid_depth_values = depth_values[depth_values > 0]
    
        if len(valid_depth_values) > 0:
            return np.median(valid_depth_values)
        
        return None


    def sendGripperPosition(self, x, y, z, speed=300, minSteps=40, withPI=False):
        moveEmio = self.simulation.MoveEmio
        moveEmio.setGripperTarget([x, y, z], speed=speed, minSteps=minSteps, withPI=withPI)
        while not moveEmio.done:
            self.simulationStep()
        return 
            

    def sendGripperOpening(self, distance, speed=300, minSteps=40):
        moveEmio = self.simulation.MoveEmio
        moveEmio.setGripperDistance(distance, speed=speed, minSteps=minSteps)
        while not moveEmio.done:
            self.simulationStep()
        return 


    def moveEmioToRestPosition(self):
        """
        Move Emio to the rest position
        """
        self.sendGripperPosition(self.restPosition[0], self.restPosition[1], self.restPosition[2], minSteps=0)


    def simulationStep(self):        
        self.dhresults.displayAnnotatedImage()
        Sofa.Simulation.animate(self.simulation, self.simulation.dt.value)


    def sequenceMove(self, cubePosition, cellPosition):
        """
        Make Emio move through a sequence of movement from:
         1. taking the cube
         2. putting it in the right box and 
         3. going to the rest position

        Parameters:
        -----------
        cubePosition        : numpy.ndarray. The position of the cube
        cellPosition        : list[float]. The position of the box
        """

        # Define the offset y above the cube and the offset to release the cube
        y_move = -230
        y_place = -270
        y_pick = -290
        gripper_rest = 35
        gripper_open = 45
        gripper_close = 15

        # Pick the cube
        self.sendGripperPosition(self.restPosition[0], y_move, self.restPosition[2])
        self.sendGripperPosition(cubePosition[0], y_move, cubePosition[2])
        self.sendGripperOpening(gripper_open)
        self.sendGripperPosition(cubePosition[0], y_pick, cubePosition[2], minSteps=70, withPI=True)
        self.sendGripperOpening(gripper_close)
        self.sendGripperPosition(cubePosition[0], y_move, cubePosition[2])

        # Place the cube in the right cell
        self.sendGripperPosition(cellPosition[0], y_move, cellPosition[1])
        self.sendGripperPosition(cellPosition[0], y_place, cellPosition[1], minSteps=70, withPI=True)
        self.sendGripperOpening(gripper_open)
        self.sendGripperPosition(cellPosition[0], y_move, cellPosition[1])

        # Back to rest position
        self.sendGripperOpening(gripper_rest)
        self.sendGripperPosition(self.restPosition[0], y_move, self.restPosition[2])
        self.moveEmioToRestPosition()
    

    def checkBoard(self):
        """
        Check that the real board matches
        """
        return


    def clearBoard(self):
        """
        Make Emio clear the board
        """
        _, depthImage = self.dhresults.getProcessedImages()

        while not self.isPlayZoneClear(depthImage): # If the playzone is not empty
            _, depthImage = self.dhresults.updateAndDisplayAnnotatedImage()
            self.updateStorageState(depthImage) # Update the storage state to know where to put the cube to store
            
            cubePosition = self.board.cellToPosition(self.board.positionToCell(self.selectCubeToStore(depthImage))) # Chose the next cube to store and return its position
            distance_min = np.finfo(np.float32).max
            closestCellPosition = None
            while self.board.getNextEmptyStorage() is not None:
                cellPosition = self.board.storageToPosition(self.board.getNextEmptyStorage()) # Chose a position of an empty box in the storage zone of the good class
                distance = np.linalg.norm(np.array(cellPosition) - np.array(cubePosition))
                if distance < distance_min:
                    closestCellPosition = cellPosition
                    distance_min = distance

            if closestCellPosition is None or cubePosition is None:
                logger.error("No empty storage left to clear the board.")
                return
            else:
                self.sequenceMove(cubePosition, cellPosition)
                self.takePhotoForDatabase()
        
            depthImage = self.dhresults.updateAndDisplayAnnotatedImage()


    def winEmote(self):
        """
        Make Emio applauds
        """
        self.sendGripperPosition(self.restPosition[0], self.restPosition[1], self.restPosition[2])
        for i in range(10):
            self.sendGripperOpening(8, speed=400, minSteps=10)
            self.sendGripperOpening(35, speed=400, minSteps=10)


    def loseEmote(self):
        """
        Make Emio do some up and down movement
        """
        self.sendGripperPosition(self.restPosition[0], self.restPosition[1], self.restPosition[2])
        for i in range(3):
            self.sendGripperPosition(self.restPosition[0] + 20, self.restPosition[1], self.restPosition[2], speed=500, minSteps=10)
            self.sendGripperPosition(self.restPosition[0] - 20, self.restPosition[1], self.restPosition[2], speed=500, minSteps=10) 
        self.sendGripperPosition(self.restPosition[0], self.restPosition[1], self.restPosition[2])


    def reset(self):
        """
        Reset the parameter to begin a new game
        """
        self.board = Board()
        self.nbEmptyCell = 9
        self.results = None
        self.humanColor = None


    def makeEmioPlay(self) -> bool:
        """
        Make Emio chose a move and then play it

        Return:
        -----------
        True if Emio has played, False otherwise
        """
        cellPosition = self.chosenStrategy()

        # The tree next line are to be commented if you want to use the hardcoded position of the box instead of the calculated one
        _, depth_image = self.dhresults.updateAndDisplayAnnotatedImage()

        cubePosition = None
        index = None
        while cubePosition is None:
            _, depth_image = self.dhresults.updateAndDisplayAnnotatedImage()
            index = self.chooseCubeToPlay(self.computerColor, depth_image, cellPosition)
            depth = self.getMedianDepth(index, depth_image)
            cubePosition = self.camera.image_to_simulation(int(self.dhresults.xywh[index][0]),int(self.dhresults.xywh[index][1]), depth)
            i = self.board.positionToStorage(cubePosition[0], cubePosition[2])
            cubePosition[0], cubePosition[2] = self.board.storageToPosition(i)
            
        logger.debug(f"Picking cube at position: [{cubePosition[0]:.2f}, {cubePosition[1]:.2f}, {cubePosition[2]:.2f}]")
        self.sequenceMove(cubePosition, cellPosition)

        self.takePhotoForDatabase()
    

    def takePhotoForDatabase(self):
        """
        Take a photo and save it in the database
        """
        if self.photo:
            color_image, _ = self.getProcessedImages()
            cv.imwrite(os.path.join(self.path, f"Photo_{self.photoID}.jpg"), color_image)
            self.photoID+=1