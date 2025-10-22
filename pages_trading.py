"""
Página de Trading Simulator para Streamlit.
Interface completa para trading com ordens, dashboard e gerenciamento de carteira.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from datetime import datetime
from trading_simulator import (
    TradingSimulator,
    OrderType,
    OrderSide,
    OrderStatus,
    save_simulator_to_mongodb,
    load_simulator_from_mongodb
)
from binance_api import get_binance_data_with_indicators
import logging

logger = logging.getLogger(__name__)


def render_trading_page(mongodb_collection):
    """
    Renderiza a página completa de trading simulator.

    Args:
        mongodb_collection: Coleção do MongoDB para salvar estado
    """
    st.title("🎯 Trading Simulator")
    st.markdown("Pratique suas estratégias de trading sem risco real!")

    # Inicializar simulador no session state
    if 'simulator' not in st.session_state:
        # Tentar carregar do MongoDB
        simulator = load_simulator_from_mongodb(mongodb_collection, user_id="default")

        if simulator is None:
            # Criar novo simulador
            initial_balance = st.sidebar.number_input(
                "Saldo Inicial (USDT)",
                min_value=100.0,
                max_value=1000000.0,
                value=10000.0,
                step=1000.0,
                key="initial_balance_input"
            )
            simulator = TradingSimulator(initial_balance=initial_balance)
            st.success(f"✅ Novo simulador criado com saldo de ${initial_balance:,.2f}")

        st.session_state.simulator = simulator

    simulator: TradingSimulator = st.session_state.simulator

    # Buscar preço atual
    if 'current_prices' not in st.session_state:
        st.session_state.current_prices = {}

    # Configurações na sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Configurações")

    # Symbol selector
    symbol = st.sidebar.text_input("Símbolo", value="BTCUSDT", key="trading_symbol")
    interval = st.sidebar.selectbox("Intervalo", ["1m", "5m", "15m", "1h", "1d"], key="trading_interval")

    # Botão para atualizar preço
    if st.sidebar.button("🔄 Atualizar Preço", key="update_price_btn"):
        with st.spinner(f"Buscando preço de {symbol}..."):
            df = get_binance_data_with_indicators(symbol=symbol, interval=interval, limit=1)
            if df is not None and not df.empty:
                current_price = float(df.iloc[-1]['close'])
                st.session_state.current_prices[symbol] = current_price
                st.sidebar.success(f"Preço atualizado: ${current_price:,.2f}")

                # Processar ordens pendentes
                executed = simulator.process_pending_orders(st.session_state.current_prices)
                if executed:
                    st.sidebar.info(f"✅ {len(executed)} ordem(ns) executada(s)")
                    save_simulator_to_mongodb(simulator, mongodb_collection)
            else:
                st.sidebar.error("Erro ao buscar preço")

    # Botões de ação
    st.sidebar.markdown("---")
    if st.sidebar.button("💾 Salvar Simulador", key="save_simulator_btn"):
        if save_simulator_to_mongodb(simulator, mongodb_collection):
            st.sidebar.success("✅ Simulador salvo!")
        else:
            st.sidebar.error("❌ Erro ao salvar")

    if st.sidebar.button("🔄 Resetar Simulador", key="reset_simulator_btn"):
        st.session_state.simulator = TradingSimulator(initial_balance=simulator.initial_balance)
        save_simulator_to_mongodb(st.session_state.simulator, mongodb_collection)
        st.sidebar.success("✅ Simulador resetado!")
        st.rerun()

    # Layout principal: 3 tabs
    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📝 Nova Ordem", "📜 Histórico"])

    # ==================== TAB 1: DASHBOARD ====================
    with tab1:
        render_dashboard(simulator, st.session_state.current_prices)

    # ==================== TAB 2: NOVA ORDEM ====================
    with tab2:
        render_order_form(simulator, mongodb_collection, st.session_state.current_prices)

    # ==================== TAB 3: HISTÓRICO ====================
    with tab3:
        render_history(simulator)


def render_dashboard(simulator: TradingSimulator, current_prices: dict):
    """Renderiza o dashboard com resumo da carteira."""

    # Calcular métricas
    portfolio_value = simulator.get_portfolio_value(current_prices)
    pnl_absolute, pnl_percentage = simulator.get_pnl(current_prices)
    stats = simulator.get_statistics()

    # Cards de métricas principais
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="💰 Saldo Disponível",
            value=f"${simulator.balance:,.2f}",
            delta=None
        )

    with col2:
        st.metric(
            label="📈 Valor do Portfólio",
            value=f"${portfolio_value:,.2f}",
            delta=f"${pnl_absolute:,.2f}" if pnl_absolute != 0 else None,
            delta_color="normal" if pnl_absolute >= 0 else "inverse"
        )

    with col3:
        st.metric(
            label="📊 P&L Total",
            value=f"${pnl_absolute:,.2f}",
            delta=f"{pnl_percentage:.2f}%",
            delta_color="normal" if pnl_absolute >= 0 else "inverse"
        )

    with col4:
        win_rate = stats['win_rate']
        st.metric(
            label="🎯 Taxa de Acerto",
            value=f"{win_rate:.1f}%",
            delta=f"{stats['total_trades']} trades"
        )

    st.markdown("---")

    # Posições abertas
    st.subheader("📂 Posições Abertas")

    if simulator.positions:
        positions_data = []
        for symbol, pos in simulator.positions.items():
            current_price = current_prices.get(symbol, pos['avg_price'])
            current_value = pos['quantity'] * current_price
            pnl = current_value - pos['invested']
            pnl_pct = (pnl / pos['invested']) * 100 if pos['invested'] > 0 else 0

            positions_data.append({
                'Símbolo': symbol,
                'Quantidade': f"{pos['quantity']:.8f}",
                'Preço Médio': f"${pos['avg_price']:,.2f}",
                'Preço Atual': f"${current_price:,.2f}",
                'Valor Investido': f"${pos['invested']:,.2f}",
                'Valor Atual': f"${current_value:,.2f}",
                'P&L': f"${pnl:,.2f}",
                'P&L %': f"{pnl_pct:+.2f}%"
            })

        df_positions = pd.DataFrame(positions_data)
        st.dataframe(df_positions, use_container_width=True)
    else:
        st.info("Nenhuma posição aberta")

    st.markdown("---")

    # Ordens pendentes
    st.subheader("⏳ Ordens Pendentes")

    pending_orders = [o for o in simulator.orders if o['status'] == OrderStatus.PENDING.value]

    if pending_orders:
        orders_data = []
        for order in pending_orders:
            orders_data.append({
                'ID': order['id'],
                'Símbolo': order['symbol'],
                'Tipo': order['type'].upper(),
                'Lado': order['side'].upper(),
                'Quantidade': order['quantity'],
                'Preço': f"${order['price']:,.2f}" if order['price'] else '-',
                'Stop Price': f"${order['stop_price']:,.2f}" if order['stop_price'] else '-',
                'Criada em': order['created_at'][:19]
            })

        df_orders = pd.DataFrame(orders_data)
        st.dataframe(df_orders, use_container_width=True)

        # Opção de cancelar ordem
        st.markdown("##### Cancelar Ordem")
        col1, col2 = st.columns([3, 1])
        with col1:
            order_to_cancel = st.selectbox(
                "Selecione a ordem",
                options=[f"#{o['id']} - {o['symbol']} {o['side']} {o['quantity']}" for o in pending_orders],
                key="cancel_order_select"
            )
        with col2:
            if st.button("🗑️ Cancelar", key="cancel_order_btn"):
                order_id = int(order_to_cancel.split('#')[1].split(' ')[0])
                if simulator.cancel_order(order_id):
                    st.success(f"Ordem #{order_id} cancelada!")
                    st.rerun()
                else:
                    st.error("Erro ao cancelar ordem")
    else:
        st.info("Nenhuma ordem pendente")

    st.markdown("---")

    # Estatísticas de Trading
    st.subheader("📊 Estatísticas de Trading")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total de Trades", stats['total_trades'])
        st.metric("✅ Trades Ganhos", stats['winning_trades'])
        st.metric("❌ Trades Perdidos", stats['losing_trades'])

    with col2:
        st.metric("💚 Ganho Médio", f"${stats['avg_win']:,.2f}")
        st.metric("❤️ Perda Média", f"${stats['avg_loss']:,.2f}")
        st.metric("⭐ Melhor Trade", f"${stats['best_trade']:,.2f}")

    with col3:
        st.metric("🎯 Taxa de Acerto", f"{stats['win_rate']:.1f}%")
        st.metric("💰 P&L Total", f"${stats['total_pnl']:,.2f}")
        st.metric("⚠️ Pior Trade", f"${stats['worst_trade']:,.2f}")


def render_order_form(simulator: TradingSimulator, mongodb_collection, current_prices: dict):
    """Renderiza o formulário para criar novas ordens."""

    st.subheader("📝 Nova Ordem de Trading")

    # Formulário
    col1, col2 = st.columns(2)

    with col1:
        symbol = st.text_input("Símbolo", value="BTCUSDT", key="order_symbol")
        order_type = st.selectbox(
            "Tipo de Ordem",
            options=["Market", "Limit", "Stop Loss", "Take Profit"],
            key="order_type"
        )
        side = st.radio("Lado", options=["BUY", "SELL"], horizontal=True, key="order_side")

    with col2:
        quantity = st.number_input("Quantidade", min_value=0.00001, value=0.001, step=0.001, format="%.8f", key="order_quantity")

        # Campos condicionais baseados no tipo de ordem
        price = None
        stop_price = None

        if order_type == "Limit":
            price = st.number_input("Preço Limite (USDT)", min_value=0.01, value=50000.0, step=100.0, key="order_price")
        elif order_type in ["Stop Loss", "Take Profit"]:
            stop_price = st.number_input("Preço de Stop (USDT)", min_value=0.01, value=50000.0, step=100.0, key="order_stop_price")

    # Informações adicionais
    st.markdown("---")

    current_price = current_prices.get(symbol)
    if current_price:
        st.info(f"💵 Preço Atual de {symbol}: **${current_price:,.2f}**")

        # Calcular custo estimado
        if side == "BUY":
            exec_price = price if order_type == "Limit" else current_price
            estimated_cost = quantity * exec_price if exec_price else 0
            st.info(f"💰 Custo Estimado: **${estimated_cost:,.2f}** USDT")

            if estimated_cost > simulator.balance:
                st.error(f"⚠️ Saldo insuficiente! Disponível: ${simulator.balance:,.2f}")
        else:  # SELL
            if symbol in simulator.positions:
                available = simulator.positions[symbol]['quantity']
                st.info(f"📦 Quantidade Disponível: **{available:.8f}** {symbol.replace('USDT', '')}")

                if quantity > available:
                    st.error(f"⚠️ Quantidade insuficiente!")
            else:
                st.error(f"⚠️ Você não possui {symbol}")
    else:
        st.warning(f"⚠️ Preço de {symbol} não disponível. Clique em '🔄 Atualizar Preço' na sidebar")

    # Botão de enviar ordem
    st.markdown("---")

    if st.button("✅ Enviar Ordem", type="primary", use_container_width=True, key="submit_order_btn"):
        try:
            # Converter tipo de ordem
            order_type_enum = {
                "Market": OrderType.MARKET,
                "Limit": OrderType.LIMIT,
                "Stop Loss": OrderType.STOP_LOSS,
                "Take Profit": OrderType.TAKE_PROFIT
            }[order_type]

            side_enum = OrderSide.BUY if side == "BUY" else OrderSide.SELL

            # Criar ordem
            order = simulator.create_order(
                symbol=symbol,
                order_type=order_type_enum,
                side=side_enum,
                quantity=quantity,
                price=price,
                stop_price=stop_price,
                current_price=current_price
            )

            # Salvar no MongoDB
            save_simulator_to_mongodb(simulator, mongodb_collection)

            # Feedback
            if order['status'] == OrderStatus.EXECUTED.value:
                st.success(f"✅ Ordem executada com sucesso! ID: #{order['id']}")
                st.balloons()
            elif order['status'] == OrderStatus.PENDING.value:
                st.success(f"✅ Ordem criada e aguardando execução! ID: #{order['id']}")
            else:
                st.error(f"❌ Ordem cancelada: {order.get('cancel_reason', 'Erro desconhecido')}")

            st.rerun()

        except Exception as e:
            st.error(f"❌ Erro ao criar ordem: {str(e)}")
            logger.error(f"Erro ao criar ordem: {e}")


def render_history(simulator: TradingSimulator):
    """Renderiza o histórico de trades e ordens."""

    st.subheader("📜 Histórico Completo")

    # Tabs para trades e ordens
    tab1, tab2 = st.tabs(["Trades Executados", "Todas as Ordens"])

    # Tab 1: Trades
    with tab1:
        if simulator.trades:
            trades_data = []
            for trade in simulator.trades:
                trades_data.append({
                    'ID': trade['id'],
                    'Símbolo': trade['symbol'],
                    'Quantidade': f"{trade['quantity']:.8f}",
                    'Preço Entrada': f"${trade['entry_price']:,.2f}",
                    'Preço Saída': f"${trade['exit_price']:,.2f}",
                    'P&L': f"${trade['pnl']:,.2f}",
                    'P&L %': f"{trade['pnl_percentage']:+.2f}%",
                    'Data': trade['executed_at'][:19]
                })

            df_trades = pd.DataFrame(trades_data)
            st.dataframe(df_trades, use_container_width=True)

            # Gráfico de P&L acumulado
            st.markdown("---")
            st.subheader("📈 P&L Acumulado")

            cumulative_pnl = []
            total = 0
            for trade in simulator.trades:
                total += trade['pnl']
                cumulative_pnl.append(total)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                y=cumulative_pnl,
                mode='lines+markers',
                name='P&L Acumulado',
                line=dict(color='green' if cumulative_pnl[-1] > 0 else 'red', width=3),
                marker=dict(size=8)
            ))

            fig.update_layout(
                title="Evolução do P&L",
                xaxis_title="Trade #",
                yaxis_title="P&L (USDT)",
                hovermode='x unified',
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info("Nenhum trade executado ainda")

    # Tab 2: Ordens
    with tab2:
        if simulator.orders:
            orders_data = []
            for order in simulator.orders:
                orders_data.append({
                    'ID': order['id'],
                    'Símbolo': order['symbol'],
                    'Tipo': order['type'].upper(),
                    'Lado': order['side'].upper(),
                    'Quantidade': order['quantity'],
                    'Preço': f"${order['price']:,.2f}" if order['price'] else '-',
                    'Stop': f"${order['stop_price']:,.2f}" if order['stop_price'] else '-',
                    'Status': order['status'].upper(),
                    'Preço Exec.': f"${order['executed_price']:,.2f}" if order['executed_price'] else '-',
                    'Criada': order['created_at'][:19],
                    'Executada': order['executed_at'][:19] if order['executed_at'] else '-'
                })

            df_orders = pd.DataFrame(orders_data)
            st.dataframe(df_orders, use_container_width=True)

        else:
            st.info("Nenhuma ordem criada ainda")
