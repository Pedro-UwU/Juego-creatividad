FROM python:3.12.3-slim

ENV NVM_DIR=/root/.nvm
ENV NODE_VERSION=22.14.0
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    gnupg \
    iproute2 \
    build-essential \
    && curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash \
    && . "$NVM_DIR/nvm.sh" \
    && nvm install $NODE_VERSION \
    && nvm use $NODE_VERSION \
    && nvm alias default $NODE_VERSION \
    && npm install -g npm \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
ENV PATH="$NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH"

# You can now COPY your files and continue building your app
COPY ./frontend/package.json /app/frontend/
WORKDIR /app/frontend/
RUN npm install 

COPY ./backend/requirements.txt /app/backend/
WORKDIR /app/backend/
RUN pip install -r requirements.txt  

COPY . /app
CMD ["python", "main.py"]

