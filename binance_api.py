"""
Módulo para conexão com a API da Binance e coleta de dados de criptomoedas.
Busca dados de candlestick (OHLCV) e calcula indicadores técnicos.
"""

import os
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import requests
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logger = logging.getLogger(__name__)

# URLs da API da Binance
BINANCE_API_BASE_URL = "https://api.binance.com/api/v3"
BINANCE_KLINES_ENDPOINT = f"{BINANCE_API_BASE_URL}/klines"


class BinanceAPI:
    """Cliente para API pública da Binance."""

    def __init__(self):
        """Inicializa o cliente da API da Binance."""
        self.base_url = BINANCE_API_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0'
        })

    def get_klines(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1m",
        limit: int = 100
    ) -> Optional[List[List]]:
        """
        Busca dados de candlestick (klines) da Binance.

        Args:
            symbol: Par de negociação (ex: 'BTCUSDT', 'ETHUSDT')
            interval: Intervalo de tempo ('1m', '5m', '15m', '1h', '1d')
            limit: Número de candles a buscar (máximo 1000)

        Returns:
            List[List]: Lista de klines ou None se houver erro

        Formato de retorno da API Binance:
        [
            [
                1499040000000,      # Open time
                "0.01634000",       # Open
                "0.80000000",       # High
                "0.01575800",       # Low
                "0.01577100",       # Close
                "148976.11427815",  # Volume
                1499644799999,      # Close time
                "2434.19055334",    # Quote asset volume
                308,                # Number of trades
                "1756.87402397",    # Taker buy base asset volume
                "28.46694368",      # Taker buy quote asset volume
                "17928899.62484339" # Ignore
            ]
        ]
        """
        try:
            params = {
                'symbol': symbol.upper(),
                'interval': interval,
                'limit': min(limit, 1000)  # Máximo 1000 pela API
            }

            logger.info(f"Buscando klines da Binance: {symbol} {interval} (limit={limit})")

            response = self.session.get(BINANCE_KLINES_ENDPOINT, params=params, timeout=10)
            response.raise_for_status()

            klines = response.json()
            logger.info(f"Klines recebidos com sucesso: {len(klines)} candles")

            return klines

        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao buscar klines da Binance: {e}")
            return None
        except Exception as e:
            logger.error(f"Erro inesperado ao buscar klines: {e}")
            return None

    def klines_to_dataframe(self, klines: List[List]) -> pd.DataFrame:
        """
        Converte klines da Binance para DataFrame do pandas.

        Args:
            klines: Lista de klines retornada pela API

        Returns:
            pd.DataFrame: DataFrame com colunas formatadas
        """
        if not klines:
            logger.warning("Klines vazios recebidos")
            return pd.DataFrame()

        try:
            # Criar DataFrame com as colunas relevantes
            df = pd.DataFrame(klines, columns=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            # Converter tipos de dados
            df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')

            # Converter preços para float
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)

            # Remover colunas desnecessárias
            df = df[['open_time', 'open', 'high', 'low', 'close', 'volume']]

            # Formatar open_time como string para compatibilidade com MongoDB
            df['open_time'] = df['open_time'].dt.strftime('%Y-%m-%d %H:%M:%S')

            logger.info(f"DataFrame criado com {len(df)} registros")
            return df

        except Exception as e:
            logger.error(f"Erro ao converter klines para DataFrame: {e}")
            return pd.DataFrame()


def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
    """
    Calcula as Bandas de Bollinger.

    Args:
        df: DataFrame com coluna 'close'
        period: Período para média móvel (padrão: 20)
        std_dev: Número de desvios padrão (padrão: 2.0)

    Returns:
        pd.DataFrame: DataFrame com colunas Upper, Lower e MA20 adicionadas
    """
    try:
        if df.empty or 'close' not in df.columns:
            logger.error("DataFrame vazio ou sem coluna 'close'")
            return df

        # Calcular Média Móvel Simples (SMA) de 20 períodos
        df['MA20'] = df['close'].rolling(window=period).mean()

        # Calcular desvio padrão
        rolling_std = df['close'].rolling(window=period).std()

        # Calcular bandas superior e inferior
        df['Upper'] = df['MA20'] + (rolling_std * std_dev)
        df['Lower'] = df['MA20'] - (rolling_std * std_dev)

        # Preencher valores NaN nas primeiras linhas com valores razoáveis
        # (primeiros períodos não têm média móvel completa)
        for i in range(min(period, len(df))):
            if pd.isna(df.loc[i, 'MA20']):
                # Usar média parcial dos dados disponíveis
                df.loc[i, 'MA20'] = df.loc[:i+1, 'close'].mean()
                partial_std = df.loc[:i+1, 'close'].std()
                df.loc[i, 'Upper'] = df.loc[i, 'MA20'] + (partial_std * std_dev)
                df.loc[i, 'Lower'] = df.loc[i, 'MA20'] - (partial_std * std_dev)

        logger.info("Bandas de Bollinger calculadas com sucesso")
        return df

    except Exception as e:
        logger.error(f"Erro ao calcular Bandas de Bollinger: {e}")
        return df


def get_binance_data_with_indicators(
    symbol: str = "BTCUSDT",
    interval: str = "1m",
    limit: int = 100
) -> Optional[pd.DataFrame]:
    """
    Busca dados da Binance e calcula indicadores técnicos.

    Args:
        symbol: Par de negociação
        interval: Intervalo de tempo
        limit: Número de candles

    Returns:
        pd.DataFrame: DataFrame com preços e indicadores ou None se houver erro
    """
    try:
        # Criar cliente da API
        api = BinanceAPI()

        # Buscar klines
        klines = api.get_klines(symbol=symbol, interval=interval, limit=limit)

        if not klines:
            logger.error("Falha ao buscar klines da Binance")
            return None

        # Converter para DataFrame
        df = api.klines_to_dataframe(klines)

        if df.empty:
            logger.error("DataFrame vazio após conversão")
            return None

        # Calcular Bandas de Bollinger e MA20
        df = calculate_bollinger_bands(df, period=20, std_dev=2.0)

        # Arredondar valores para 2 casas decimais
        for col in ['open', 'high', 'low', 'close', 'Upper', 'Lower', 'MA20']:
            if col in df.columns:
                df[col] = df[col].round(2)

        logger.info(f"Dados da Binance processados: {len(df)} candles com indicadores")
        return df

    except Exception as e:
        logger.error(f"Erro ao buscar dados da Binance com indicadores: {e}")
        return None


def save_to_mongodb(df: pd.DataFrame, collection) -> bool:
    """
    Salva DataFrame no MongoDB.

    Args:
        df: DataFrame com dados
        collection: Coleção do MongoDB

    Returns:
        bool: True se salvou com sucesso, False caso contrário
    """
    try:
        if df.empty:
            logger.warning("DataFrame vazio, nada para salvar")
            return False

        # Converter DataFrame para lista de dicionários
        records = df.to_dict('records')

        # Limpar collection antes de inserir novos dados
        collection.delete_many({})
        logger.info("Collection limpa")

        # Inserir novos dados
        result = collection.insert_many(records)
        logger.info(f"{len(result.inserted_ids)} documentos inseridos no MongoDB")

        return True

    except Exception as e:
        logger.error(f"Erro ao salvar dados no MongoDB: {e}")
        return False
