"""
Script de diagnóstico para verificar a estrutura dos dados no MongoDB.
Execute este script para entender o que há no seu banco de dados.

Uso: python check_mongodb.py
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "crypto_db")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "crypto_data")

print("=" * 80)
print("DIAGNÓSTICO DO MONGODB")
print("=" * 80)
print()

try:
    # Conectar ao MongoDB
    print(f"🔗 Conectando ao MongoDB...")
    print(f"   URI: {MONGODB_URI}")
    print(f"   Database: {MONGODB_DATABASE}")
    print(f"   Collection: {MONGODB_COLLECTION}")
    print()

    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)

    # Testar conexão
    client.server_info()
    print("✅ Conexão com MongoDB estabelecida com sucesso!")
    print()

    # Acessar database e collection
    db = client[MONGODB_DATABASE]
    collection = db[MONGODB_COLLECTION]

    # Contar documentos
    total_docs = collection.count_documents({})
    print(f"📊 Total de documentos na collection: {total_docs}")
    print()

    if total_docs == 0:
        print("⚠️  ATENÇÃO: A collection está VAZIA!")
        print()
        print("Você precisa inserir dados no MongoDB antes de usar a aplicação.")
        print("Use o script 'populate_sample_data.py' para inserir dados de exemplo.")
        client.close()
        exit(1)

    # Buscar um documento de exemplo
    print("📄 Exemplo de documento (primeiro registro):")
    print("-" * 80)
    sample_doc = collection.find_one()

    if sample_doc:
        for key, value in sample_doc.items():
            print(f"   {key}: {value} (tipo: {type(value).__name__})")
    print()

    # Verificar colunas necessárias
    required_columns = ["open_time", "open", "high", "low", "close", "Upper", "Lower", "MA20"]

    print("🔍 Verificando colunas obrigatórias:")
    print("-" * 80)

    missing_columns = []
    present_columns = []

    for col in required_columns:
        if col in sample_doc:
            present_columns.append(col)
            print(f"   ✅ {col}: PRESENTE")
        else:
            missing_columns.append(col)
            print(f"   ❌ {col}: AUSENTE")

    print()

    if missing_columns:
        print("⚠️  PROBLEMA ENCONTRADO!")
        print()
        print(f"As seguintes colunas estão AUSENTES: {', '.join(missing_columns)}")
        print()
        print("A aplicação precisa destas colunas para funcionar:")
        print("  - open_time: Timestamp do candle")
        print("  - open: Preço de abertura")
        print("  - high: Preço máximo")
        print("  - low: Preço mínimo")
        print("  - close: Preço de fechamento")
        print("  - Upper: Banda superior de Bollinger")
        print("  - Lower: Banda inferior de Bollinger")
        print("  - MA20: Média móvel de 20 períodos")
        print()
        print("SOLUÇÃO: Use o script 'populate_sample_data.py' para corrigir a estrutura dos dados.")
    else:
        print("✅ TUDO OK! Todos os campos necessários estão presentes.")
        print()
        print(f"📈 Últimos 5 registros (preços de fechamento):")
        print("-" * 80)

        last_docs = list(collection.find().sort("_id", -1).limit(5))
        for i, doc in enumerate(reversed(last_docs), 1):
            timestamp = doc.get("open_time", "N/A")
            close_price = doc.get("close", "N/A")
            print(f"   {i}. {timestamp} - Close: ${close_price}")
        print()
        print("✅ Sua aplicação deve funcionar corretamente!")

    print()
    print("=" * 80)

    # Fechar conexão
    client.close()

except Exception as e:
    print(f"❌ ERRO: {e}")
    print()
    print("Possíveis causas:")
    print("  1. MongoDB não está rodando")
    print("  2. URI de conexão incorreta")
    print("  3. Database ou collection não existe")
    print()
    print("Verifique se o MongoDB está rodando:")
    print("  - Windows: Verifique o serviço MongoDB no Gerenciador de Tarefas")
    print("  - Linux/Mac: sudo systemctl status mongod")
