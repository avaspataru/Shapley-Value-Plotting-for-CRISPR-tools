import shap
import pandas as pd
import pickle

from tuscandata import *
from sgRNAScorer2data import *
from wucrisprdata import *
from sscdata import *

#gets the 30-nucleotide sequences from the dataset (Xu / Doench)
def getDataset(datasetName, toolName):

    sequences = []

    if datasetName == 'Xu':
        #WHERE THE DATASET IS
        INPUT_FILE_NAME = "/users/ms19avs/Documents/proj/datasets/Xu-2015_Is-Efficient.csv"

        # Used for extracting the guide from the CSV format
        if (toolName in ['tuscan-regression','tuscan-classification']): #Tuscan has a special extraction of data since it uses context around the guide
            GUIDE_INDEX = 4
            GUIDE_START_POS = 10 - 4
            GUIDE_LEN = 23 + 4 + 3 # TUSCAN considers nucleotides 4 upstream, 3 upstream from guide (?=([ACTG]{25}GG[ACTG]{3}))
        elif toolName == 'wu-crispr': #it needs 3 more nucleotides after the guide
            GUIDE_INDEX = 4
            GUIDE_START_POS = 10
            GUIDE_LEN = 23 + 3
        elif toolName == 'ssc': #it doesn't take the PAM
            GUIDE_INDEX = 4
            GUIDE_START_POS = 10
            GUIDE_LEN = 20
        else:
            GUIDE_INDEX = 4
            GUIDE_START_POS = 10
            GUIDE_LEN = 23

        #read in sequences
        with open(INPUT_FILE_NAME, 'r') as fRead:
            # read each line - file contains header and blank footer - then break apart by comma
            for line in [x.split(',') for x in fRead.read().split('\n')[1:-1]]:
                guideSeq = line[GUIDE_INDEX][GUIDE_START_POS:(GUIDE_START_POS + GUIDE_LEN)]
                sequences.append(guideSeq)

        return sequences
    elif datasetName =='Doench':
        print("Loading Doench not yet here")
        quit()
    else:
        print("Dataset not supported")
        quit()

def getToolObject(toolName):
    if toolName in ['tuscan-regression','tuscan-classification']:
        tool = TuscanData()
        tool.setRegressionFlag(toolName=='tuscan-regression')
    elif toolName == 'sgRNAScorer2':
        tool = SgRNAScorer2Data()
    elif toolName == 'wu-crispr':
        tool = WuCrisprData()
    elif toolName == 'ssc':
        tool = SSCData()
    else:
        print("Tool Name not valid")
        quit()
    return tool

def main(toolName,datasetName):

    tool = getToolObject(toolName)

    tool.loadModel().predict([tool.getFeatures("AAGCCAAAGAGAAAGGTACC")])

    train_df = tool.loadTrainingSet()

    #load the dataset
    sequences = getDataset(datasetName, toolName)
    print("Loaded the dataset " + datasetName + " of " + str(len(sequences)) + " data points.")

    #calculate the features for the dataset
    print("Calculating features for the dataset. [Might take a while for wu-crispr]")
    feature_set = []
    cnt = 1
    for seq in sequences:
        features = tool.getFeatures(seq)
        feature_set.append(features)
        if toolName == 'wu-crispr' and cnt % 100 == 0: #inform on progress
            print("Calculated features for " + str(cnt))
        cnt = cnt + 1
    print("Calculated the features for this dataset.")

    #get feature names
    feature_names = tool.loadFeatureNames()
    print("Loaded the names of all " + str(len(feature_names)) + " features.")

    #put together features with names in one dataframe
    dataset_df = pd.DataFrame(np.array(feature_set),columns=feature_names)

    #training set (must be loaded before model)
    train_df = tool.loadTrainingSet()
    print("Loaded the training set used for tool " + toolName + ", size: " + str(train_df.shape)+ ".")

    #load model
    model = tool.loadModel()
    print("Loaded the model for tool " + toolName + ".")

    #summarize training set and subsample test set
    summary_train_df = shap.kmeans(train_df,2)
    dataset_sub_df = dataset_df # dataset_df.sample(400)

    #compute and plot shapley values
    svm_shap_values = shap.KernelExplainer(model.predict,summary_train_df)
    shap.summary_plot(svm_shap_values.shap_values(dataset_sub_df), dataset_sub_df)


toolName = "ssc"
datasetName = "Xu"
main(toolName,datasetName)
