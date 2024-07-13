# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory to /app
WORKDIR /facial-server

# Copy the current directory contents into the container at /app
COPY . /facial-server

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 5031

# Run app.py when the container launches
CMD ["python", "app.py"]
