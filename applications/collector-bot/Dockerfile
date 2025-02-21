# Use the official Node.js image as the base image
FROM node:23.6.0

# Install system packages
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    sox \
    && rm -rf /var/lib/apt/lists/*

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Command to run the application
CMD [ "node", "index.js" ]