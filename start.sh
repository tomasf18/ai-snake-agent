#!/bin/bash

TERMINAL="gnome-terminal"

if [ -z "$1" ]; then
    SEED=$RANDOM
else
    SEED=$1
fi

COMMAND="source venv/bin/activate && python3"
APP=("server.py --seed $SEED" "viewer.py" "student.py")

for i in {1..3}; do
    case $TERMINAL in
        gnome-terminal)
            gnome-terminal -- bash -c "$COMMAND ${APP[$i-1]}; exec bash"
            ;;
    esac
done

echo "Chosen seed was $SEED"