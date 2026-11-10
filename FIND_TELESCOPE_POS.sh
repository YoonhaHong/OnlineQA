#!/bin/bash

source "$(dirname "$0")/setup.sh" #Load the setup script to set environment variables(corry path, etc.))
#CORRY=/home/aliceits/Testbeam/corryvreckan/bin/corry
RAW_FILE_PATH=$1
OUTPUT_NAME=telescope_$(basename "$1" .raw)
DETECTOR_FILE=../geometry/ALPIDE.conf

$CORRY -c ./configs/prealign.conf -o detectors_file=$DETECTOR_FILE -o EventLoaderEUDAQ2.file_name=$RAW_FILE_PATH -o detectors_file_updated=../updated/prealigned.conf 

python3 plot_alpide.py ./output/prealignment_run_test.root --canvastitle=$OUTPUT_NAME --output=./output/$OUTPUT_NAME