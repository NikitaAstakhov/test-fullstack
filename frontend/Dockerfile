FROM node:24-alpine AS builder
WORKDIR /app

COPY package.json package-lock.json ./
COPY tsconfig.json vite.config.ts ./

RUN npm ci

COPY ./src ./src
COPY index.html ./

RUN npm run build


FROM nginx:stable-alpine

RUN rm -rf /usr/share/nginx/html/*

COPY --from=builder /app/dist /usr/share/nginx/html

COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]