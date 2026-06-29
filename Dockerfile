# Imagen base de Node.js ligera
FROM node:20-slim

# Instalar dependencias de sistema necesarias para Python y OpenCV
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /app

# Copiar package.json e instalar dependencias de Node.js
COPY package*.json ./
RUN npm install

# Copiar archivo de requerimientos e instalar dependencias de Python
COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt --break-system-packages

# Copiar todo el código del backend
COPY . .

# Definir variables de entorno de producción
ENV NODE_ENV=production
ENV PORT=3000

# Exponer puerto
EXPOSE 3000

# Comando de arranque del servidor Hono
CMD ["npm", "start"]
