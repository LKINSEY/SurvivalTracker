#%%
import sys, os, fitz, json
from PyQt6.QtWidgets import  QPushButton, QComboBox, QHBoxLayout, QLabel,  QApplication,  QMainWindow,  QPushButton, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QPainter, QPolygon,  QImage, QPixmap, QColor,  QIcon
from glob import glob
from pathlib import Path
import numpy as np
import tifffile as tiff
import matplotlib.pyplot as plt

userDir = (os.getcwd()).split('SurvivalTracker')[0][:-1]

class PDFLabel(QLabel):
    def __init__(self, pixmap):
        super().__init__()
        self.setPixmap(pixmap)
        self.polygons = []  
        self.selectedPolygon = None
        self.middleButtonPressed = False  
        self.lastMousePosition = None  
        self.moveAllPolygonsMode = False  

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.middleButtonPressed = False
            pos = event.pos()
            self.addPolygon(pos)
        elif event.button() == Qt.MouseB.utton.RightButton:
            self.middleButtonPressed = False
            self.hidePolygon(event.pos())
        elif event.button() == Qt.MouseButton.MiddleButton:
            if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                self.moveAllPolygonsMode = True
            else:
                self.selectPolygon(event.pos())
            self.middleButtonPressed = True
            self.lastMousePosition = event.pos()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            self.middleButtonPressed = False
            self.moveAllPolygonsMode = False
            self.lastMousePosition = None

    def mouseMoveEvent(self, event):
        if self.middleButtonPressed:
            if self.moveAllPolygonsMode:
                self.moveAllPolygons(event.pos())
            elif self.selectedPolygon is not None:
                self.movePolygon(event.pos())

    def addPolygon(self, pos):
        polygon = {
            'center': pos,
            'polygon': self.createPolygon(pos),
            'visible': True
        }
        self.polygons.append(polygon)
        self.update()
    def createPolygon(self, center):
        size = 10  
        points = [
            QPoint(center.x() + int(size), center.y()),
            QPoint(center.x() + int(size*0.75), center.y() - int(size*0.75)),
            QPoint(center.x(), center.y() - size),
            QPoint(center.x() - int(size*0.75), center.y() - int(size*0.75)),
            QPoint(center.x() - size, center.y()),
            QPoint(center.x() - int(size*0.75), center.y() + int(size*0.75)),
            QPoint(center.x(), center.y() + size),
            QPoint(center.x() + int(size*0.75), center.y() + int(size*0.75))

        ]
        return QPolygon(points)

    def hidePolygon(self, pos):
        for polygon in self.polygons:
            if polygon['polygon'].containsPoint(pos, Qt.FillRule.OddEvenFill):
                polygon['visible'] = False
                self.update()

    def selectPolygon(self, pos):
        # Select polygon to move
        for i, polygon in enumerate(self.polygons):
            if polygon['visible'] and polygon['polygon'].containsPoint(pos, Qt.FillRule.OddEvenFill):
                self.selectedPolygon = i
                break

    def movePolygon(self, pos):
        # Move the selected polygon
        if self.selectedPolygon is not None:
            self.polygons[self.selectedPolygon]['center'] = pos
            self.polygons[self.selectedPolygon]['polygon'] = self.createPolygon(pos)
            self.update()

    def moveAllPolygons(self, pos):
        delta = pos - self.lastMousePosition
        self.lastMousePosition = pos

        for polygon in self.polygons:
            polygon['center'] = polygon['center'] + delta
            polygon['polygon'] = self.createPolygon(polygon['center'])
        
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)

        for polygon in self.polygons:
            if polygon['visible']:
                painter.setBrush(QColor(255, 0, 0, 150))  
                painter.drawPolygon(polygon['polygon'])


scaling = 3
class SpineTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Spine tracker')
        self.currentIndex = 0
        #set app attributes
        self.dataDir = userDir + '/SurvivalTracker/demo/withoutPreprocessing' ##### change this to your data dir
        self.checkMark = userDir + '/SurvivalTracker/UI/icons/check-mark-icon-vector.jpg'
        self.xMark = userDir + '/SurvivalTracker/UI/icons/x-mark-icon.jpg'
        self.miceAvailable = []
        self.currentMouse = None
        self.roisAvailable = []
        self.frames = []
        self.numROIs = np.zeros((1,1))
        self.offsetOccured = np.zeros((1,1))
        self.roiInfo = {} 
        self.saveDict = {}
        self.loadingDict = {}
        self.initUI()

    def initUI(self):
        #Defining Background
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        mainLayout = QVBoxLayout() #Top Down Approach
        centralWidget.setLayout(mainLayout)

        #organizational structure of the layout
        layer1 = QHBoxLayout()    #layer 1 = drop down selections
        layer2 = QHBoxLayout()    #layer 2 = image
        layer3 = QHBoxLayout()    # layer 3 = buttons to change frame

        mainLayout.addLayout(layer1)
        mainLayout.addLayout(layer2)
        mainLayout.addLayout(layer3)

        #At the top we place a drop down to select mouse
        self.mouseDropDown = QComboBox()
        layer1.addWidget(self.mouseDropDown)
        self.mouseDropDown.setCurrentIndex(0)
        self.mouseDropDown.currentIndexChanged.connect(self.loadROIs)

        self.roiDropDown = QComboBox()
        layer1.addWidget(self.roiDropDown)
        self.mouseDropDown.setCurrentIndex(0)
        self.roiDropDown.currentIndexChanged.connect(self.displayData)

        #Set up where the tif stacks will be displayed
        self.displayTiffHere = PDFLabel(QPixmap(100,100)) #setting a place holder
        self.displayTiffHere.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layer2.addWidget(self.displayTiffHere)

        #give app left right buttons
        self.leftButton = QPushButton('<',self)
        self.leftButton.clicked.connect(self.previousImage)
        layer3.addWidget(self.leftButton)
        self.rightButton = QPushButton('>', self)
        self.rightButton.clicked.connect(self.nextImage)
        layer3.addWidget(self.rightButton)

        #a button to save this timestamp's roi
        self.logLabels = QPushButton('Verify Labels', self)
        self.logLabels.clicked.connect(self.logLabelsToDict)
        mainLayout.addWidget(self.logLabels)

        #Exit button goes at the bottom
        exitButton = QPushButton('Exit')
        exitButton.clicked.connect(self.close)
        mainLayout.addWidget(exitButton)

        #Push a button to get a mouseID
        #button will find all avaliable ROIs, load them into a Queue (Queue will be a combo box)
        self.setFocus()
        self.loadData()
        print('UI Initialized')
    
    #populates roi choice dropdown
    def loadData(self):
        self.miceAvailable = []   
        self.mouseDropDown.clear()                                              #we want to reset the search for labels every time this funciton is called
        for mouseID in os.listdir(self.dataDir):
            mousePath = Path.joinpath(Path(self.dataDir), Path(mouseID))
            if os.path.exists(Path.joinpath(Path(mousePath), Path('labels'))) and os.path.isdir(mousePath):
                self.miceAvailable.append(
                    (mouseID, self.checkMark)                                   #mouse has been labeled
                )
            elif os.path.isdir(mousePath) and not os.path.exists(Path.joinpath(Path(mousePath), Path('labels'))):
                self.miceAvailable.append(
                    (mouseID, self.xMark)                                       #mouse has not been labeled
                )
            else:
                pass
        for mouseID, labelExistence in self.miceAvailable:                      #reload the info on each mouse
            icon = QIcon(QPixmap(labelExistence))
            self.mouseDropDown.addItem(icon, mouseID)

    #initiates display data as soon as dropdown is cleared 
    def loadROIs(self):
        selectedMouseIndex = self.mouseDropDown.currentIndex()
        self.currentMouse = self.miceAvailable[selectedMouseIndex]
        mouseFN = self.currentMouse[0]
        mousePath = Path.joinpath(Path(self.dataDir), Path( mouseFN))
        self.roiDropDown.clear()
        self.roisAvailable = []
        for roiNum in os.listdir(mousePath):
            if '.tif' in roiNum:                    #only display tiffs   
                roiLabel = roiNum.split('.')[0]     #    'roiNum'
                if os.path.exists(Path.joinpath(Path(mousePath), Path('labels'), Path(roiLabel))):
                    self.roisAvailable.append(
                        (roiNum, self.checkMark)
                    )
                else:
                    self.roisAvailable.append(
                        (roiNum, self.xMark)
                    )
        for roiID, labelExistence in self.roisAvailable:
            icon = QIcon(QPixmap(labelExistence))
            self.roiDropDown.addItem(icon, roiID)    

    #uses drop downs to construct a path that points to tif stacks (and loads stack)
    def displayData(self):
        currentStack = self.roiDropDown.currentText() 
        if len(currentStack)>0:                         # display data gets double called when we clear roi combo box
            roiPath = f'{self.dataDir}/{self.currentMouse[0]}/{currentStack}'
            
            try:
                with tiff.TiffFile(roiPath) as tif:
                    self.tiffStack = tif.asarray()
                    self.numROIs = np.zeros((self.tiffStack.shape[0],1))
                    self.offsetOccured = np.zeros((self.tiffStack.shape[0],1))
            except Exception as e:
                print(e)
                pass  
            self.updateImage()
    
    #display stack as a pixmap, maps each page as a temp pdf to a temp folder so that quick load occurs -- also limits image distortion when pdf-ed first
    def updateImage(self):
        self.displayTiffHere.setFocus()
        frame = self.tiffStack[self.currentIndex, :,:]
        frame = (frame / np.max(frame) * 255).astype(np.uint8)
        plt.imshow(frame, cmap='gray')
        plt.axis('off')
        plt.savefig('C:/temp/tempROI.pdf', format='pdf', bbox_inches='tight', pad_inches=0)
        plt.close()
        if not os.path.exists('C:/temp'):
            os.mkdir('C:/temp')
        frame = fitz.open('C:/temp/tempROI.pdf')
        page = frame.load_page(0)
        px = page.get_pixmap()
        qimage = QImage(px.samples, px.width, px.height, px.stride, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage).scaled(px.width * scaling, px.height*scaling, aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
        self.displayTiffHere.setPixmap(pixmap)
    
    def nextImage(self):
        if self.currentIndex < self.tiffStack.shape[0] - 1:
            self.currentIndex += 1
            self.updateImage()
            if self.numROIs[self.currentIndex,0] == 1:
                self.displayTiffHere.polygons = []
                for label in self.roiInfo[self.currentIndex]:
                    newPolyPos = QPoint(label['center'].x(), label['center'].y())
                    self.displayTiffHere.addPolygon(newPolyPos)
                    if label['visible'] == False:
                        self.displayTiffHere.hidePolygon(newPolyPos)
                self.displayTiffHere.update()
            else:
                self.displayTiffHere.polygons = []
                self.displayTiffHere.update()
    def keyPressEvent(self,event):
        k = event.key()
        txt = event.text()
        print(k, txt)
        if txt == 'w':
            previousIDX = self.currentIndex - 1
            for label in self.roiInfo[previousIDX]:
                newPolyPos = QPoint(label['center'].x(), label['center'].y())
                self.displayTiffHere.addPolygon(newPolyPos)
                if label['visible'] == False:
                    self.displayTiffHere.hidePolygon(newPolyPos)
                self.displayTiffHere.update()
            print('carry over')
        elif txt == 'a':
            self.previousImage()
        elif txt == 'd':
            self.nextImage()
        elif k == 32: #space
            print(self.saveDict)
            print('test')
            print(self.roiInfo)
            self.logLabelsToDict()
        elif k == 16777220: #enter
            self.saveAllLabels()
        elif k == 16777248: #shift
            self.offsetOccured[self.currentIndex] = 1
        elif txt =='r':
            self.roiInfo[self.currentIndex] = []
            self.numROIs[self.currentIndex,0] = 0
            self.nextImage()
            self.previousImage()
            self.displayTiffHere.update()
            print(self.saveDict)
            print('test')
            print(self.roiInfo)
    
    def saveAllLabels(self):
        #need to make QPoints serializable
        for t in self.roiInfo.keys():
            self.saveDict[t] = str(self.roiInfo[t])
        writePath = f'{self.dataDir}{self.mouseDropDown.currentText()}/labels'
        if not os.path.exists(writePath):
            os.mkdir(writePath)
            roiBase = writePath + f'/{self.roiDropDown.currentText()[:-4]}/'
            if not os.path.exists(roiBase):
                os.mkdir(roiBase)
                roiLabelPath = roiBase + f'/{self.roiDropDown.currentText()[:-4]}_labels.json'
                with open(roiLabelPath, 'w') as f:
                    json.dump(self.saveDict, f)
                print(self.saveDict)
            else:
                print('this roi has labels')
        else:
            print('Mouse has existing labels, checking if this roi has labels')
            roiBase = writePath + f'/{self.roiDropDown.currentText()[:-4]}/'
            if not os.path.exists(roiBase):
                os.mkdir(roiBase)
                roiLabelPath = roiBase + f'/{self.roiDropDown.currentText()[:-4]}_labels.json'
                with open(roiLabelPath, 'w') as f:
                    json.dump(self.saveDict, f)
                print(self.saveDict)
            else:
                print('this roi has labels')
        self.loadData()

    def previousImage(self):
        if self.currentIndex > 0:
            self.currentIndex -= 1
            self.updateImage()
            if self.numROIs[self.currentIndex,0] == 1:
                self.displayTiffHere.polygons = []
                for label in self.roiInfo[self.currentIndex]:
                    newPolyPos = QPoint(label['center'].x(), label['center'].y())
                    self.displayTiffHere.addPolygon(newPolyPos)
                    if label['visible'] == False:
                        self.displayTiffHere.hidePolygon(newPolyPos)
                self.displayTiffHere.update()
            else:
                self.displayTiffHere.polygons = []
                self.displayTiffHere.update()

    def logLabelsToDict(self):
        if len(self.displayTiffHere.polygons)>0:
            self.numROIs[self.currentIndex,0] = 1
            self.roiInfo[self.currentIndex] =  self.displayTiffHere.polygons
            self.displayTiffHere.polygons = []



if __name__=='__main__':
    app = QApplication(sys.argv)
    viewer = SpineTracker()
    viewer.showFullScreen()
    sys.exit(app.exec())


# %%
