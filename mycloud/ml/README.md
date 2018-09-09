# General Ideas
Neureal Network to decide whether a given file is worth uploading or not.

# Broad Technical Definition
## Features
- Every part of the path is a feature of the output
 - useful for files contained in certain folders (node_modules, etc.)
- File size
- ctime, mtime
- File extension

## Network
- Use LSTM Network foreach part
- Flatten LSTM outputs
- Connect to output layer


## Outputs
Output Layer: Softmax Probabilities between 0 and 1, where: 0 = not worth uploading, 1 = worth uploading


# Model Customizability
- Add train and evaluate mode
- Save model in .mycloud folder (appdata)

