#!/bin/sh
service cron start
crontab /app/crontab
streamlit run main.py