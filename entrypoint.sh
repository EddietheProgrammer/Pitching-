#!/bin/bash
service cron start
crontab /etc/crontab
streamlit run main.py