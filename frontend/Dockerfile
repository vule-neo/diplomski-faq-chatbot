# --- stage 1: build ---
FROM node:24-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci                 # kao npm install, ali strogo po lock fajlu
COPY . .
RUN npm run build


FROM nginx:alpine
# kopiraj gotov sajt iz stage 1 u nginx-ov folder:
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
# kopiraj nasu nginx konfiguraciju (napravicemo je u sljedecem koraku):
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80