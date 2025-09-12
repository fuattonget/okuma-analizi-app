FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json pnpm-lock.yaml* ./

# Install dependencies
RUN if [ -f pnpm-lock.yaml ]; then \
        npm install -g pnpm && pnpm install; \
    else \
        npm install; \
    fi

# Install additional packages
RUN npm install next@latest react@latest react-dom@latest axios zustand classnames

# Copy source code
COPY . .

# Set environment variable
ENV NEXT_PUBLIC_API_BASE=http://localhost:8000

# Expose port
EXPOSE 3000

# Start the application
CMD ["npm", "run", "dev"]


