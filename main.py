import os
import logging
import time
import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from pymongo import MongoClient
from pymongo.collection import Collection
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configurações iniciais
st.set_page_config(
    page_title="Crypto Monitor with Bollinger Bands and Moving Average",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

# Configuração do cliente MongoDB usando variáveis de ambiente
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "crypto_db")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "crypto_data")
DEFAULT_CRYPTO_SYMBOL = os.getenv("DEFAULT_CRYPTO_SYMBOL", "BTCUSDT")
DEFAULT_INTERVAL = os.getenv("DEFAULT_INTERVAL", "1m")
DATA_LIMIT = int(os.getenv("DATA_LIMIT", "100"))
AUTO_REFRESH_INTERVAL = int(os.getenv("AUTO_REFRESH_INTERVAL", "60"))


def get_mongodb_client() -> MongoClient:
    """
    Cria e retorna um cliente MongoDB.

    Returns:
        MongoClient: Cliente MongoDB conectado

    Raises:
        Exception: Se não conseguir conectar ao MongoDB
    """
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        # Testa a conexão
        client.server_info()
        logger.info("Conectado ao MongoDB com sucesso")
        return client
    except Exception as e:
        logger.error(f"Erro ao conectar ao MongoDB: {e}")
        raise


def fetch_data_from_mongodb(collection: Collection, limit: int = 100) -> pd.DataFrame:
    """
    Busca dados do MongoDB e retorna como DataFrame do pandas.

    Args:
        collection: Coleção do MongoDB
        limit: Número máximo de documentos a buscar

    Returns:
        pd.DataFrame: DataFrame com os dados ou DataFrame vazio se houver erro
    """
    try:
        logger.info(f"Buscando últimos {limit} documentos do MongoDB")

        # Busca os últimos documentos e ordena por _id crescente
        data = list(collection.find().sort("_id", -1).limit(limit))

        if not data:
            logger.warning("Nenhum dado encontrado no MongoDB")
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # Remove a coluna _id se existir
        if "_id" in df.columns:
            df.drop("_id", axis=1, inplace=True)

        # Inverte a ordem para que os dados mais antigos apareçam primeiro
        df = df.iloc[::-1].reset_index(drop=True)

        # Valida se as colunas necessárias existem
        required_columns = ["open_time", "open", "high", "low", "close", "Upper", "Lower", "MA20"]
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            logger.error(f"Colunas obrigatórias ausentes: {missing_columns}")
            st.error(f"Dados incompletos no MongoDB. Colunas ausentes: {', '.join(missing_columns)}")
            return pd.DataFrame()

        logger.info(f"Dados carregados com sucesso: {len(df)} registros")
        return df

    except Exception as e:
        logger.error(f"Erro ao buscar dados do MongoDB: {e}")
        st.error(f"Erro ao buscar dados: {str(e)}")
        return pd.DataFrame()


def identify_trade_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Identifica sinais de compra e venda baseados nas Bandas de Bollinger.

    Args:
        df: DataFrame com dados de preço e indicadores

    Returns:
        pd.DataFrame: DataFrame com colunas adicionais Buy_Signal e Sell_Signal
    """
    try:
        # Sinal de compra: preço de fechamento abaixo ou igual à banda inferior
        df["Buy_Signal"] = df["close"] <= df["Lower"]

        # Sinal de venda: preço de fechamento acima ou igual à banda superior
        df["Sell_Signal"] = df["close"] >= df["Upper"]

        logger.info(f"Sinais identificados - Compra: {df['Buy_Signal'].sum()}, Venda: {df['Sell_Signal'].sum()}")
        return df

    except Exception as e:
        logger.error(f"Erro ao identificar sinais de compra/venda: {e}")
        return df


def create_candlestick_chart(df: pd.DataFrame, crypto_symbol: str, interval: str) -> go.Figure:
    """
    Cria gráfico de candlestick com Bandas de Bollinger, Média Móvel e sinais de compra/venda.

    Args:
        df: DataFrame com dados de preço e indicadores
        crypto_symbol: Símbolo da criptomoeda
        interval: Intervalo de tempo

    Returns:
        go.Figure: Figura do Plotly com o gráfico
    """
    try:
        # Criar o gráfico de candlestick
        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=df["open_time"],
                    open=df["open"],
                    high=df["high"],
                    low=df["low"],
                    close=df["close"],
                    name="Price"
                )
            ]
        )

        # Adicionar Bandas de Bollinger
        fig.add_trace(
            go.Scatter(
                x=df["open_time"],
                y=df["Upper"],
                name="Upper Band",
                line=dict(color="rgba(250, 0, 0, 0.50)", width=1),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=df["open_time"],
                y=df["Lower"],
                name="Lower Band",
                line=dict(color="rgba(0, 0, 250, 0.50)", width=1),
            )
        )

        # Adicionar Média Móvel
        fig.add_trace(
            go.Scatter(
                x=df["open_time"],
                y=df["MA20"],
                name="Moving Average (20)",
                line=dict(color="rgba(0, 255, 0, 0.50)", width=2),
            )
        )

        # Adicionar sinais de compra
        buy_signals = df[df["Buy_Signal"]]
        if not buy_signals.empty:
            fig.add_trace(
                go.Scatter(
                    mode="markers",
                    x=buy_signals["open_time"],
                    y=buy_signals["close"],
                    marker=dict(color="green", size=10, symbol="triangle-up"),
                    name="Buy Signal",
                )
            )

        # Adicionar sinais de venda
        sell_signals = df[df["Sell_Signal"]]
        if not sell_signals.empty:
            fig.add_trace(
                go.Scatter(
                    mode="markers",
                    x=sell_signals["open_time"],
                    y=sell_signals["close"],
                    marker=dict(color="red", size=10, symbol="triangle-down"),
                    name="Sell Signal",
                )
            )

        # Layout do gráfico
        fig.update_layout(
            title=f"{crypto_symbol} Candlestick Chart with Bollinger Bands and Moving Average ({interval})",
            xaxis_title="Time",
            yaxis_title="Price",
            xaxis_rangeslider_visible=False,
            hovermode="x unified",
            height=600
        )

        return fig

    except Exception as e:
        logger.error(f"Erro ao criar gráfico: {e}")
        raise


# Título da aplicação
st.title(":chart_with_upwards_trend: Crypto Monitor with Bollinger Bands and Moving Average")

# Entrada do usuário para o símbolo da criptomoeda e intervalo
crypto_symbol = st.sidebar.text_input(
    "Enter the crypto symbol (e.g., 'BTCUSDT'):",
    DEFAULT_CRYPTO_SYMBOL
)
interval = st.sidebar.selectbox(
    "Select the interval for the candlestick chart:",
    options=["1m", "5m", "15m", "1h", "1d"],
    index=0,
)

# Configuração de auto-refresh
st.sidebar.markdown("---")
st_autorefresh = st.sidebar.checkbox("Auto-refresh", value=False)
if st_autorefresh:
    st.sidebar.info(f"Auto-refreshing every {AUTO_REFRESH_INTERVAL} seconds")

# Botão para buscar dados
get_data_button = st.sidebar.button("Get Data")

# Instruções
st.sidebar.markdown("---")
st.sidebar.markdown("### Instructions")
st.sidebar.write("1. Enter the crypto symbol in the input box")
st.sidebar.write("2. Select the interval for the candlestick chart")
st.sidebar.write("3. Click on 'Get Data' to fetch the latest data")
st.sidebar.write("4. Check 'Auto-refresh' for live updates")

# Lógica principal
if get_data_button or st_autorefresh:
    try:
        # Conectar ao MongoDB
        with st.spinner("Connecting to MongoDB..."):
            client = get_mongodb_client()
            db = client[MONGODB_DATABASE]
            collection = db[MONGODB_COLLECTION]

        # Buscar dados do MongoDB
        with st.spinner("Fetching data from MongoDB..."):
            candle_data = fetch_data_from_mongodb(collection, limit=DATA_LIMIT)

        # Verificar se há dados
        if candle_data.empty:
            st.warning("No data available in MongoDB. Please check your database.")
        else:
            # Identificar sinais de compra/venda
            candle_data_with_signals = identify_trade_signals(candle_data)

            # Criar e exibir o gráfico
            with st.spinner("Creating chart..."):
                fig = create_candlestick_chart(candle_data_with_signals, crypto_symbol, interval)
                st.plotly_chart(fig, use_container_width=True)

            # Exibir o último preço
            last_price = candle_data_with_signals.iloc[-1]["close"]
            last_time = candle_data_with_signals.iloc[-1]["open_time"]

            # Métricas em colunas
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Last Close Price", f"${last_price:.2f}")

            with col2:
                upper_band = candle_data_with_signals.iloc[-1]["Upper"]
                st.metric("Upper Band", f"${upper_band:.2f}")

            with col3:
                lower_band = candle_data_with_signals.iloc[-1]["Lower"]
                st.metric("Lower Band", f"${lower_band:.2f}")

            with col4:
                ma20 = candle_data_with_signals.iloc[-1]["MA20"]
                st.metric("MA20", f"${ma20:.2f}")

            # Estatísticas dos sinais
            st.markdown("---")
            col1, col2, col3 = st.columns(3)

            with col1:
                total_signals = len(candle_data_with_signals)
                st.info(f"📊 Total Data Points: {total_signals}")

            with col2:
                buy_signals = candle_data_with_signals["Buy_Signal"].sum()
                st.success(f"🟢 Buy Signals: {buy_signals}")

            with col3:
                sell_signals = candle_data_with_signals["Sell_Signal"].sum()
                st.error(f"🔴 Sell Signals: {sell_signals}")

            logger.info(f"Dashboard atualizado com sucesso para {crypto_symbol}")

        # Fechar conexão com MongoDB
        client.close()

    except Exception as e:
        logger.error(f"Erro na aplicação: {e}")
        st.error(f"An error occurred: {str(e)}")
        st.error("Please check your MongoDB connection and ensure the database is running.")

# Auto-refresh com intervalo correto
if st_autorefresh:
    time.sleep(AUTO_REFRESH_INTERVAL)
    st.rerun()
