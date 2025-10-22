"""
Script para coletar dados da Binance continuamente e salvar no MongoDB.
Este script roda em background e atualiza o MongoDB periodicamente.

Uso:
    python collect_data.py
    python collect_data.py --symbol ETHUSDT --interval 5m --update-interval 60
"""

import os
import sys
import time
import argparse
import logging
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv
from binance_api import get_binance_data_with_indicators, save_to_mongodb

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('collect_data.log')
    ]
)
logger = logging.getLogger(__name__)

# Configurações
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "crypto_db")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "crypto_data")


def parse_arguments():
    """Parse argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description='Coleta dados da Binance e salva no MongoDB'
    )

    parser.add_argument(
        '--symbol',
        type=str,
        default='BTCUSDT',
        help='Símbolo da criptomoeda (padrão: BTCUSDT)'
    )

    parser.add_argument(
        '--interval',
        type=str,
        default='1m',
        choices=['1m', '5m', '15m', '1h', '1d'],
        help='Intervalo dos candles (padrão: 1m)'
    )

    parser.add_argument(
        '--limit',
        type=int,
        default=100,
        help='Número de candles a buscar (padrão: 100)'
    )

    parser.add_argument(
        '--update-interval',
        type=int,
        default=60,
        help='Intervalo de atualização em segundos (padrão: 60)'
    )

    parser.add_argument(
        '--once',
        action='store_true',
        help='Executar apenas uma vez ao invés de loop contínuo'
    )

    return parser.parse_args()


def collect_and_save(symbol: str, interval: str, limit: int, collection) -> bool:
    """
    Coleta dados da Binance e salva no MongoDB.

    Args:
        symbol: Símbolo da criptomoeda
        interval: Intervalo dos candles
        limit: Número de candles
        collection: Coleção do MongoDB

    Returns:
        bool: True se bem-sucedido, False caso contrário
    """
    try:
        logger.info(f"Coletando dados da Binance: {symbol} {interval}")

        # Buscar dados da Binance com indicadores
        df = get_binance_data_with_indicators(
            symbol=symbol,
            interval=interval,
            limit=limit
        )

        if df is None or df.empty:
            logger.error("Falha ao buscar dados da Binance")
            return False

        # Salvar no MongoDB
        success = save_to_mongodb(df, collection)

        if success:
            last_price = df.iloc[-1]['close']
            last_time = df.iloc[-1]['open_time']
            logger.info(f"✅ Dados atualizados: {symbol} @ ${last_price:.2f} ({last_time})")
            return True
        else:
            logger.error("Falha ao salvar dados no MongoDB")
            return False

    except Exception as e:
        logger.error(f"Erro ao coletar e salvar dados: {e}")
        return False


def main():
    """Função principal."""
    args = parse_arguments()

    print("=" * 80)
    print("COLETOR DE DADOS DA BINANCE")
    print("=" * 80)
    print(f"Símbolo:           {args.symbol}")
    print(f"Intervalo:         {args.interval}")
    print(f"Número de candles: {args.limit}")
    print(f"Atualização:       a cada {args.update_interval} segundos")
    print(f"Modo:              {'Única execução' if args.once else 'Loop contínuo'}")
    print("=" * 80)
    print()

    try:
        # Conectar ao MongoDB
        logger.info("Conectando ao MongoDB...")
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.server_info()  # Testa conexão
        logger.info("✅ Conectado ao MongoDB")

        db = client[MONGODB_DATABASE]
        collection = db[MONGODB_COLLECTION]

        if args.once:
            # Executar apenas uma vez
            logger.info("Modo de execução única")
            success = collect_and_save(args.symbol, args.interval, args.limit, collection)

            if success:
                print()
                print("✅ Dados coletados e salvos com sucesso!")
                print("Execute 'streamlit run main.py' para visualizar")
            else:
                print()
                print("❌ Erro ao coletar dados. Verifique os logs.")
                sys.exit(1)

        else:
            # Loop contínuo
            logger.info("Iniciando loop contínuo de coleta de dados")
            print("Loop iniciado. Pressione Ctrl+C para parar.")
            print()

            iteration = 0

            while True:
                iteration += 1
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iteração #{iteration}")

                success = collect_and_save(args.symbol, args.interval, args.limit, collection)

                if success:
                    print(f"✅ Dados atualizados ({args.symbol})")
                else:
                    print(f"❌ Erro ao atualizar dados")

                # Aguardar próximo ciclo
                logger.info(f"Aguardando {args.update_interval} segundos...")
                time.sleep(args.update_interval)

    except KeyboardInterrupt:
        print()
        print("=" * 80)
        print("⚠️  Interrompido pelo usuário (Ctrl+C)")
        print("=" * 80)
        logger.info("Script interrompido pelo usuário")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Erro fatal: {e}")
        print()
        print("=" * 80)
        print(f"❌ ERRO FATAL: {e}")
        print("=" * 80)
        print()
        print("Possíveis causas:")
        print("  1. MongoDB não está rodando")
        print("  2. Sem conexão com a internet (API da Binance)")
        print("  3. Símbolo inválido")
        print()
        print("Verifique os logs em: collect_data.log")
        sys.exit(1)

    finally:
        if 'client' in locals():
            client.close()
            logger.info("Conexão com MongoDB fechada")


if __name__ == "__main__":
    main()
