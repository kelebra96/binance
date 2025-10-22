"""
Script para popular o MongoDB com dados de exemplo para testar a aplicação.
Cria dados sintéticos de criptomoedas com Bandas de Bollinger e Média Móvel.

Uso: python populate_sample_data.py
"""

import os
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv
import random

# Carregar variáveis de ambiente
load_dotenv()

# Configuração
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "crypto_db")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "crypto_data")

print("=" * 80)
print("POPULAR MONGODB COM DADOS DE EXEMPLO")
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
    client.server_info()

    print("✅ Conexão estabelecida!")
    print()

    db = client[MONGODB_DATABASE]
    collection = db[MONGODB_COLLECTION]

    # Verificar se já existem dados
    existing_count = collection.count_documents({})

    if existing_count > 0:
        print(f"⚠️  A collection já contém {existing_count} documentos.")
        response = input("Deseja LIMPAR todos os dados e inserir novos? (sim/não): ")

        if response.lower() in ["sim", "s", "yes", "y"]:
            collection.delete_many({})
            print("🗑️  Dados antigos removidos.")
            print()
        else:
            print("❌ Operação cancelada.")
            client.close()
            exit(0)

    # Gerar dados de exemplo
    print("📊 Gerando dados de exemplo...")
    print()

    # Parâmetros
    num_candles = 100
    base_price = 42000.0  # BTC base price
    volatility = 500.0

    # Iniciar do passado
    start_time = datetime.now() - timedelta(minutes=num_candles)

    data = []

    for i in range(num_candles):
        timestamp = start_time + timedelta(minutes=i)

        # Gerar preços com movimento browniano
        price_change = random.gauss(0, volatility)
        open_price = base_price + price_change

        high_price = open_price + random.uniform(0, volatility * 0.5)
        low_price = open_price - random.uniform(0, volatility * 0.5)

        close_change = random.gauss(0, volatility * 0.3)
        close_price = open_price + close_change

        # Garantir que high é o maior e low o menor
        high_price = max(high_price, open_price, close_price)
        low_price = min(low_price, open_price, close_price)

        # Calcular indicadores
        # MA20: média dos últimos 20 fechamentos
        if i >= 20:
            recent_closes = [d["close"] for d in data[-20:]]
            ma20 = sum(recent_closes) / 20

            # Calcular desvio padrão
            variance = sum((x - ma20) ** 2 for x in recent_closes) / 20
            std_dev = variance ** 0.5

            # Bandas de Bollinger (2 desvios padrão)
            upper_band = ma20 + (2 * std_dev)
            lower_band = ma20 - (2 * std_dev)
        else:
            # Para os primeiros 20 candles, usar valores aproximados
            ma20 = close_price
            upper_band = close_price + (volatility * 2)
            lower_band = close_price - (volatility * 2)

        # Criar documento
        doc = {
            "open_time": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "open": round(open_price, 2),
            "high": round(high_price, 2),
            "low": round(low_price, 2),
            "close": round(close_price, 2),
            "Upper": round(upper_band, 2),
            "Lower": round(lower_band, 2),
            "MA20": round(ma20, 2)
        }

        data.append(doc)
        base_price = close_price  # Próximo candle começa onde o anterior terminou

    # Inserir no MongoDB
    print(f"💾 Inserindo {len(data)} documentos no MongoDB...")
    result = collection.insert_many(data)

    print(f"✅ {len(result.inserted_ids)} documentos inseridos com sucesso!")
    print()

    # Mostrar estatísticas
    print("📈 Estatísticas dos dados inseridos:")
    print("-" * 80)
    print(f"   Primeiro candle: {data[0]['open_time']}")
    print(f"   Último candle:   {data[-1]['open_time']}")
    print(f"   Preço inicial:   ${data[0]['close']:.2f}")
    print(f"   Preço final:     ${data[-1]['close']:.2f}")
    print(f"   Variação:        ${(data[-1]['close'] - data[0]['close']):.2f}")
    print()

    # Contar possíveis sinais
    buy_signals = sum(1 for d in data if d['close'] <= d['Lower'])
    sell_signals = sum(1 for d in data if d['close'] >= d['Upper'])

    print(f"   🟢 Potenciais sinais de COMPRA:  {buy_signals}")
    print(f"   🔴 Potenciais sinais de VENDA:   {sell_signals}")
    print()

    print("✅ PRONTO! Agora você pode executar a aplicação:")
    print("   streamlit run main.py")
    print()
    print("=" * 80)

    client.close()

except Exception as e:
    print(f"❌ ERRO: {e}")
    print()
    print("Verifique se:")
    print("  1. MongoDB está rodando")
    print("  2. Você tem permissões para escrever no banco")
    print("  3. A URI de conexão está correta no arquivo .env")
