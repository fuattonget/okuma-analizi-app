FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source code
COPY frontend/ .

# Expose port
EXPOSE 3000

# Start the application
CMD ["npm", "run", "dev"]


