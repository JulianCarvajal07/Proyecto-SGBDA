FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /vortexSQL

# 1️ Instalar dependencias base primero (incluyendo curl)
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    apt-transport-https \
    unixodbc \
    unixodbc-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 2️ Agregar repo de Microsoft CORRECTAMENTE para Debian 12
#    (apt-key está deprecado → usar /etc/apt/keyrings/)
RUN mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
        | gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg \
    && echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/microsoft.gpg] \
        https://packages.microsoft.com/debian/12/prod bookworm main" \
        > /etc/apt/sources.list.d/mssql-release.list

# 3️ Instalar msodbcsql18 en capa separada
RUN apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*


RUN adduser --disabled-password --gecos "" vortexsql-user

COPY requirements.txt .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt gunicorn

COPY . .

RUN mkdir -p /vortexSQL/staticfiles

RUN chown -R vortexsql-user:vortexsql-user /vortexSQL

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER vortexsql-user

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]