FROM python:3.12-slim

# Set working directory first
WORKDIR /code

# Copy only requirements first for better layer caching
COPY requirements.txt .

# Install dependencies (langchain-community already in requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose the app port
EXPOSE 8000

# Use CMD instead of RUN for the startup command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

