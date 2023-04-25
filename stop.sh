#!/bin/bash

# Get the process ID of the program by its alias
PID=$(pgrep -f "gpt_main")

# Check if the program is running
if [ -z "$PID" ]; then
    echo "my_program is not running"
else
    # Terminate the program
    kill $PID
    echo "my_program stopped"
fi
