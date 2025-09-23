# Usar Python 3.9 como imagen base
   FROM python:3.9-slim

   # Establecer el directorio de trabajo
   WORKDIR /app

   # Instalar dependencias del sistema si son necesarias
   RUN apt-get update && apt-get install -y \
       gcc \
       && rm -rf /var/lib/apt/lists/*

   # Copiar requirements.txt primero para aprovechar el cache de Docker
   COPY requirements.txt .

   # Instalar dependencias de Python
   RUN pip install --no-cache-dir -r requirements.txt

   # Copiar el código de la aplicación
   COPY . .

   # Crear directorio para la base de datos si no existe
   RUN mkdir -p data

   # Exponer el puerto que usa Flask (por defecto 5000)
   EXPOSE 5000

   # Variables de entorno para Flask
   ENV FLASK_APP=app.py
   ENV FLASK_RUN_HOST=0.0.0.0
   ENV FLASK_ENV=production

   # Comando para ejecutar la aplicación
   CMD ["python", "app.py"]