FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy only requirements first (for efficient Docker caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port your app runs on (if applicable)
EXPOSE 8000

# Default command to run your app (adjusted to run main.py as requested)
CMD ["python", "main.py"]
