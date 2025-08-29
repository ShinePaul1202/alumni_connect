#!/bin/bash

# Ask for commit message
echo "Enter commit message:"
read msg

# Git commands
git add .
git commit -m "$msg"
git push
