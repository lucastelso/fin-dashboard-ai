# Estágio 1: Compilação (Builder)
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Estágio 2: Produção (Runner)
FROM nginx:alpine

# ALINHAMENTO FÍSICO: Copiando o build para dentro de uma pasta com o nome exato 
# que foi configurado no "base" do Vite e no "basename" do React Router.
COPY --from=builder /app/dist /usr/share/nginx/html/dashboard-financeiro

# CONFIGURAÇÃO OTIMIZADA DO NGINX
RUN cat <<'EOF' > /etc/nginx/conf.d/default.conf
server {
    listen 80;
    
    # Define o diretório base global
    root /usr/share/nginx/html;
    
    # REGRA 1: Redireciona quem acessar a raiz do servidor (http://localhost/)
    location = / {
        return 301 /dashboard-financeiro/macro;
    }

    # REGRA 2: Serve os arquivos do React e delega o roteamento
    location /dashboard-financeiro {
        index index.html;
        
        # Tenta achar o arquivo. Se não achar, joga para o index.html DAQUELA pasta.
        try_files $uri $uri/ /dashboard-financeiro/index.html;
    }
}
EOF

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]