:::: collapse Gameplay Sequence
### Gameplay Sequence

|![Screenshot of the instructions on the terminal. Start the game.](assets/labs/demo_tictactoe/data/images/instructions.png){width=100%}| ![Screenshot of the instructions on the terminal. The rounds.](assets/labs/demo_tictactoe/data/images/roundsInstructions.png){width=60%}  |
|:--------------------------------------------------------------------:|:--------------------------------------------------------------------:|
|**Screenshot of the instructions on the terminal. Start the game.**                               |**Screenshot of the instructions on the terminal. The rounds.**|

::: highlight
#icon("info")

**Important:** In the field below, set the path to the DarkHelp python library. This is required for Emio to use the Darknet neural network framework.
#input("darkhelp_path", "Path to DarkHelp", "PATH_TO_darkhelp/src-python")  
:::
   
1. Click the python button below 
2. Follow the instructions on the terminal
3. Choose a difficulty between:
    - "e" (easy),
    - "r" (random),
    - "h" (hard), 
    - and "i" (impossible)  
4. Emio will start by putting the pawns into the storage zone if the board is not clear.  
5. Once the board is clear, Emio will wait for you to start. If you don't do anything after 10 seconds it will choose a pawn and start the game.
6. At each round, after Emio plays, wait for the instruction to make your move, otherwise Emio will think you're cheating!    
7. During the game, Emio will check the board at the end of each round and will try to correct it if there is any mismatch. It will try two times, then ask you to correct the board if it didn't succeed. 
8. At the end of the game, Emio will ask you to play again.

#python-button("assets/labs/demo_tictactoe/play.py", "darkhelp_path")
::::