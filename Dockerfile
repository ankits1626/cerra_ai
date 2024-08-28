FROM python:3.12-slim

# Add wait-for-it script
ADD https://raw.githubusercontent.com/vishnubob/wait-for-it/master/wait-for-it.sh /usr/local/bin/wait-for-it
RUN chmod +x /usr/local/bin/wait-for-it

# Install dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    build-essential \
    pkg-config \
    libhdf5-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Increase pip's default timeout and retries to prevent timeout errors
#required for tensorflow
RUN pip config set global.timeout 120
RUN pip config set global.retries 5

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt # incase want to force reinstall pips
RUN pip install -r requirements.txt

# Copy the application code
COPY . .

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003",  "--reload"]
