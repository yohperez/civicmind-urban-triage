# Build multi-stage: instala deps, compila con Vite (VITE_API_URL se fija
# en tiempo de build, ver src/api.js) y sirve el resultado con `vite preview`
# para desarrollo local vía docker-compose. En Railway se sigue usando el
# flujo estático descrito en frontend/DEPLOY.md, no esta imagen.

FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=build /app/dist ./dist
COPY --from=build /app/package.json ./package.json
RUN npm install -g vite
EXPOSE 4173
CMD ["vite", "preview", "--host", "0.0.0.0", "--port", "4173"]
