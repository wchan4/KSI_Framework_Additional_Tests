# KSI_Framework_Additional_Tests

## NOTE: A lot of the pipeline used in the Logistic Regression and Bi-Directional LSTM experiments are taken from the original author's code. The main difference is in the model design itself.

## How to Replicate Experimentation:

1. Clone the following GitHub repo (original paper's source code): https://github.com/tiantiantu/KSI

2. Move the files "KSI_LR.py" and "KSI_LSTM_Bidirectional.py" into main folder of KSI repo (if you want to test these models as well)
- "KSI_LR.py" and "KSI_LSTM_Bidirectional.py" should be in the same folder as other pipeline files (ie. KSI_CNN.py)

3. Set up Conda environment for python 3.7.0 and install the following packages using conda commands (use commands in this order)
- torch=0.4.1 (conda install pytorch=0.4.1 cuda90 -c pytorch)
- sklearn=0.19.2 (conda install -c intel scikit-learn=0.19.2)
- numpy=1.16.1 (conda install -c conda-forge numpy=1.16.1)
  - Downgrades NumPy (IMPORTANT)

4. Follow the instructions listed in the original GitHub repo (Recapped below)
- Run preprocessing1.py, preprocessing2.py, and preprocessing3.py (in that order)
- Run the python file for any desired model tests


Note: Pretrained models are included in TrainedModels folder for all 5 main base models and the 1 additional model. Models were saved using "torch.save" and can be loaded using "torch.load".

## Results:
![alt text](https://github.com/wchan4/KSI_Framework_Additional_Tests/blob/main/model_performance.PNG?raw=true)


## Citations:
Original Paper: Bai, T., Vucetic, S., Improving Medical Code Prediction from Clinical Text via Incorporating Online Knowledge Sources, The Web Conference (WWW'19), 2019.
Original Paper Code: https://github.com/tiantiantu/KSI
