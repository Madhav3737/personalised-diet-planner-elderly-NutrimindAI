FROM node:20-alpine

WORKDIR /app

COPY package.json .

RUN npm install

COPY . .

EXPOSE 3000

# Start Vite dev server exposing hosts
CMD ["npm", "run", "dev", "--", "--host"]
