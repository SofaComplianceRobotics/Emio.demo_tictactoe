# Emio Tic Tac Toe

<!-- Camera Calibration -->
#include(assets/labs/modules/camera_calibration.md)

:::: collapse Play with Emio
## Play tic tac toe with Emio


|![Emio with the tic tac toe board](assets/labs/demo_tictactoe/data/images/tictactoe.png){width=50%}|
|:--------------------------------------------------------------------:|
|**Emio with the tic tac toe board.**                               |

|![Emio with the tic tac toe board](assets/labs/demo_tictactoe/data/images/instructions.png){width=50%}|
|:--------------------------------------------------------------------:|
|**Screenshot of the instructions on the terminal.**                               |

The pawns are cubes with a photo of a cat or a dog on top. We trained Emio to recognize the cats and dogs. 
Choose a pawn and start playing with Emio.  

**Features**:
- Follow the instructions on the terminal
- Choose a difficulty between: "e" easy, "r" random, "h" hard, "i" impossible
- Emio will wait for you to start. If you don't do anything it will choose a pawn and start the game.
- During the game, Emio will check the board at the end of each round and will try to correct it if there is any mismatch
- At the end of the game you can let Emio put the pawns into the storage zone  

#python-button("assets/labs/demo_tictactoe/play.py")
::::