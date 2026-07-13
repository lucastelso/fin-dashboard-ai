# Estágio 1: Compilação (Builder)
FROM node:20-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Estágio 2: Produção (Runner)
FROM nginx:alpine
# Copia os arquivos estáticos compilados para a pasta padrão do Nginx
COPY --from=builder /app/dist /usr/share/nginx/html
# Copia a configuração customizada do Nginx para lidar com as rotas do React (SPA)
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]