# Emio Tic Tac Toe

<!-- Camera Calibration -->
#include(assets/labs/modules/camera_calibration.md)

:::: collapse Play with Emio
## Play tic tac toe with Emio


|![Emio with the tic tac toe board](assets/labs/demo_tictactoe/data/images/tictactoe.png){width=50%}|
|:--------------------------------------------------------------------:|
|**Emio with the tic tac toe board.**                               |

The pawns are cubes with a photo of a cat or a dog on top. We trained Emio to recognize the cats and dogs. 
Choose a pawn and start playing with Emio.  

### Gameplay sequence

1. Click the python button below 
2. Follow the instructions on the terminal
3. Choose a difficulty between, "e" (easy), "r" (random), "h" (hard), and "i" (impossible)  
    ![Screenshot of the instructions on the terminal. Start the game.](assets/labs/demo_tictactoe/data/images/instructions.png){width=60%}
4. Emio will start by putting the pawns into the storage zone if the board is not clear.  
5. Once the board is clear, Emio will wait for you to start. If you don't do anything after 10 seconds it will choose a pawn and start the game.
6. At each round, after Emio plays, wait for the instruction to make your move.   
    ![Screenshot of the instructions on the terminal. The rounds.](assets/labs/demo_tictactoe/data/images/roundsInstructions.png){width=35%}  
7. During the game, Emio will check the board at the end of each round and will try to correct it if there is any mismatch. It will try two times, then ask you to correct the board if it didn'd succeed. 
8. At the end of the game, Emio will ask you to play again.


#python-button("assets/labs/demo_tictactoe/play.py")
::::