#!/bin/bash
echo "🍽️  Iniciando Sistema Epicuro..."
echo "📂 Directorio: $(pwd)"

# Activar entorno virtual
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "🔄 Activando entorno virtual..."
    source venv/bin/activate
fi

# Verificar Flask
python3 -c "import flask; print(f'✅ Flask {flask.__version__} instalado')" 2>/dev/null || {
    echo "❌ Flask no encontrado. Instalando..."
    pip install Flask==2.3.3 Werkzeug==2.3.7
}

# Inicializar base de datos
echo "🗄️  Inicializando base de datos..."
python3 -c "
from app import init_db
init_db()
print('✅ Base de datos lista')
" 2>/dev/null || echo "⚠️  Ejecutar después de crear app.py"

# Iniciar servidor
echo "🌐 Abriendo http://localhost:5002"
echo "🛑 Presiona Ctrl+C para detener"
python3 app.py
