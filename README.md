# KSI_Framework_Additional_Tests

## How to Replicate Experimentation:

1. Clone the following GitHub repo (original paper's source code): https://github.com/tiantiantu/KSI

2. Move the files "KSI_LR.py" and "KSI_LSTM_Bidirectional.py" into main folder of KSI repo (if you want to test these models as well)

3. Set up Conda environment for python 3.7.0 and install the following packages using conda commands (use commands in this order)
- torch=0.4.1 (conda install pytorch=0.4.1 cuda90 -c pytorch)
- sklearn=0.19.2 (conda install -c intel scikit-learn=0.19.2)
- numpy=1.16.1 (conda install -c conda-forge numpy=1.16.1)

4. Follow the instructions listed in the original GitHub repo (Recapped below)
- Run preprocessing1.py, preprocessing2.py, and preprocessing3.py (in that order)
- Run the python file for any desired model tests


Note: Pretrained models are included in TrainedModels folder for all 5 main base models and the 1 additional model. Models were saved using "torch.save" and can be loaded using "torch.load".
