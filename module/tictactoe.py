import random
import copy
import numpy as np
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
        self.restOpeningDistance = 35

        # Initialize Emio simulation
        self.simulation = Sofa.Core.Node("rootnode")
        createEmioScene(self.simulation, self.camera)
        Sofa.Simulation.init(self.simulation)
        # Emio set up animation
        for i in range(200):
            self.simulationStep()


    def displayBoard(self):
        """
        Display the board on the terminal (will be replace by the GUI)
        
        Parameter:
        -----------
        boardState      : list[list[int]]. The board state to display
        """
        self.board.display()
        

    def displayResults(self):
        """
        Display the results of the game and make an emote if there is a winner
        """
        results = self.board.getWinner()
        if results == Results.DRAW.value : 
            logger.info("It's a draw!")
            self.loseEmote()
        elif results == self.humanColor:
            logger.info("Congratulations, you won!")
            self.winEmote()
        else:
            logger.info("Yay, I won!")
            self.loseEmote()


    def hasWinner(self):
        return self.board.hasWinner()
    

    def __emioPlays(self, i, j):
        position = self.board.cellIndicesToPosition(i, j)
        logger.info(f"I'm playing: ({i}, {j}, '{Classes._member_names_[self.computerColor]}')")
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
        # Check if Emio can win
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


    def imageToSimulationPosition(self, x, y, z):
        """
        We only use x and z position in this program  
        """
        position = [0, 0]
        position[0], _, position[1] = self.camera.image_to_simulation(int(x), int(y), z)
        return position


    def getNearestStorageCube(self, color, cellPosition) -> list[float]:
        """
        Parameters:
        -----------
        color           : int. The class of Emio's pawns
        cellPosition

        Return:
        -----------
        cubePosition
        """
        xydwh = self.dhresults.xydwh
        cls = self.dhresults.cls
        prob = self.dhresults.conf

        distance_min = np.finfo(np.float32).max
        nearestStoragePosition = None
        for i in range(len(cls)):
            
            # If the object is the color emio's playing
            if int(cls[i]) == color and prob[i] > 0.6:

                position = self.imageToSimulationPosition(xydwh[i][0], xydwh[i][1], xydwh[i][2])

                # If the position is valid
                if position is None:
                    logger.debug("Problem with the estimated position.")
                    continue 
                
                if not self.board.isInPlayZone(position[0], position[1]):
                    # If the object is not on the play zone
                    distance = np.linalg.norm(np.array(cellPosition)-np.array(position))
                    storageIndex = self.board.positionToStorageIndex(position[0], position[1])
                    storagePosition = self.board.storageIndexToPosition(storageIndex)
                    logger.debug(f"Found a cube to play, not in play zone: {position, Classes._member_names_[int(cls[i])], distance, storageIndex, storagePosition}")
                    # Take the closest object
                    if distance < distance_min:
                        distance_min = distance
                        nearestStoragePosition = np.copy(storagePosition)

        # If it has found an object to play
        if nearestStoragePosition is None:
            logger.info("I did not find a cube to play.")
            return None
        
        logger.debug(f"Found a cube to play, nearest from cell position: {nearestStoragePosition}")
        return nearestStoragePosition
        
    
    def getNearestEmptyStoragePosition(self, cubePosition) -> list[float]:
        """
        Return:
        -----------
        cellPosition
        """
        distance_min = np.finfo(np.float32).max
        closestCellPosition = None

        for i in range(len(self.board.storage)):
            if self.board.storage[i] == Classes.EMPTY.value:
                cellPosition = self.board.storageIndexToPosition(i) # Chose a position of an empty box in the storage zone of the good class            
                distance = np.linalg.norm(np.array(cellPosition) - np.array(cubePosition))
                if distance < distance_min:
                    closestCellPosition = cellPosition
                    distance_min = distance

        return closestCellPosition


    def userPlayed(self) -> bool:
        """
        Detect change of the board state, do not detect any change if a hand is detected
        If the colors of the player is not set and a change is detected, set the color of the player
        Do not trigger if several changes are detected
        Do not detect change if the position or the depth are miscalculated
        """
        cls = self.dhresults.cls
        xydwh = self.dhresults.xydwh 

        playZone_cls = [] # List of classes of the detected objects in the play zone

        new_board = Board()
        new_boardstate = new_board.state # New board state after the change detection
        
        if self.dhresults.isHandDetected(): # If a hand is detected, return
            return False
        
        for i in range(len(cls)): # Loop on the detected classes
            
            position = self.imageToSimulationPosition(xydwh[i][0], xydwh[i][1], xydwh[i][2])

            # If the position is not valid no change detected
            if position is None:
                logger.debug("Problem with the estimated position.")
                return False

            # We only look object in the play zone
            if self.board.isInPlayZone(position[0], position[1]):
                playZone_cls.append(cls[i]) 
                a, b = self.board.positionToCellIndices(position[0], position[1])
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
            

    def selectCubeInPlayZone(self):
        """
        Choose the next cube to be stored

        Parameters:
        -----------
        Return:
        position        : numpy.ndarray. The real world coordinates of the cube
        """
        cls = self.dhresults.cls
        xydwh = self.dhresults.xydwh 

        for i in range(len(cls)):

            if int(cls[i]) == Classes.DOG.value or int(cls[i]) == Classes.CAT.value:

                position = self.imageToSimulationPosition(xydwh[i][0], xydwh[i][1], xydwh[i][2])

                if self.board.isInPlayZone(position[0], position[1]):
                    x, y = self.board.positionToCellIndices(position[0], position[1])
                    return self.board.cellIndicesToPosition(x, y)
                
        return None
            

    def updateStorageState(self):
        """
        Detect the storage zone state
        Does not detect if a hand is detected
        """
        cls = self.dhresults.cls
        xydwh = self.dhresults.xydwh 

        if self.dhresults.isHandDetected(): # If there is a hand return
            return 
        
        self.board.storage = np.copy(Board().storage)
        for i in range(len(cls)):
            
            if int(cls[i]) == Classes.DOG.value or int(cls[i]) == Classes.CAT.value:
                position = self.imageToSimulationPosition(xydwh[i][0], xydwh[i][1], xydwh[i][2])
                j = self.board.positionToStorageIndex(position[0], position[1])
                if j is not None:
                    self.board.storage[j] = int(cls[i])


    def isPlayZoneClear(self) -> bool:
        """
        Detect if there is cubes on the play zone

        Return:
        -----------
        True if the play zone is empty, False otherwise
        """
        cls = self.dhresults.cls
        xydwh = self.dhresults.xydwh 
        
        if self.dhresults.isHandDetected(): # If there is a hand return
            return False

        for i in range(len(cls)): # Loop on the detected classes    
            if int(cls[i]) == Classes.DOG.value or int(cls[i]) == Classes.CAT.value:
                # Get the position of the object
                position = self.imageToSimulationPosition(xydwh[i][0], xydwh[i][1], xydwh[i][1])

                if self.board.isInPlayZone(position[0], position[1]):
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
        logger.info(f"I chose to play with {Classes._member_names_[self.computerColor]}")
        logger.info(f"You are then playing the {Classes._member_names_[self.humanColor]}")

        return True


    def makeEmioPlay(self) -> bool:
        """
        Make Emio chose a move and then play it

        Return:
        -----------
        True if Emio has played, False otherwise
        """
        cellPosition = self.chosenStrategy()

        # The tree next line are to be commented if you want to use the hardcoded position of the box instead of the calculated one
        cubePosition = None
        while cubePosition is None:
            self.dhresults.updateAndDisplayAnnotatedImage()
            cubePosition = self.getNearestStorageCube(self.computerColor, cellPosition)

        logger.debug(f"Picking cube at position: [{cubePosition[0]:.2f}, {cubePosition[1]:.2f}]")
        self.sequenceMove(cubePosition, cellPosition)

        self.takePhotoForDatabase()


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
        self.sendGripperOpening(self.restOpeningDistance)


    def simulationStep(self):        
        self.dhresults.displayAnnotatedImage()
        Sofa.Simulation.animate(self.simulation, self.simulation.dt.value)


    def sequenceMove(self, cubePosition, cellPosition, endInRestPosition=True):
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
        y_place = -280
        y_pick = -290
        gripper_open = 40 
        gripper_close = 15

        # Pick the cube
        if endInRestPosition:
            self.sendGripperPosition(self.restPosition[0], y_move, self.restPosition[2])

        self.sendGripperPosition(cubePosition[0], y_move, cubePosition[1])
        self.sendGripperOpening(gripper_open)
        self.sendGripperPosition(cubePosition[0], y_pick, cubePosition[1], minSteps=70, withPI=True)
        self.sendGripperOpening(gripper_close)
        self.sendGripperPosition(cubePosition[0], y_move, cubePosition[1])

        # Place the cube in the right cell
        self.sendGripperPosition(cellPosition[0], y_move, cellPosition[1])
        self.sendGripperPosition(cellPosition[0], y_place, cellPosition[1], minSteps=70, withPI=True)
        self.sendGripperOpening(gripper_open)
        self.sendGripperPosition(cellPosition[0], y_move, cellPosition[1])

        # Back to rest position
        if endInRestPosition:
            self.sendGripperPosition(self.restPosition[0], y_move, self.restPosition[2])
            self.moveEmioToRestPosition()
    

    def checkAndCorrectBoard(self):
        """
        Check that the real board matches
        """
        def getRealBoard(cls, xydwh):
            realBoard = Board()
            for i in range(len(cls)):
                # If the object is the color emio's playing
                if int(cls[i]) == Classes.DOG.value or int(cls[i]) == Classes.CAT.value:
                    position = self.imageToSimulationPosition(xydwh[i][0], xydwh[i][1], xydwh[i][2])
                    if self.board.isInPlayZone(position[0], position[1]):
                        x, y = self.board.positionToCellIndices(position[0], position[1])
                        realBoard.state[x, y] = int(cls[i])
            return realBoard

        self.dhresults.updateAndDisplayAnnotatedImage()
        cls = self.dhresults.cls
        xydwh = self.dhresults.xydwh
        realBoard = getRealBoard(cls, xydwh)
        matchingCells = (realBoard.state == self.board.state)

        nbMaximumAttempts = 2
        while nbMaximumAttempts > 0 and not matchingCells.all():

            logger.info("Boards mismatch. I will try to fix that!")
            realBoard.display()
            logger.info("!=")
            self.board.display()

            nbMaximumAttempts -= 1
            for i in range(3):
                for j in range(3):
                    if not matchingCells[i][j]:

                        # Should not be empty
                        if realBoard.state[i][j] == Classes.EMPTY.value:
                            cellPosition = self.board.cellIndicesToPosition(i, j)
                            cubePosition = self.getNearestStorageCube(self.board.state[i][j], cellPosition)
                            if cubePosition is not None:
                                self.sequenceMove(cubePosition, cellPosition)

                        # Should be empty
                        elif self.board.state[i][j] == Classes.EMPTY.value:
                            cubePosition = self.board.cellIndicesToPosition(i, j)
                            cellPosition = self.getNearestEmptyStoragePosition(cubePosition)
                            if cellPosition is not None:
                                self.sequenceMove(cubePosition, cellPosition)

                        # Should not be this color
                        else:
                            # First empty the cell
                            cubePosition = self.board.cellIndicesToPosition(i, j)
                            cellPosition = self.getNearestEmptyStoragePosition(cubePosition)
                            if cellPosition is not None:
                                self.sequenceMove(cubePosition, cellPosition)
                            
                            # Get the right color
                            cellPosition = self.board.cellIndicesToPosition(i, j)
                            cubePosition = self.getNearestStorageCube(self.board.state[i][j], cellPosition)
                            if cubePosition is not None:
                                self.sequenceMove(cubePosition, cellPosition)

            self.dhresults.updateAndDisplayAnnotatedImage()
            cls = self.dhresults.cls
            xydwh = self.dhresults.xydwh
            realBoard = getRealBoard(cls, xydwh)
            matchingCells = (realBoard.state == self.board.state)

        if not matchingCells.all():
            logger.error("Sorry I tried to correct the board but did not succeed. Can you fix the board? Thank you.")
            self.displayBoard()

        return


    def clearBoard(self):
        """
        Make Emio clear the board
        """

        self.dhresults.updateAndDisplayAnnotatedImage()
        while not self.isPlayZoneClear(): # If the playzone is not empty
            self.updateStorageState() # Update the storage state to know where to put the cube to store
            
            cubePosition = self.selectCubeInPlayZone() # Choose the next cube to store and return its position
            if cubePosition is None:
                logger.info("The board is clear.")
                return
            
            cellPosition = self.getNearestEmptyStoragePosition(cubePosition)
            if cellPosition is None:
                logger.error("No empty storage left to clear the board.")
                return
            
            self.sequenceMove(cubePosition, cellPosition, endInRestPosition=False)
            self.dhresults.updateAndDisplayAnnotatedImage()
            self.takePhotoForDatabase()


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
    

    def takePhotoForDatabase(self):
        """
        Take a photo and save it in the database
        """
        if self.photo:
            color_image, _, _ = self.dhresults.getProcessedImages()
            if color_image is not None:
                cv.imwrite(os.path.join(self.path, f"Photo_{self.photoID}.jpg"), color_image)
                self.photoID+=1