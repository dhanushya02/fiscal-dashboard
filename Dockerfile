# Use a lightweight Python environment
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Install the necessary Python libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy our dashboard code into the container
COPY app.py .

# Open the port Streamlit uses
EXPOSE 8501

# Start the dashboard
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]