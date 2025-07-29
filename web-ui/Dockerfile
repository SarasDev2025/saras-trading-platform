# Use Node.js image
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy rest of the source
COPY . .

# Copy .env explicitly
COPY .env .env

# Build the SvelteKit app
RUN npm run build

# Expose the app port (default for adapter-node is 3000)
EXPOSE 3000

# Run the SvelteKit app
CMD ["node", "build"]
