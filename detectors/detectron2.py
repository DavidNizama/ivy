'''
Performs vehicle detection using models created with the YOLO (You Only Look Once) neural net.
https://pjreddie.com/darknet/yolo/
'''

import ast
import os
import cv2
import torch

import detectron2
from detectron2.utils.logger import setup_logger
setup_logger()

# import some common libraries
import numpy as np
import random

# import some common detectron2 utilities
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog

with open(os.getenv('DETECTRON2_CLASSES_PATH'), 'r') as classes_file:
    CLASSES = dict(enumerate([line.strip() for line in classes_file.readlines()]))
with open(os.getenv('DETECTRON2_CLASSES_OF_INTEREST_PATH'), 'r') as coi_file:
    CLASSES_OF_INTEREST = tuple([line.strip() for line in coi_file.readlines()])

use_gpu = ast.literal_eval(os.getenv('ENABLE_GPU_ACCELERATION'))
conf_threshold = float(os.getenv('DETECTRON2_CONFIDENCE_THRESHOLD'))

# # initialize model with weights and config
cfg = get_cfg()
cfg.merge_from_file(os.getenv('DETECTRON2_CONFIG_PATH'))
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5  # set threshold for this model
# Find a model from detectron2's model zoo. You can either use the https://dl.fbaipublicfiles.... url, or use the following shorthand
cfg.MODEL.WEIGHTS = os.getenv('DETECTRON2_WEIGHTS_PATH')
cfg.MODEL.ROI_HEADS.NUM_CLASSES = int(os.getenv('DETECTRON2_NUM_CLASSES'))  # only has one class (ballon)
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = float(os.getenv('DETECTRON2_CONFIDENCE_THRESHOLD'))
cfg.DATALOADER.NUM_WORKERS = 2

if not torch.cuda.is_available():
    print("No GPU available, using CPU")
    cfg.MODEL.DEVICE = 'cpu'
else:
    print("GPU Available, using GPU")
    cfg.MODEL.DEVICE = 'cuda'

predictor = DefaultPredictor(cfg)

def convert_box_to_array(this_box):
    res = []
    for val in this_box:
        for ind_val in val:
            res.append(float(ind_val))

    # Convert x2, y2 into w, h
    res[2] = res[2] - res[0]
    res[3] = res[3] - res[1]
    return res

def get_bounding_boxes(image):
    '''
    Return a list of bounding boxes of vehicles detected,
    their classes and the confidences of the detections made.
    '''
    try:
      outputs = predictor(image)
    except Exception as e:
      print(e)

    _classes = []
    _confidences = []
    _bounding_boxes = []

    for i, pred in enumerate(outputs["instances"].pred_classes):
        coco_class = int(pred)
        class_string = CLASSES[coco_class]
        _classes.append(class_string)

        score = round(float(outputs['instances'].scores[i]), 3)
        _confidences.append(score)


        this_box = outputs['instances'].pred_boxes[i]
        box_vals = convert_box_to_array(this_box)
        _bounding_boxes.append(box_vals)

    return _bounding_boxes, _classes, _confidences