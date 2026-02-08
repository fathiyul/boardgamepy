FROM node:20-slim
WORKDIR /app
COPY webapp/frontend/package*.json /app/
RUN npm install
COPY webapp/frontend /app
ENV HOST=0.0.0.0
EXPOSE 8080
CMD ["sh", "-c", "VITE_API_URL=${VITE_API_URL} npm run dev -- --host 0.0.0.0 --port ${PORT:-8080}"]
