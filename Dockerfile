# Usar una imagen más liviana para producción
FROM python:3.9-slim

# Establecer el directorio de trabajo
WORKDIR /app

# Copiar los archivos de la aplicación al contenedor
COPY . /app

# Instalar las dependencias necesarias
RUN pip install --no-cache-dir -r requirements.txt

# Definir variables de entorno para producción
ENV FLASK_ENV=production
ENV FLASK_APP=app.py

# Exponer el puerto en el que la app Flask escuchará
EXPOSE 5000

# Ejecutar Gunicorn en lugar de Flask directamente
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
