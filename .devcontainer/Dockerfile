# Base image with Python
ARG VARIANT="3.11-bullseye"
FROM mcr.microsoft.com/vscode/devcontainers/python:${VARIANT}

# Install system dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    build-essential \
    cmake \
    curl \
    git \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (optional, for any JS tools)
ARG NODE_VERSION="none"
RUN if [ "${NODE_VERSION}" != "none" ]; then su vscode -c "umask 0002 && . /usr/local/share/nvm/nvm.sh && nvm install ${NODE_VERSION} 2>&1"; fi

# Install Python tools
RUN pip install --upgrade pip setuptools wheel \
    && pip install \
    pytest \
    pytest-cov \
    pytest-asyncio \
    pytest-mock \
    black \
    flake8 \
    pylint \
    mypy \
    isort \
    pre-commit \
    ipython \
    notebook \
    jupyterlab

# Create directories
WORKDIR /workspaces/bhg-rag-mvp
RUN mkdir -p data/contracts data/processed data/vector_store logs .streamlit

# Set Python path
ENV PYTHONPATH=/workspaces/bhg-rag-mvp/src:$PYTHONPATH

# Install spaCy model
RUN python -m spacy download es_core_news_sm
RUN python -m spacy download en_core_web_sm

# Pre-download some common models to speed up first run
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Set up Git
RUN git config --global core.editor "code --wait" \
    && git config --global init.defaultBranch main

# Install GitHub CLI extensions
RUN gh extension install github/gh-copilot || true

# Create a non-root user to run the app
ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Copy requirements if they exist
COPY requirements.txt* /tmp/
RUN if [ -f /tmp/requirements.txt ]; then pip install -r /tmp/requirements.txt; fi

# Clean up
RUN apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/* /tmp/requirements.txt*

# Set the default shell to zsh
SHELL ["/bin/zsh", "-c"]

# Expose ports
EXPOSE 8501 8000 9090

# Set the default command
CMD ["sleep", "infinity"]