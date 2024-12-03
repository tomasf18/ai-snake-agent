#!/bin/bash

TERMINAL="gnome-terminal"

COMMAND="source venv/bin/activate && python3"
APP=("server.py" "viewer.py" "student.py")

for i in {1..3}; do
    case $TERMINAL in
        gnome-terminal)
            gnome-terminal -- bash -c "$COMMAND ${APP[$i-1]}; exec bash"
            ;;
    esac
done
