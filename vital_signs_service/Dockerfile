# Use official Node.js image
FROM node:22-alpine

# Set working directory
WORKDIR /usr/src/app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy application source code
COPY . .

# Expose port used by the app
EXPOSE 5001

# Start the Node.js server
CMD ["node", "vital_signs.js"]
