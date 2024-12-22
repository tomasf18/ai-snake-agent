#!/bin/bash

TERMINAL="gnome-terminal"

if [ -z "$1" ]; then
    SEED=$RANDOM
else
    SEED=$1
fi

COMMAND="source venv/bin/activate"

# Server
gnome-terminal -- bash -c "$COMMAND; python3 server.py --seed $SEED; exec bash"

# Viewer
gnome-terminal -- bash -c "$COMMAND; python3 viewer.py; exec bash"

# Clients 
gnome-terminal -- bash -c "$COMMAND;SEED=$SEED python3 student.py; exec bash"

echo "Chosen seed was $SEED"


echo test 27393