#%%
import json
import pandas as pd
import numpy as np

# with open('D:/iGluSnFR_testing_project/Spine_Analysis/data/activity_Analysis/706100/labels/roiNum7/roiNum7_labels.json', 'r') as f:
#     labels = json.load(f)
# print(labels.keys())
#%%
def readLabels(labels):
    stringOfInterest = '{'
    saveDict = {}

    for tPoint in labels.keys():
        thisTimePoint = {} 
        dataString = labels[tPoint]
        roiNum = 0
        start = 0
        startLocations = []
        stopLocations = []
        while True:
            #find polygon dict
            start = dataString.find(stringOfInterest, start)
            end = dataString.find('}', start)
            if start ==-1:
                break
            startLocations.append(start)
            stopLocations.append(end)
            
            #get coordinates
            roiOutput = dataString[startLocations[roiNum]:stopLocations[roiNum]+1]
            temp = roiOutput.split('QPoint')[1]
            ROIcoords = eval(temp[:temp.find(')')+1])
            x_i = ROIcoords[0]
            y_i = ROIcoords[1]
            #get visibility
            visibility_temp = temp.split("'visible': ")[1]
            visible = eval(visibility_temp[:visibility_temp.find('}')])
            roi = {}

            #reconstruct polygon dictionary
            roi['center'] = ROIcoords
            roi['visibility'] = visible
            
            thisTimePoint[roiNum] = roi
            roiNum+=1
            start += len(stringOfInterest)
        # print(thisTimePoint)
        saveDict[tPoint] = thisTimePoint
    return saveDict



#%%

def roiSurvival(roiDict):
    timepoints = roiDict.keys()
    isFirst = True
    spineSurvival = []
    for t in timepoints:
        labelsAtT = pd.DataFrame(roiDict[t]).T
        if isFirst:
            spineSurvival.append(labelsAtT.visibility[labelsAtT.visibility].values)
            theseSpines = labelsAtT.visibility[labelsAtT.visibility].index
            isFirst = False
        else:
            spineStates = labelsAtT.visibility.values[theseSpines]
            spineSurvival.append(spineStates)
    spineSurvival = np.array(spineSurvival, dtype=np.int64).T
    return spineSurvival