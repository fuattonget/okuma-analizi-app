FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source code
COPY frontend/ .

# Set environment variable
ENV NEXT_PUBLIC_API_BASE=http://localhost:8000

# Expose port
EXPOSE 3000

# Start the application
CMD ["npm", "run", "dev"]



