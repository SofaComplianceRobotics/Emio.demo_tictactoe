
from module.board import Board, PlayZone, StorageZone, Results
import pytest

def test_board_initialization():
    """
    Test that the board is initialized correctly.
    """
    board = Board()
    assert isinstance(board, Board)
    assert board.playZone == PlayZone()
    assert board.storageZone == StorageZone()


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
def test_board_cell_to_position():
    """
    Test that the board cell to position mapping is correct.
    """
    board = Board()
    assert board.cellIDToPosition(0, 0) == (-PlayZone.dx, PlayZone.dz)
    assert board.cellIDToPosition(1, 1) == (0, 0)
    assert board.cellIDToPosition(2, 2) == (PlayZone.dx, -PlayZone.dz)

    assert board.cellIDToPosition(0, 1) == (-PlayZone.dx, 0)
    assert board.cellIDToPosition(1, 0) == (0, PlayZone.dz)
    assert board.cellIDToPosition(2, 1) == (PlayZone.dx, 0)

def test_board_position_to_cell():
    """
    Test that the board position to cell mapping is correct.
    """
    board = Board()
    assert board.positionToCellID(-PlayZone.dx, PlayZone.dz) == (0, 0)
    assert board.positionToCellID(0, 0) == (1, 1)
    assert board.positionToCellID(PlayZone.dx, -PlayZone.dz) == (2, 2)

    assert board.positionToCellID(-PlayZone.dx, 0) == (0, 1)
    assert board.positionToCellID(0, PlayZone.dz) == (1, 0)
    assert board.positionToCellID(PlayZone.dx, 0) == (2, 1)

    assert board.positionToCellID(-35,  37) == (0, 0)
    assert board.positionToCellID(-25,  -3) == (0, 1)
    assert board.positionToCellID(-30, -30) == (0, 2)

    assert board.positionToCellID(0,    30) == (1, 0)
    assert board.positionToCellID(10,    5) == (1, 1)
    assert board.positionToCellID(-10, -25) == (1, 2)

    assert board.positionToCellID(24,   25) == (2, 0)
    assert board.positionToCellID(32,    7) == (2, 1)
    assert board.positionToCellID(40,  -43) == (2, 2)


def test_board_is_in_play_zone():
    """
    Test that the board correctly identifies positions in the play zone.
    """
    board = Board()
    assert board.isInPlayZone(0, 0) 
    assert board.isInPlayZone(-PlayZone.dx, PlayZone.dz) 
    assert board.isInPlayZone(PlayZone.dx, -PlayZone.dz) 
    assert not board.isInPlayZone(-2 * PlayZone.dx, 2 * PlayZone.dz) 

def test_position_to_storage():
    """
    Test that the board correctly converts positions to storage indices.
    """
    board = Board()

    x = PlayZone.dx / 2
    z = PlayZone.dz / 2

    assert board.positionToStorageID(0, 0) == None
    assert board.positionToStorageID(PlayZone.xmin - x, PlayZone.zmax - z) == 0
    assert board.positionToStorageID(PlayZone.xmin - x, PlayZone.zmax - z - PlayZone.dz * 2) == 2
    assert board.positionToStorageID(0, PlayZone.zmin - z) == 4
    assert board.positionToStorageID(PlayZone.xmax + x, PlayZone.zmax - z) == 6
    assert board.positionToStorageID(PlayZone.xmax + x, 0) == 7
    assert board.positionToStorageID(0, PlayZone.zmax + z) == 10

def test_storage_to_position():
    """
    Test that the board correctly converts storage indices to positions.
    """
    board = Board()

    x = PlayZone.dx / 2
    z = PlayZone.dz / 2

    assert board.storageIDToPosition(12) == None
    assert board.storageIDToPosition(0) == (PlayZone.xmin - x, PlayZone.zmax - z)
    assert board.storageIDToPosition(1) == (PlayZone.xmin - x, PlayZone.zmax - z - PlayZone.dz)


def test_board_storage_zone():
    """
    Test that the board correctly identifies the storage zone.
    """
    board = Board()
    assert board.isInStorageZone(PlayZone.xmin - 1, PlayZone.zmin - 1) 
    assert board.isInStorageZone(StorageZone.xmax, StorageZone.zmax) 
    assert board.isInStorageZone(StorageZone.xmin, StorageZone.zmin) 
    assert board.isInStorageZone(StorageZone.xmax, StorageZone.zmax) 
    assert not board.isInStorageZone(0, 0) 


def test_winner():
    board = Board()
    assert not board.hasWinner() 

    # none
    board = Board([[0, 1, 2],
                    [2, 2, 2],
                    [0, 2, 2]])
    assert not board.hasWinner() 

    # draw
    board = Board([[0, 1, 1],
                    [1, 0, 0],
                    [0, 0, 1]])
    assert board.hasWinner() 
    assert board.getWinner() == Results.DRAW.value

    # winner
    for i in [Results.CAT.value, Results.DOG.value]:

        board = Board([[i, i, i],
                        [2, 2, 2],
                        [2, 2, 2]])
        assert board.hasWinner() 
        assert board.getWinner() == i

        board = Board([[i, 2, 2],
                        [i, 2, 2],
                        [i, 2, 2]])
        assert board.hasWinner() 
        assert board.getWinner() == i


        board = Board([[i, 2, 2],
                        [2, i, 2],
                        [2, 2, i]])
        assert board.hasWinner()
        assert board.getWinner() == i
    