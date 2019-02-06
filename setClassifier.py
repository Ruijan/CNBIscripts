import argparse
from appJar import gui
from screeninfo import get_monitors
import getpass
import sys
from os import walk
import xml.etree.ElementTree as ET
import scipy.io as sio
import numpy as np
import pandas as pd


global app
global data
global dataDouble
global dataSingle
global fileName


parser = argparse.ArgumentParser()
parser.add_argument(
    "--modality", help="For which modality you are setting classifier path", required=True)
parser.add_argument(
    "--subject",    help="For which subject you are setting classifier path", required=True)
parser.add_argument(
    "--taskset",    help="For which tasket you are setting threshold values", required=True)


args, unknown = parser.parse_known_args()
modality = args.modality
subject = args.subject
taskset = args.taskset
movementClass = taskset.replace('_fes', '').replace('mi_', '').replace('rst','')
user = getpass.getuser()
path = "/home/" + user + "/data/Sinergia/" + subject + "/"
REST_EVENT = 782
FLEXION_EVENT = 783
EXTENSION_EVENT = 784
OLD_EXTENSION_EVENT = 781


def chooseClassifier(button):
    global app
    if button == "Validate":
        xmlFile = path + "/mi_stroke_prot.xml"
        tree = ET.parse(xmlFile)
        root = tree.getroot()
        root.find('classifier').find('kmi2').find(
            'filename').text = app.getRadioButton("classifier")
        tree.write(xmlFile)
        app.showSubWindow('Threshold')
        app.hide()
    elif button == "Cancel":
        print(str(-1))
        app.stop()


def chooseValues(button):
    global app
    if button == "Set":
        thresholdMovement = str(app.getEntry("Threshold Movement")) if app.getEntry(
            "Threshold Movement") is not None else task.find('threshold').find(movementClass).text
        thresholdRest = str(app.getEntry("Threshold Rest")) if app.getEntry(
            "Threshold Rest") is not None else task.find('threshold').find('mi_rest').text
        setThresholdValues(thresholdMovement, thresholdRest)
    elif button == "Auto Set":
        defineThresholds()
    elif button == "Exit":
        print(str(-1))
    app.stop()


def defineThresholds():
    probaPath = "/home/" + user + "/dev/shamBCIFESData/Data/" + subject
    rejectedProbaPath = "/home/" + user + "/dev/shamBCIFESData/Data/Rej"
    lastDateRejected = 19700101
    lastDateAccepted = 19700101
    lastRejectedRun = getLatestFileInFolder(
        rejectedProbaPath, subject, movementClass, '.mat')
    lastAcceptedRun = getLatestFileInFolder(
        probaPath, subject, movementClass, '.mat')
    lastThreshold = 0
    print(lastAcceptedRun["date"] )
    print(lastRejectedRun["date"] )
    if lastAcceptedRun["date"] > lastRejectedRun["date"]:
        lastRun = lastAcceptedRun
    else:
        lastRun = lastRejectedRun
    threshold = getThresholdsFromPreviousRun()
    data = sio.loadmat(lastRun["folder"] + "/" + lastRun["file"])
    successfulMovements = [data["success"][i][0] for i, val in enumerate(data["rLabels"].tolist()) if (val[0]==FLEXION_EVENT or val[0]==EXTENSION_EVENT or val[0]==OLD_EXTENSION_EVENT)]
    successfulRests = [data["success"][i][0] for i, val in enumerate(data["rLabels"].tolist()) if (val[0]==REST_EVENT)]
    successRateMovement = sum(successfulMovements)/len(data["success"]) * 100
    successRateRest = sum(successfulRests)/len(data["success"]) * 100
    threshold["movement"] = getNewThreshold(threshold["movement"], successRateMovement)
    threshold["rest"] = getNewThreshold(threshold["rest"], successRateRest)
    setThresholdValues(threshold["movement"], threshold["rest"])


def getNewThreshold(threshold, successRate):
    newThreshold = threshold
    if successRate > 80:
        newThreshold += 0.05
    elif successRate < 70:
        newThreshold -= 0.05
    return newThreshold


def setThresholdValues(thresholdMovement, thresholdRest):
    xmlFile = path + "/mi_stroke_prot.xml"
    tree = ET.parse(xmlFile)
    root = tree.getroot()
    tasksets = root.find('online').find('mi').findall('taskset')

    for task in tasksets:
        if task.attrib['ttype'] == taskset:
            task.find('threshold').find(movementClass).text = thresholdMovement
            task.find('threshold').find('mi_rest').text = thresholdRest
    tree.write(xmlFile)


def getLatestFileInFolder(folder, subject, movement, extension):
    lastDate = 19700101
    lastFile = ''
    lastRun = dict()
    for (dirpath, dirnames, filenames) in walk(folder):
        for fileName in filenames:
            fileInfos = fileName.split('.')
            if len(fileInfos) > 2 and extension in fileName:
                fileDate = int(fileInfos[1])
                if lastDate < fileDate and fileInfos[0] == subject and movement in fileName:
                    lastDate = int(fileInfos[1])
                    lastFile = fileName
    lastRun["file"] = lastFile
    lastRun["folder"] = folder
    lastRun["date"] = lastDate
    return lastRun


def getThresholdsFromPreviousRun():
    threshold = {"movement": 0.75, "rest": 0.75}
    lastRun = {"file": "", "date": 19700101, "folder": ""}
    for (dirpath, dirnames, filenames) in walk(path):
        for directory in dirnames:
            if 'eegc3' not in directory:
                lastRunInDirectory = getLatestFileInFolder(
                    path + directory, subject, movementClass, '.gdf')
                if lastRunInDirectory["date"] > lastRun["date"]:
                    lastRun = lastRunInDirectory
    xmlFile = lastRun["folder"] + "/mi_stroke_prot.xml"
    tree = ET.parse(xmlFile)
    root = tree.getroot()
    tasksets = root.find('online').find('mi').findall('taskset')
    for task in tasksets:
        if task.attrib['ttype'] == taskset:
            threshold["movement"] = task.find(
                'threshold').find(movementClass).text
            threshold["rest"] = task.find(
                'mi_rest').find(movementClass).text
    return threshold


if modality == "online":
    user = getpass.getuser()
    path = "/home/" + user + "/data/" + subject + "/"
    f = []
    for (dirpath, dirnames, filenames) in walk(path):
        for filename in filenames:
            if ".mat" in filename and ".smr.mat" not in filename:
                f.append(filename)
        break

    # # # app.go
    sys.argv = [sys.argv[0]]
    padding = 10
    app = gui()
    user = getpass.getuser()
    path = "/home/" + user + "/data/" + subject + "/"
    xmlFile = path + "/mi_stroke_prot.xml"
    tree = ET.parse(xmlFile)
    root = tree.getroot()
    app.startSubWindow("Threshold")
    app.setGuiPadding(padding, padding)
    app.addLabelNumericEntry("Threshold Movement")
    app.addLabelNumericEntry("Threshold Rest")
    tasksets = root.find('online').find('mi').findall('taskset')
    for task in tasksets:
        if task.attrib['ttype'] == taskset:
            app.setEntryDefault("Threshold Movement", task.find(
                'threshold').find(movementClass).text)
            app.setEntryDefault("Threshold Rest", task.find(
                'threshold').find('mi_rest').text)
    app.addButtons(["Set", "Auto Set", "Exit"], chooseValues)
    app.setLocation(500, 450)
    app.stopSubWindow()

    app.setGuiPadding(padding, padding)
    for filename in f:
        app.addRadioButton("classifier", filename)
    app.addButtons(["Validate", "Cancel"], chooseClassifier)
    app.setLocation(500, 450)
    app.go()
