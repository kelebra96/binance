import streamlit as st
import requests
import pandas as pd
import plotly.graph_objs as go
from pymongo import MongoClient
from datetime import datetime, timedelta

# Configurações iniciais
st.set_page_config(
    page_title="Crypto Monitor with Bollinger Bands and Moving Average",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

# Configuração do cliente MongoDB
client = MongoClient("mongodb://localhost:27017/crypto_db")
db = client["crypto_db"]  # Nome do banco de dados
collection = db["crypto_data"]  # Nome da coleção


# Função para buscar dados do MongoDB
def fetch_data_from_mongodb(collection, limit=100):
    try:
        data = list(
            collection.find().sort("_id", -1).limit(limit)
        )  # Busca os últimos 'limit' documentos
        df = pd.DataFrame(data)
        df.drop("_id", axis=1, inplace=True)  # Remova a coluna _id
        return df
    except Exception as e:
        print(f"An error occurred while fetching data from MongoDB: {e}")
        return pd.DataFrame()


# Função para identificar sinais de compra/venda
def identify_trade_signals(df):
    df["Buy_Signal"] = (
        df["close"] <= df["Lower"]
    )  # Sinal de compra se o preço de fechamento estiver abaixo da banda inferior
    df["Sell_Signal"] = (
        df["close"] >= df["Upper"]
    )  # Sinal de venda se o preço de fechamento estiver acima da banda superior
    return df


# Função para plotar gráfico de disco (volume de compra vs venda)
def plot_buy_vs_sell_pie_chart(buy_volume, sell_volume):
    labels = ["Buy Volume", "Sell Volume"]
    values = [buy_volume, sell_volume]

    fig = go.Figure(data=[go.Pie(labels=labels, values=values)])

    fig.update_layout(
        title="Buy vs Sell Volume",
        title_x=0.5,  # Centraliza o título
    )

    st.plotly_chart(fig, use_container_width=True)


# Título da aplicação
st.title(
    ":chart_with_upwards_trend: Crypto Monitor with Bollinger Bands and Moving Average"
)

# Entrada do usuário para o símbolo da criptomoeda e intervalo de tempo para o gráfico de candlestick
crypto_symbol = st.sidebar.text_input(
    "Enter the crypto symbol (e.g., 'BTCUSDT'):", "BTCUSDT"
)
interval = st.sidebar.selectbox(
    "Select the interval for the candlestick chart:",
    options=["1m", "5m", "15m", "1h", "1d"],
    index=0,
)

# Botão para buscar dados da criptomoeda
if (
    st.sidebar.button("Get Data") or True
):  # Remova 'or True' para desabilitar a atualização automática
    # Buscar dados do MongoDB
    candle_data = fetch_data_from_mongodb(collection)

    # Identificar sinais de compra/venda
    candle_data_with_signals = identify_trade_signals(candle_data)

    # Criar o gráfico de candlestick com os sinais
    fig = go.Figure(
        data=[
            go.Candlestick(
                x=candle_data_with_signals["open_time"],
                open=candle_data_with_signals["open"],
                high=candle_data_with_signals["high"],
                low=candle_data_with_signals["low"],
                close=candle_data_with_signals["close"],
            )
        ]
    )

    # Adicionar Bandas de Bollinger e Média Móvel ao gráfico
    fig.add_trace(
        go.Scatter(
            x=candle_data_with_signals["open_time"],
            y=candle_data_with_signals["Upper"],
            name="Upper Band",
            line=dict(color="rgba(250, 0, 0, 0.50)"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=candle_data_with_signals["open_time"],
            y=candle_data_with_signals["Lower"],
            name="Lower Band",
            line=dict(color="rgba(0, 0, 250, 0.50)"),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=candle_data_with_signals["open_time"],
            y=candle_data_with_signals["MA20"],
            name="Moving Average (20)",
            line=dict(color="rgba(0, 255, 0, 0.50)"),
        )
    )

    # Adicionar sinais de compra/venda ao gráfico
    fig.add_trace(
        go.Scatter(
            mode="markers",
            x=candle_data_with_signals[candle_data_with_signals["Buy_Signal"]][
                "open_time"
            ],
            y=candle_data_with_signals[candle_data_with_signals["Buy_Signal"]]["close"],
            marker=dict(color="green", size=10),
            name="Buy Signal",
        )
    )
    fig.add_trace(
        go.Scatter(
            mode="markers",
            x=candle_data_with_signals[candle_data_with_signals["Sell_Signal"]][
                "open_time"
            ],
            y=candle_data_with_signals[candle_data_with_signals["Sell_Signal"]][
                "close"
            ],
            marker=dict(color="red", size=10),
            name="Sell Signal",
        )
    )

    fig.update_layout(
        title=f"{crypto_symbol} Candlestick Chart with Bollinger Bands and Moving Average ({interval})",
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Exibir o último preço
    last_price = candle_data_with_signals.iloc[-1]["close"]
    st.success(f"The last close price of {crypto_symbol} is {last_price}")

    


# Atualizar automaticamente a cada minuto
st_autorefresh = st.sidebar.checkbox("Auto-refresh every minute", value=True)
if st_autorefresh:
    refresh_interval = 60 * 1000  # 60 segundos em milissegundos
    st.experimental_rerun()

# Instruções
st.sidebar.write("1. Enter the crypto symbol in the input box.")
st.sidebar.write("2. Select the interval for the candlestick chart.")
st.sidebar.write("3. Click on 'Get Data' to fetch the latest data.")
st.sidebar.write("4. Check 'Auto-refresh every minute' for live updates.")
