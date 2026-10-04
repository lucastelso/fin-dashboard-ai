
# ESTÁGIO 1: COMPILAÇÃO - Node 22
FROM node:22-alpine AS builder

WORKDIR /app

COPY package*.json ./

RUN npm ci 

COPY . .
RUN npm run build

# ESTÁGIO 2: PRODUÇÃO (Nginx Otimizado)
FROM nginx:alpine

# Remove o default do nginx para evitar conflitos
RUN rm -rf /usr/share/nginx/html/*

# Copia do builder
COPY --from=builder /app/dist /usr/share/nginx/html/dashboard-financeiro

# CRIA O NGINX DIRETO PELO DOCKERFILE
RUN cat <<'EOF' > /etc/nginx/conf.d/default.conf
server {
    listen 80;
    server_tokens off; # Segurança: Oculta a versão do Nginx

    root /usr/share/nginx/html;

    # Otimização de I/O de rede (Compressão)
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml application/json;

    # Headers de Segurança
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-XSS-Protection "1; mode=block";
    add_header X-Content-Type-Options "nosniff";

    location = / {
        return 301 /dashboard-financeiro/macro;
    }

    # Como eles nunca mudam, deixar o navegador cachear por 1 ano kkkkkk
    location /dashboard-financeiro/assets {
        expires 1y;
        add_header Cache-Control "public, max-age=31536000, immutable";
        access_log off;
    }

    location /dashboard-financeiro {
        index index.html;
        # Evita cache do index.html para garantir que a versão mais nova da UI seja baixada
        add_header Cache-Control "no-store, no-cache, must-revalidate";
        try_files $uri $uri/ /dashboard-financeiro/index.html;
    }
}
EOF

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]