FROM python:3.12-slim

# Install cron
RUN apt-get update && apt-get -y install cron

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

# Make port 8501 available to the world outside this container
EXPOSE 8501

# Define environment variable for Streamlit
ENV STREAMLIT_SERVER_PORT 8501

# Copy crontab file
COPY crontab /etc/crontab

# Set shell
SHELL ["/bin/bash", "-c"]

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh

# Change permissions for the entrypoint script
RUN chmod +x /app/entrypoint.sh

# Run entrypoint script when the container launches
CMD ["/bin/bash", "/app/entrypoint.sh"]
