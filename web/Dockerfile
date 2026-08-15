FROM node:24-slim

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npx", "next", "dev", "-p", "3000", "-H", "0.0.0.0"]
