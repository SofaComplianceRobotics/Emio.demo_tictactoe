:::: collapse Requirements
### Requirements

To launch the demo, you need to install: 

1. [**Darknet**](https://github.com/hank-ai/darknet): Darknet is an open source neural network framework written in C, C++, and CUDA. No binaries are provided, you need to clone the GitHub project and compile from source. You can follow the instructions on the [GitHub repository](https://github.com/hank-ai/darknet).
2. [**DarkHelp**](https://github.com/stephanecharette/DarkHelp): The DarkHelp C++ API is a wrapper to make it easier to use the Darknet neural network framework. No binaries are provided, you need to clone the GitHub project and compile from source. You can follow the instructions on the [GitHub repository](https://github.com/stephanecharette/DarkHelp).
3. In DarkHelp.py line 86 : `Predict.argtypes = [c_void_p, c_int, c_int, POINTER(c_uint8), c_int]`
4. Emio Labs is distributed with its own Python interpreter, click the button below to install the python packages required by the demo (see requirements.txt)

#python-button("-m pip install --target 'assets/labs/demo_tictactoe/modules/site-packages' -r 'assets/labs/demo_tictactoe/requirements.txt'")
::::