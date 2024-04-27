#!/bin/bash
service cron start
crontab /app/crontab
streamlit run main.py