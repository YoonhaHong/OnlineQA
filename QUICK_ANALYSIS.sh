#!/bin/bash

source "$(dirname "$0")/setup.sh" # change to autoresolve for alignment or efficiency  #Load the setup script to set environment variables(corry path, etc.))
#CORRY=/home/aliceits/Testbeam/corryvreckan/bin/corry
RAW_FILE_PATH=$1
OUTPUT_NAME=analyse_$(basename "$1" .raw)
DETECTOR_FILE=$DETECTOR_DIR/UTA110.conf
ALIGNED_GEOMETRY_PATH=../updated/dut_aligned.conf

$CORRY -c ./configs/createmask.conf -o detectors_file=$DETECTOR_FILE -o EventLoaderEUDAQ2.file_name=$RAW_FILE_PATH -o detectors_file_updated=../updated/masked.conf 
$CORRY -c ./configs/prealign.conf -o detectors_file=../updated/masked.conf -o EventLoaderEUDAQ2.file_name=$RAW_FILE_PATH -o detectors_file_updated=../updated/prealigned.conf 
$CORRY -c ./configs/align.conf -o detectors_file=../updated/prealigned.conf -o EventLoaderEUDAQ2.file_name=$RAW_FILE_PATH -o detectors_file_updated=../updated/aligned.conf
$CORRY -c ./configs/align_dut.conf -o detectors_file=../updated/aligned.conf -o EventLoaderEUDAQ2.file_name=$RAW_FILE_PATH -o detectors_file_updated=$ALIGNED_GEOMETRY_PATH

echo "Aligned geometry file is saved at $ALIGNED_GEOMETRY_PATH"

$CORRY -c ./configs/analyse.conf -o detectors_file=$ALIGNED_GEOMETRY_PATH \
                                -o EventLoaderEUDAQ2.file_name=$RAW_FILE_PATH \
                                -o histogram_file=$OUTPUT_NAME.root \
                                -o Tracking4D.momentum=10GeV \
                                -o OnlineMonitor.canvas_title=$OUTPUT_NAME\