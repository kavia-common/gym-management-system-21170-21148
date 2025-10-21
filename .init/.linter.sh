#!/bin/bash
cd /home/kavia/workspace/code-generation/gym-management-system-21170-21148/gym_backend_api
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

