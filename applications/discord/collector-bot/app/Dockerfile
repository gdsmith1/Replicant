# Use the official Node.js image as the base image
FROM node:23.6.0

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Command to run the application
CMD [ "node", "index.js" ]