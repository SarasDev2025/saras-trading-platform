# Step 1: Build the app
FROM node:20-alpine AS builder

WORKDIR /app

COPY . .

RUN npm install
RUN npm run build

# Step 2: Serve it with Vite preview
FROM node:20-alpine

WORKDIR /app

COPY --from=builder /app /app

RUN npm install -g vite serve

EXPOSE 3000

CMD ["vite", "preview", "--port", "3000", "--host"]
