#!/bin/bash
# Script to verify AI Translator installation

echo "🔍 Verifying AI Translator installation..."

# Check services
echo "\nChecking services:"
echo "AI Translator: $(systemctl is-active ai-translator)"
echo "PostgreSQL: $(systemctl is-active postgresql)"
echo "Nginx: $(systemctl is-active nginx)"

# Check ports
echo "\nChecking ports:"
echo "Port 5000 (AI Translator): $(netstat -tuln | grep -q ':5000 ' && echo 'OPEN' || echo 'CLOSED')"
echo "Port 80 (Nginx): $(netstat -tuln | grep -q ':80 ' && echo 'OPEN' || echo 'CLOSED')"
echo "Port 5432 (PostgreSQL): $(netstat -tuln | grep -q ':5432 ' && echo 'OPEN' || echo 'CLOSED')"
echo "Port 11434 (Ollama): $(netstat -tuln | grep -q ':11434 ' && echo 'OPEN' || echo 'CLOSED')"

# Check database
echo "\nChecking database connection:"
if python3 -c "import psycopg2; conn = psycopg2.connect('dbname=ai_translator user=ai_translator password=ai_translator_pass2024 host=localhost'); print('Database connection successful')" 2>/dev/null; then
    echo "Database connection: SUCCESS"
else
    echo "Database connection: FAILED"
fi

# Check web access
echo "\nChecking web access:"
if curl -s http://localhost:5000 | grep -q "AI Translator"; then
    echo "Web access: SUCCESS"
else
    echo "Web access: FAILED"
fi

echo "\n✅ Verification complete"

#!/bin/bash
# Script to verify AI Translator installation

echo "🔍 Verifying AI Translator installation..."

# Check services
echo "\nChecking services:"
echo "AI Translator: $(systemctl is-active ai-translator)"
echo "PostgreSQL: $(systemctl is-active postgresql)"
echo "Nginx: $(systemctl is-active nginx)"

# Check ports
echo "\nChecking ports:"
echo "Port 5000 (AI Translator): $(netstat -tuln | grep -q ':5000 ' && echo 'OPEN' || echo 'CLOSED')"
echo "Port 80 (Nginx): $(netstat -tuln | grep -q ':80 ' && echo 'OPEN' || echo 'CLOSED')"
echo "Port 5432 (PostgreSQL): $(netstat -tuln | grep -q ':5432 ' && echo 'OPEN' || echo 'CLOSED')"
echo "Port 11434 (Ollama): $(netstat -tuln | grep -q ':11434 ' && echo 'OPEN' || echo 'CLOSED')"

# Check database
echo "\nChecking database connection:"
if python3 -c "import psycopg2; conn = psycopg2.connect('dbname=ai_translator user=ai_translator password=ai_translator_pass2024 host=localhost'); print('Database connection successful')" 2>/dev/null; then
    echo "Database connection: SUCCESS"
else
    echo "Database connection: FAILED"
fi

# Check web access
echo "\nChecking web access:"
if curl -s http://localhost:5000 | grep -q "AI Translator"; then
    echo "Web access: SUCCESS"
else
    echo "Web access: FAILED"
fi

echo "\n✅ Verification complete"