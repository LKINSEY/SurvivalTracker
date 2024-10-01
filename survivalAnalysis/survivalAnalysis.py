#%%
import json
import pandas as pd
import numpy as np
import os
from glob import glob
from readLabelJSON import readLabels
import matplotlib.pyplot as plt

#%% PAIR EACH VARIANT WITH ID
dataPath = 'D:/SurvivalTracker/demo/withoutpreprocessing' ### set to your data dir, defualt is demo
variantIDPair = glob(dataPath + '/notes*')[0]
pairDict = {}
with open(variantIDPair, 'r') as f:
    for line in f:
        if len(((line.split('\t')[0]).split(':')))>1:
            pair = ((line.split('\t')[0]).split(':'))
            value = pair[0]
            key =   pair[1]
            if key in pairDict:
                pairDict[key].append(value)
            else:
                pairDict[key] = [value]
print(      pairDict   )
# %%
def roiSurvival(roiDict):
    timepoints = roiDict.keys()
    isFirst = True
    reverseOrder = False
    spineSurvival = []
    firstLen = 0
    for t in timepoints:
        labelsAtT = pd.DataFrame(roiDict[t]).T
        if isFirst:
            firstLen = len(labelsAtT.visibility.values)
            spineSurvival.append(labelsAtT.visibility[labelsAtT.visibility].values)
            theseSpines = labelsAtT.visibility[labelsAtT.visibility].index
            isFirst = False
        else:
            if len(labelsAtT.visibility.values) >= firstLen:
                # print('pass')
                spineStates = labelsAtT.visibility.values[theseSpines]
                spineSurvival.append(spineStates)
            else:
                reverseOrder = True
                isFirst = True
                spineSurvival = []
    #accounting for wierd save instances
    if reverseOrder:
        for t in reversed(timepoints):
            labelsAtT = pd.DataFrame(roiDict[t]).T
            if isFirst:
                firstLen = len(labelsAtT.visibility.values)
                spineSurvival.append(labelsAtT.visibility[labelsAtT.visibility].values)
                theseSpines = labelsAtT.visibility[labelsAtT.visibility].index
                isFirst = False
            else:
                spineStates = labelsAtT.visibility.values[theseSpines]
                spineSurvival.append(spineStates)
    spineSurvival = np.array(spineSurvival, dtype=np.int64).T

    return spineSurvival


survivalDictionary = {}
for variant in pairDict.keys():
    survivalForVariant = np.zeros((1,3))
    errorForVariant = np.zeros((1,3))
    mouseCount = 0
    survivalRate_acrossROIs = np.zeros((1,3))
    binomialError_acrossROIS = np.zeros((1,3))
    firstMouse = True
    for mouse in pairDict[variant]:
        mouseCount += 1
        mousePath = glob(dataPath + f'/*{mouse}*/labels/')[0]
        roi_count = 1
        firstROI = True
        for roi in os.listdir(mousePath):
            roiPath = glob(mousePath + roi + '/*.json')[0]
            with open(roiPath, 'r') as f:
                labelData = json.load(f)
            thisROI = readLabels(labelData)
            survivalArray = roiSurvival(thisROI)
            if survivalArray.shape[1] ==3:
                survivalRate = np.nanmean(survivalArray, axis=0) #survival rate of roi
            else:
                temp = np.vstack([ survivalArray[:,0].T,  survivalArray[:,3].T, survivalArray[:,6].T]).T
                survivalRate = np.nanmean(temp, axis=0)
            binomialError = np.sqrt(survivalRate * (1- survivalRate) / survivalArray.shape[0])
            if firstROI:
                survivalRate_acrossROIs_sum = survivalRate
                binomialError_acrossROIS_sum = binomialError
                firstROI = False
            else:
                survivalRate_acrossROIs_sum = np.vstack([survivalRate_acrossROIs_sum, survivalRate])#/roi_count #average across ROIs
                binomialError_acrossROIS_sum = np.vstack([binomialError_acrossROIS_sum , binomialError]) #/ roi_count #average binomial error
            roi_count += 1 
        survivalRate_acrossROIs = np.nanmean(survivalRate_acrossROIs_sum, axis=0)   
        binomialError_acrossROIS = np.nanmean(binomialError_acrossROIS_sum, axis=0)
        if firstMouse:
            survivalForVariant = survivalRate_acrossROIs
            errorForVariant = binomialError_acrossROIS
            firstMouse = False
        else:
            survivalForVariant = np.vstack([survivalForVariant , survivalRate_acrossROIs]) 
            errorForVariant = np.vstack([errorForVariant , binomialError_acrossROIS])
    if mouseCount > 1:
        survivalForVariant = np.nanmean(survivalForVariant, axis=0)
        errorForVariant = np.nanmean(errorForVariant, axis=0)
    else:
        survivalForVariant = survivalForVariant
        errorForVariant = errorForVariant
    survivalDictionary[f'{variant}_survivalRate'] = survivalForVariant
    survivalDictionary[f'{variant}_error'] = errorForVariant
print(survivalDictionary)
#%% PLOTTING

for variant in pairDict.keys():
    low = survivalDictionary[f'{variant}_survivalRate'] - survivalDictionary[f'{variant}_error']
    high = survivalDictionary[f'{variant}_survivalRate'] - survivalDictionary[f'{variant}_error']
    print(low)
    print(high)
    plt.fill_between([0,1,2], low, high)
    plt.show()
