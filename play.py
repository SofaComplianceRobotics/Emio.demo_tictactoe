
import time 
import cv2 as cv
import numpy as np
import os

import DarkHelp

from module.tictactoe import TicTacToe, Players, Strategies
from module.dhresults import DHResults, Classes
from module.loggerconfig import getLogger, logging
logger = getLogger()
logger.info(f"Logger has been initialized with level: {logging.getLevelName(logger.level)}")



def createPhotoDirectory():
    """
    Create a folder where the photo will be put
    """
    import os
    import re

    # Directory where the photos will be stored
    base_folder = os.path.join(os.path.dirname(__file__), 'yolov4', 'picture_for_database', 'data_base')
    # Make sure the base folder exists
    os.makedirs(base_folder, exist_ok=True)

    # Search all existing folders with the format "photo_partie_i"
    existing = [d for d in os.listdir(base_folder) if re.match(r"photo_partie_\d+$", d)]
    if existing == []:
        next_index=1
    else:
        # Extract the index "i" from the folder names and find the next available index
        existing_indices = [int(re.search(r"photo_partie_(\d+)", d).group(1)) for d in existing]
        next_index = max(existing_indices, default=0) + 1

    # Create the new folder
    new_folder_name = f"photo_partie_{next_index}"
    new_folder_path = os.path.join(base_folder, new_folder_name)
    os.makedirs(new_folder_path)
    logger.info(f"New folder created: {new_folder_path}")
    return new_folder_path


def calibrationStep(tictactoe: TicTacToe):
    """
    Ask the user if they want to calibrate the camera
    """
    answer = ""
    while answer != "y" and answer != "n":
        answer = input("Do you want to calibrate the camera (y/n)?")

    if answer == "y":
        tictactoe.camera.calibrate()
        logger.info("Calibration done.")

    return


def enrichDatabaseStep(tictactoe):
    """
    Ask the user if they want to enrich the database
    """
    answer = ""
    while answer != "y" and answer != "n":
        answer = input("Do you want to take photo at each change to enrich the database (y/n)?")

    if answer == "y":
       tictactoe.photo = True
    else:
        tictactoe.photo = False
    return


def difficultyStep(tictactoe):
    """
    Ask the user to choose the difficulty of Emio's strategy
    """
    answer = ""
    while answer not in [item.value for item in Strategies]: 
        answer = input("Choose a difficulty for the game (r: random, e: easy, h: hard, i: impossible) : ").lower()
    tictactoe.chosenStrategy = tictactoe.strategies.get(answer)


def startNewGameStep():
    """
    Ask the user if they want to play
    """
    answer=""
    play = True
    while answer != "y" and answer != "n":
        answer = input("Start a new game (y/n)?")
    if answer == "n":
        play=False
    return play


def clearBoardStep(tictactoe: TicTacToe, dhresults: DHResults):
    """
    Make Emio clear the board
    """
    colorImage, depthImage = dhresults.getProcessedImages()

    while not tictactoe.isPlayZoneClear(depthImage): # If the playzone is not empty
        colorImage, depthImage = dhresults.updateAndDisplayAnnotatedImage()
        tictactoe.updateStorageState(depthImage) # Update the storage state to know where to put the cube to store
        
        cubePosition, color = tictactoe.selectCubeToStore(depthImage) # Chose the next cube to store and return its position
        cellPosition = None
        if color is not None:
            cellPosition = tictactoe.board.storageToPosition(tictactoe.board.getNextEmptyStorage()) # Chose a position of an empty box in the storage zone of the good class
        
        if cellPosition is None:
            pass
        else:
            tictactoe.sequenceMove(cubePosition, cellPosition)
            tictactoe.takePhotoForDatabase()
       
        colorImage, depthImage = dhresults.updateAndDisplayAnnotatedImage()


def firstRound(tictactoe: TicTacToe, dhresults: DHResults):
    """
    First round of the TicTacToe game (at the end of this round, Emio must has played, next player should be the human)
    Decide who plays first and distribute the colors
    """
    t0 = time.time()
    _, depthImage = dhresults.updateAndDisplayAnnotatedImage()

    # Wait 10 seconds for the player to play, or if a hand is detected, then Emio plays
    while (dhresults.isHandDetected() or 
           (time.time()-t0 < 10 and not tictactoe.userPlayed(depthImage))): 
        
        _, depthImage = dhresults.updateAndDisplayAnnotatedImage()

    tictactoe.takePhotoForDatabase()

    if tictactoe.humanColor is None: # If the human did not play first, Emio will take the first detected color
        while not tictactoe.makeEmioChooseColor(depthImage):
            _, depthImage = dhresults.updateAndDisplayAnnotatedImage()
    else:
        tictactoe.displayBoard()

    tictactoe.makeEmioPlay()
    tictactoe.displayBoard()
    return 


def gameLoop():
    """
    Game loop of the TicTacToe game
    """

    dhresults = DHResults()
    tictactoe = TicTacToe(boardState=[
                                        [0, 0, 0],
                                        [0, 0, 0],
                                        [0, 0, 0] ],
                          dhresults=dhresults)
   
    # User choices
    # calibrationStep(tictactoe)
    # enrichDatabaseStep(tictactoe)
    # difficultyStep(tictactoe)
    tictactoe.chosenStrategy = tictactoe.strategies.get("i")

    while startNewGameStep():

        # Initialize the game
        tictactoe.reset()
        tictactoe.moveEmioToRestPosition()
        tictactoe.sendGripperOpening(35)
        tictactoe.displayBoard()

        # Photo step, if the user chose to take photo, create a directory to store them
        if tictactoe.photo:
            tictactoe.path = createPhotoDirectory()
        tictactoe.photoID = 1

        firstRound(tictactoe, dhresults) # First round of the game

        # Loop on the next rounds
        while not tictactoe.hasWinner():
            logger.debug("Starting a new round.")
            logger.info(f"Your turn to play: ('{Classes._member_names_[tictactoe.humanColor]}')")
            
            # We wait for the human to play and the boardstate to be has it should  
            _, depthImage = dhresults.updateAndDisplayAnnotatedImage()
            while not tictactoe.userPlayed(depthImage): 
                _, depthImage = dhresults.updateAndDisplayAnnotatedImage()

            # The human has played, now it's Emio's turn
            tictactoe.takePhotoForDatabase()
            tictactoe.displayBoard()
            if tictactoe.hasWinner(): # If there is a winner or a draw, break
                break

            tictactoe.makeEmioPlay() # Emio plays
            tictactoe.displayBoard()

        tictactoe.displayResults()
        tictactoe.moveEmioToRestPosition()

        input("Press any key to make Emio clear the board.")
        clearBoardStep(tictactoe)
    
    # Cleanup
    DarkHelp.DestroyDarkHelpNN(dhresults.dh)


def main():
    """
    Main function to run the TicTacToe game 
    """
    # Game loop
    gameLoop()
        

if __name__ == "__main__":
   main()



