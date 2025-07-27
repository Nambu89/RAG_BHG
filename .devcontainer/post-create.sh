#!/bin/bash
set -e

echo "Setting up BHG RAG development environment..."

# Create necessary directories
echo "Creating project directories..."
mkdir -p data/contracts data/processed data/vector_store logs .streamlit
mkdir -p tests/data cache output

# Create .env file from template if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please update .env with your API keys!"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Install pre-commit hooks
echo "Setting up pre-commit hooks..."
pre-commit install

# Download spaCy models
echo "Downloading spaCy language models..."
python -m spacy download es_core_news_sm
python -m spacy download en_core_web_sm

# Create Streamlit config
echo "Setting up Streamlit configuration..."
mkdir -p .streamlit
cat > .streamlit/config.toml << 'EOF'
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
headless = true
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 200

[browser]
gatherUsageStats = false
EOF

# Create initial test data
echo "Creating sample test data..."
cat > data/contracts/sample_contract.txt << 'EOF'
CONTRATO DE GESTIÓN HOTELERA

Entre Barceló Hotel Group S.A., con CIF A-12345678, domiciliada en Palma de Mallorca,
y Hotel Example S.L., con CIF B-87654321, domiciliada en Madrid.

CLÁUSULAS:
1. OBJETO: Gestión integral del Hotel Example Madrid
2. DURACIÓN: 10 años desde el 1 de enero de 2024
3. CANON DE GESTIÓN: 5% sobre ingresos totales
4. OBLIGACIONES DEL GESTOR:
   - Mantener estándares de calidad Barceló
   - Reportar mensualmente resultados operativos
   - Gestionar personal según normativa laboral
   - Mantener las instalaciones en perfecto estado

Firmado en Madrid, a 15 de diciembre de 2023.
EOF

# Run initial tests
echo "Running initial tests..."
python -m pytest tests/ -v --tb=short || echo "Some tests failed, this is expected in initial setup"

# Create VS Code workspace settings
echo "Configuring VS Code workspace..."
mkdir -p .vscode
cat > .vscode/settings.json << 'EOF'
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "python.testing.pytestEnabled": true,
    "python.testing.unittestEnabled": false,
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/.pytest_cache": true,
        "**/.coverage": true,
        "**/htmlcov": true
    }
}
EOF

# Final message
echo "Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your OpenAI API key"
echo "2. Run 'streamlit run src/ui/streamlit_app.py' to start the app"
echo "3. Visit http://localhost:8501"
echo ""
echo "Happy coding!"