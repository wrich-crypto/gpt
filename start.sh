#!/bin/bash

# Change the directory to the absolute path where the main.py program is located
cd /home/ec2-user/gpt_python/gpt

# Start the program with an alias and redirect the standard output to a log file
python3.8 gpt_main.py >> output.log 2>&1 &

# Give the program some time to start up
sleep 2

# Print a message to confirm that the program has started
echo "gpt_main started"
