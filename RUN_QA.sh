#!/bin/bash

source "$(dirname "$0")/setup.sh" #Load the setup script to set environment variables(corry path, etc.))
RAW_FILE_PATH=$1
OUTPUT_NAME=QA_$(basename "$1" .raw)
#DETECTOR_FILE=$DETECTOR_DIR/ALPIDE.conf

DETECTOR_FILE=$DETECTOR_DIR/UTA100.conf
CONFIG_FILE=./configs/QA.conf 
#CONFIG_FILE=./configs/QA_shifttrg.conf #Shift trigger for continuous readout

echo $OUTPUT_NAME

$CORRY -c $CONFIG_FILE -o detectors_file=$DETECTOR_FILE \
                            -o EventLoaderEUDAQ2.file_name=$RAW_FILE_PATH\
                            -o histogram_file=$OUTPUT_NAME.root \
                            -o OnlineMonitor.canvas_title=$OUTPUT_NAME\
