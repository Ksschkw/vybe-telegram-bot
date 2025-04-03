#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Start the bot (with nohup to keep running)
nohup python bot/bot.py &