  
import json
import os
import ctypes
import numpy as np
import cv2 as cv
import time

from emioapi import EmioCamera

from enum import Enum
import DarkHelp

from module.loggerconfig import getLogger
logger = getLogger()


class Classes(Enum):
    """
    Enum to define the classes of the objects detected by the YOLO model
    """
    DOG = 0
    CAT = 1
    EMPTY = 2
    HAND = 3


def getDarkHelpClassificationModel():
    """
    Create and initialize the DarkHelp classification model
    """
    base_path = os.path.dirname(__file__)
    cfg_path = os.path.join(base_path, 'model.cfg')
    names_path = os.path.join(base_path, 'classes.names')
    weights_path = os.path.join(base_path, 'model.weights')
    dh = DarkHelp.CreateDarkHelpNN(cfg_path.encode("utf-8"), names_path.encode("utf-8"), weights_path.encode("utf-8")) 
    DarkHelp.SetThreshold(dh, 0.35)
    DarkHelp.SetAnnotationLineThickness(dh, 1)
    DarkHelp.EnableTiles(dh, True)
    DarkHelp.EnableCombineTilePredictions(dh, True)
    DarkHelp.EnableOnlyCombineSimilarPredictions(dh, False)
    DarkHelp.SetTileEdgeFactor(dh, 0.)
    DarkHelp.SetTileRectFactor(dh, 1.)
    return dh


class DHResults:
    """
    Class that handle the DarkHelp prediction and put them in an easy to use format
    """
    def __init__(self):
        self.xydwh = []     # list of [x, y, d, w, h], 
                           # x and y are the center of the bounding box, 
                           # d is the median depth
                           # w is the width and h is the height of the bounding box
        self.conf = []     # list of confidence
        self.cls  = []     # list of classes (what we detect on the image), 
                           # 0: dog, 1: cat, 2: empty, 3: hand

        self.dh = getDarkHelpClassificationModel()

        #hand detection
        self.handDetectedTime = 0 # time in seconds
        self.handDetectedTimer = 2 # seconds

        # Initialize the camera
        self.camera = EmioCamera(show=False, track_markers=True, compute_point_cloud=False)
        try:
            self.camera.open()
        except Exception as e:
            logger.error(f"Error opening camera: {e}")


    def __del__(self):
        self.camera.close()


    def getFrame(self):
        """
        Access the last frame of the camera
        Wait for a coherent pair of frames: depth and color
        
        Return:
        -----------
        state           : bool. True if the depth image and RGB image are correctly received; False otherwise.
        color_image     : numpy.ndarray. The color image returned by the camera
        depth_image     : numpy.ndarray. The depth image returned by the camera
        """

        self.camera.update()
        depth_frame = self.camera.depth_frame
        color_frame = self.camera.frame
     
        if depth_frame is None or color_frame is None:
            logger.error('Problem with accessing the frames.')
            return color_frame, depth_frame

        return color_frame, depth_frame
    

    def getProcessedImages(self):
        """
        Get images from camera and applies an ROI on it 
        """
        color_image, depth_image = self.getFrame()

        masked_image = None
        if color_image is not None:
            mask = np.zeros(color_image.shape[:2], dtype="uint8")
            cv.rectangle(mask, (30, 30), (400, 450), 255, -1)
            masked_image = cv.bitwise_and(color_image, color_image, mask=mask)

        return color_image, masked_image, depth_image


    def updateAndDisplayAnnotatedImage(self, extra=True):
        color_image, _ = self.update()
        self.displayAnnotatedImage(color_image, extra=extra)


    def checkConsistency(self, cls_list):
        """
            Check consistency in prediction results: same results over n consecutive number of frame
        """
        nbFrames = 3
        if len(cls_list) < nbFrames:
            return False
        
        while len(cls_list) > nbFrames:
            cls_list.pop(0) 

        for i in range(nbFrames-1):
            if (cls_list[i] == Classes.CAT.value).sum() != (cls_list[i] == Classes.CAT.value).sum():
                return False
            
            if (cls_list[i] == Classes.DOG.value).sum() != (cls_list[i] == Classes.DOG.value).sum():
                return False

        return True


    def update(self):
        """
        Update the value of the predictions
        """

        cls_list = []

        while not self.checkConsistency(cls_list): 
            self.xydwh = []     
            self.conf = []       
            self.cls  = []  

            color_image, masked_image, depth_image = self.getProcessedImages()
            if color_image is None:
                continue

            image_data = np.ascontiguousarray(masked_image, dtype=np.uint8)

            # Update the model prediction
            DarkHelp.Predict(self.dh, 640, 480, 
                            image_data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)),
                            640*480*3)
            
            json_string = DarkHelp.GetPredictionResults(self.dh)
            data = json.loads(json_string)

            # Store the information in a easy to use (looking like YOLO standard) object
            size=int(data['file'][0]['count'])

            for i in range(size):
                self.cls.append(data['file'][0]['prediction'][i]['best_class'])
                self.conf.append(data['file'][0]['prediction'][i]['best_probability'])
                x=data['file'][0]['prediction'][i]['rect']['x']
                y=data['file'][0]['prediction'][i]['rect']['y']
                w=data['file'][0]['prediction'][i]['rect']['width']
                h=data['file'][0]['prediction'][i]['rect']['height']
                x=x+w/2
                y=y+h/2

                x1 = max(0, int(x - w / 2))
                y1 = max(0, int(y - h / 2))
                x2 = min(depth_image.shape[1], int(x + w / 2))
                y2 = min(depth_image.shape[0], int(y + h / 2))
                depth_values = depth_image[y1:y2, x1:x2].flatten()
                d = np.median(depth_values[depth_values > 0])
    
                self.xydwh.append([x,y,d,w,h])

            self.cls  = np.array(self.cls)
            self.conf = np.array(self.conf)
            self.xydwh = np.array(self.xydwh)
            cls_list.append(self.cls)

        return color_image, depth_image
    

    def displayAnnotatedImage(self, color_image=None, extra=False):
        """
        Display the bounding boxes, the labels and the confidences
        Parameters:
        -----------
        color_image        : numpy.ndarray. The color image used for the prediction
        extra              : bool. If True, display the class and the confidence on the annotated image
        """

        if color_image is None:
            color_image = self.camera.frame
        if color_image is None:
            return

        class_color = [[0, 0, 255],   # red for dog
                       [0, 255, 0],   # green for cat
                       [0, 255, 255], # yellow for empty
                       [96, 48, 176]] # purple for hand
        
        annoted_image = color_image.copy()
        for (box, conf, cls) in zip(self.xydwh, self.conf, self.cls):
            x, y, _, w, h = map(int, box)
            label = f"{cls}: {conf:.2f}"
            
            # Draw the bounding boxes
            cv.rectangle(annoted_image, 
                         (int(x - w/2), int(y - h/2)), 
                         (int(x + w/2), int(y + h/2)), 
                         class_color[cls], 
                         1)

            if extra:
                cv.putText(annoted_image, label, (x, y - 2), cv.FONT_HERSHEY_SIMPLEX, 0.3, class_color[cls], 1)
        cv.imshow("Tic Tac Toe", annoted_image)
        cv.waitKey(1)

        return
    

    def isHandDetected(self):
        """
        Check if a hand is detected in the field of view

        Parameters:
        -----------
        dhresults : DHResults. The prediction of the YOLO model

        Return:
        -----------
        True if a hand is detected, False otherwise
        """
        cls = self.cls
        for i in range(len(cls)):
            if cls[i] == Classes.HAND.value:
                logger.debug("Hand detected.")
                self.handDetectedTime = time.time()
                self.handDetectedTimer = 2 # reset the timer
                return True

        # The detection of the hand is not stable
        # So we set a timer when detected
        if self.handDetectedTime > 0:
            timeElapsed = time.time() - self.handDetectedTime 
            if timeElapsed < self.handDetectedTimer:
                self.handDetectedTimer -= timeElapsed
                return True
            
        if self.handDetectedTimer <= 0:
            self.handDetectedTime = 0
            return False
            
        return False

