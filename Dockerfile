# Use the official Playwright Python image
FROM mcr.microsoft.com/playwright/python:v1.57.0-jammy

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (Chromium is needed)
RUN playwright install chromium

# Copy the rest of the app
COPY . .

# Expose the port your FastAPI app will run on
EXPOSE 10000

# Run FastAPI with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
