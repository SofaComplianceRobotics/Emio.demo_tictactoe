from dataclasses import dataclass
from enum import Enum
import numpy as np

@dataclass
class PlayZone:

    xmin: int = -45
    zmin: int = -45
    xmax: int = 45
    zmax: int = 45

    dx : int = 30 # from the center of a cell to the center of the next cell
    dz : int = 30 # from the center of a cell to the center of the next cell

@dataclass
class StorageZone:

    xmin: int = -75
    zmin: int = -75
    xmax: int = 75
    zmax: int = 75

class Results(Enum):
    """
    Enum to define the results of the game
    """
    DOG = 0
    CAT = 1
    DRAW = 2
    NONE = -1

class CellState(Enum):
    """
    Enum to define the state of a cell
    """
    DOG = 0
    CAT = 1
    EMPTY = 2
    UNDIFINED = -1


class Board:

    playZone: PlayZone = PlayZone()
    storageZone: StorageZone = StorageZone()

    def __init__(self, state = None):

        if state is not None:
            self.state = np.array(state)
        else:
            self.state = np.array([[CellState.EMPTY.value, CellState.EMPTY.value, CellState.EMPTY.value],
                                    [CellState.EMPTY.value, CellState.EMPTY.value, CellState.EMPTY.value],
                                    [CellState.EMPTY.value, CellState.EMPTY.value, CellState.EMPTY.value]])
            
            self.storage = [[CellState.UNDIFINED.value]*12]

    def isInPlayZone(self, x: float, z: float) -> bool:
        return (self.playZone.xmin <= x <= self.playZone.xmax and
                self.playZone.zmin <= z <= self.playZone.zmax)
    
    def isInStorageZone(self, x: float, z: float) -> bool:
        return (not self.isInPlayZone(x, z) and 
                self.storageZone.xmin <= x <= self.storageZone.xmax and 
                self.storageZone.zmin <= z <= self.storageZone.zmax)
    
    
    # Visualization of the board play zone indices vs position coordinates (center of the cell)
    # +-----------------+-----------------+-----------------+
    # |  (0, 0)         |  (0, 1)         |  (0, 2)         |
    # |  (-dx, dz)      |  (-dx, 0)       |  (-dx, -dz)     |
    # +-----------------+-----------------+-----------------+
    # |  (1, 0)         |  (1, 1)         |  (1, 2)         |
    # |  (0, dz)        |  (0, 0)         |  (0, -dz)       |
    # +-----------------+-----------------+-----------------+
    # |  (2, 0)         |  (2, 1)         |  (2, 2)         |
    # |  (dx, dz)       |  (dx, 0)        |  (dx, -dz)      |
    # +-----------------+-----------------+-----------------+

    def positionToCell(self, x: float, z: float) -> tuple:
        """
        Converts position coordinates to cell indices.
        returns None if the position is not in the play zone, otherwise returns a tuple (i, j)
        """
        if not self.isInPlayZone(x, z):
            return (None, None)

        i = int((x + self.playZone.xmax) //  self.playZone.dx ) 
        j = int((z - self.playZone.zmax) // -self.playZone.dz ) 

        return (i, j)
    
    def cellToPosition(self, i: int, j: int) -> tuple:
        """
        Converts cell indices to position coordinates.
        """
        x = (i - 1) * self.playZone.dx
        z = (1 - j) * self.playZone.dz
        return (x, z)
    
    # Visualization of the storage zone indices 
    # |    | 0  | 1  | 2  |    |
    # | 9  |    |    |    | 3  |
    # | 10 |    |    |    | 4  |
    # | 11 |    |    |    | 5  |
    # |    | 6  |  7 | 8  |    |

    def positionToStorage(self, x: float, z: float) -> int:
        """
        Converts position coordinates to storage indices.
        returns None if the position is not in any player's zone, otherwise returns a tuple (storageID, cellID)

        """
        if self.isInStorageZone(x, z):
            if x < self.playZone.xmin: # zone up
                i = int((z - self.playZone.zmax) // -self.playZone.dz )
            elif z < self.playZone.zmin: # zone right
                i = int((x + self.playZone.xmax) //  self.playZone.dx ) + 3
            elif x > self.playZone.xmax: # zone down
                i = int((z - self.playZone.zmax) // -self.playZone.dz ) + 6
            else: # zone left
                i = int((x + self.playZone.xmax) //  self.playZone.dx ) + 9
            return i

        return None
    
    def storageToPosition(self, cellID: int) -> tuple:
        """
        Converts storage indices to position coordinates.
        """

        if 0 > cellID or cellID > 11:
            return None

        if 0 <= cellID <= 2:
            x = - self.playZone.dx * 2
            z = (1 - cellID % 3) * self.playZone.dz
        elif 3 <= cellID <= 5:
            x = (cellID % 3 - 1) * self.playZone.dx
            z = - self.playZone.dz * 2
        elif 6 <= cellID <= 8:
            x = self.playZone.dx * 2
            z = (1 - cellID % 3) * self.playZone.dz
        else:
            x = (cellID % 3 - 1) * self.playZone.dx
            z = self.playZone.dz * 2

        return (x, z)

    def getNextEmptyStorage(self) -> int:
        """
        Returns the next empty storage index.
        If no empty storage is found, returns None.
        """
        for i in range(len(self.storage)):
            if self.storage[i] == CellState.EMPTY:
                return i
        return None
    
    def display(self):
        """
        Display the board on the terminal (will be replace by the GUI)
        
        Parameter:
        -----------
        self.state      : list[list[int]]. The board state to display
        """
        for row in self.state:
            for i in row:
                if i == CellState.EMPTY.value:
                    print(" . ", end="")
                elif i == CellState.DOG.value:
                    print(" X ", end="")
                elif i == CellState.CAT.value:
                    print(" O ", end="")
                elif i == CellState.UNDIFINED.value:
                    print(" , ", end="")
            print("\n")


    def hasWinner(self) -> bool:
        return self.getWinner() != Results.NONE.value


    def getWinner(self):
        """
        Check if the board state given has a winner
        Used in optimalStrategy and easyStrategy to block or to play the best move

        Return:
        -----------
        results        : int. The result of the next calculated move
        """
        
        # Check rows
        for row in self.state:
            if (row == CellState.CAT.value).all() or (row == CellState.DOG.value).all():   
                return row[0] # We have a winner

        # Check columns
        for colId in range(3):
            col = np.array(self.state[:, colId])
            if (col == CellState.CAT.value).all() or (col == CellState.DOG.value).all():
                return col[0] # We have a winner

        # Check diagonals
        if self.state[0][0] == self.state[1][1] == self.state[2][2] and self.state[0][0] != CellState.EMPTY.value:
            return self.state[0][0] # We have a winner
        if self.state[0][2] == self.state[1][1] == self.state[2][0] and self.state[0][2] != CellState.EMPTY.value: 
            return self.state[0][2] # We have a winner

        # Game not finished yet
        for row in self.state:
            if (row == CellState.EMPTY.value).any():
                return Results.NONE.value
            
        # Then it's a draw
        return Results.DRAW.value
    
    def isEqual(self, state):
        return (state == self.state).all()