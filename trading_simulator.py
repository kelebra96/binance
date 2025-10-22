"""
Simulador de Trading de Criptomoedas
Permite treinar estratégias sem risco real com ordens de mercado, limite, stop loss e take profit.
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum
import pandas as pd
from pymongo import MongoClient
from pymongo.collection import Collection
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Tipos de ordem disponíveis."""
    MARKET = "market"  # Executa imediatamente ao preço de mercado
    LIMIT = "limit"    # Executa quando preço atingir valor especificado
    STOP_LOSS = "stop_loss"  # Venda automática para limitar perdas
    TAKE_PROFIT = "take_profit"  # Venda automática para garantir lucros


class OrderSide(Enum):
    """Lado da ordem (compra ou venda)."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Status da ordem."""
    PENDING = "pending"      # Aguardando execução
    EXECUTED = "executed"    # Executada
    CANCELLED = "cancelled"  # Cancelada
    EXPIRED = "expired"      # Expirada


class TradingSimulator:
    """
    Simulador de trading com gerenciamento de ordens, carteira e histórico.
    """

    def __init__(self, initial_balance: float = 10000.0):
        """
        Inicializa o simulador de trading.

        Args:
            initial_balance: Saldo inicial em USDT
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance  # Saldo disponível em USDT
        self.positions: Dict[str, Dict] = {}  # Posições abertas {symbol: {quantity, avg_price, ...}}
        self.orders: List[Dict] = []  # Lista de todas as ordens
        self.trades: List[Dict] = []  # Histórico de trades executados

        logger.info(f"Simulador inicializado com saldo: ${initial_balance:.2f}")

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """
        Calcula o valor total do portfólio (saldo + posições).

        Args:
            current_prices: Dicionário com preços atuais {symbol: price}

        Returns:
            float: Valor total do portfólio em USDT
        """
        total_value = self.balance

        for symbol, position in self.positions.items():
            if symbol in current_prices:
                position_value = position['quantity'] * current_prices[symbol]
                total_value += position_value

        return total_value

    def get_pnl(self, current_prices: Dict[str, float]) -> Tuple[float, float]:
        """
        Calcula lucro/perda absoluto e percentual.

        Args:
            current_prices: Dicionário com preços atuais

        Returns:
            Tuple[float, float]: (P&L absoluto, P&L percentual)
        """
        current_value = self.get_portfolio_value(current_prices)
        pnl_absolute = current_value - self.initial_balance
        pnl_percentage = (pnl_absolute / self.initial_balance) * 100

        return pnl_absolute, pnl_percentage

    def create_order(
        self,
        symbol: str,
        order_type: OrderType,
        side: OrderSide,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        current_price: Optional[float] = None
    ) -> Dict:
        """
        Cria uma nova ordem.

        Args:
            symbol: Símbolo da criptomoeda (ex: BTCUSDT)
            order_type: Tipo da ordem
            side: Lado da ordem (BUY/SELL)
            quantity: Quantidade a comprar/vender
            price: Preço limite (para limit orders)
            stop_price: Preço de stop (para stop loss/take profit)
            current_price: Preço atual de mercado (para market orders)

        Returns:
            Dict: Ordem criada
        """
        order = {
            'id': len(self.orders) + 1,
            'symbol': symbol,
            'type': order_type.value,
            'side': side.value,
            'quantity': quantity,
            'price': price,
            'stop_price': stop_price,
            'status': OrderStatus.PENDING.value,
            'created_at': datetime.now().isoformat(),
            'executed_at': None,
            'executed_price': None
        }

        # Market orders são executadas imediatamente
        if order_type == OrderType.MARKET:
            if current_price is None:
                raise ValueError("current_price é obrigatório para market orders")

            success, message = self._execute_order(order, current_price)
            if not success:
                order['status'] = OrderStatus.CANCELLED.value
                order['cancel_reason'] = message

        self.orders.append(order)
        logger.info(f"Ordem criada: {order['id']} - {side.value} {quantity} {symbol} @ {price or current_price}")

        return order

    def _execute_order(self, order: Dict, execution_price: float) -> Tuple[bool, str]:
        """
        Executa uma ordem.

        Args:
            order: Ordem a ser executada
            execution_price: Preço de execução

        Returns:
            Tuple[bool, str]: (sucesso, mensagem)
        """
        symbol = order['symbol']
        side = order['side']
        quantity = order['quantity']
        order_cost = quantity * execution_price

        # Verificar fundos para compra
        if side == OrderSide.BUY.value:
            if order_cost > self.balance:
                return False, f"Saldo insuficiente. Necessário: ${order_cost:.2f}, Disponível: ${self.balance:.2f}"

            # Deduzir do saldo
            self.balance -= order_cost

            # Adicionar/atualizar posição
            if symbol not in self.positions:
                self.positions[symbol] = {
                    'quantity': 0,
                    'avg_price': 0,
                    'invested': 0
                }

            position = self.positions[symbol]
            total_invested = position['invested'] + order_cost
            total_quantity = position['quantity'] + quantity

            position['avg_price'] = total_invested / total_quantity
            position['quantity'] = total_quantity
            position['invested'] = total_invested

        # Venda
        elif side == OrderSide.SELL.value:
            if symbol not in self.positions:
                return False, f"Posição não encontrada para {symbol}"

            position = self.positions[symbol]

            if quantity > position['quantity']:
                return False, f"Quantidade insuficiente. Disponível: {position['quantity']}, Solicitado: {quantity}"

            # Adicionar ao saldo
            sale_value = quantity * execution_price
            self.balance += sale_value

            # Calcular P&L desta venda
            cost_basis = quantity * position['avg_price']
            pnl = sale_value - cost_basis

            # Atualizar posição
            position['quantity'] -= quantity
            position['invested'] -= cost_basis

            # Remover posição se zerada
            if position['quantity'] == 0:
                del self.positions[symbol]

            # Registrar trade
            trade = {
                'id': len(self.trades) + 1,
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'entry_price': position['avg_price'],
                'exit_price': execution_price,
                'pnl': pnl,
                'pnl_percentage': (pnl / cost_basis) * 100,
                'executed_at': datetime.now().isoformat()
            }
            self.trades.append(trade)

        # Atualizar ordem
        order['status'] = OrderStatus.EXECUTED.value
        order['executed_at'] = datetime.now().isoformat()
        order['executed_price'] = execution_price

        logger.info(f"Ordem executada: {order['id']} - {side} {quantity} {symbol} @ ${execution_price:.2f}")

        return True, "Ordem executada com sucesso"

    def process_pending_orders(self, current_prices: Dict[str, float]) -> List[Dict]:
        """
        Processa ordens pendentes verificando se devem ser executadas.

        Args:
            current_prices: Dicionário com preços atuais {symbol: price}

        Returns:
            List[Dict]: Lista de ordens executadas
        """
        executed_orders = []

        for order in self.orders:
            if order['status'] != OrderStatus.PENDING.value:
                continue

            symbol = order['symbol']
            if symbol not in current_prices:
                continue

            current_price = current_prices[symbol]
            order_type = order['type']
            side = order['side']
            should_execute = False

            # Limit Order
            if order_type == OrderType.LIMIT.value:
                target_price = order['price']
                if side == OrderSide.BUY.value and current_price <= target_price:
                    should_execute = True
                elif side == OrderSide.SELL.value and current_price >= target_price:
                    should_execute = True

            # Stop Loss
            elif order_type == OrderType.STOP_LOSS.value:
                stop_price = order['stop_price']
                if current_price <= stop_price:
                    should_execute = True

            # Take Profit
            elif order_type == OrderType.TAKE_PROFIT.value:
                stop_price = order['stop_price']
                if current_price >= stop_price:
                    should_execute = True

            if should_execute:
                success, message = self._execute_order(order, current_price)
                if success:
                    executed_orders.append(order)
                    logger.info(f"Ordem pendente executada: {order['id']}")
                else:
                    order['status'] = OrderStatus.CANCELLED.value
                    order['cancel_reason'] = message
                    logger.warning(f"Ordem cancelada: {order['id']} - {message}")

        return executed_orders

    def cancel_order(self, order_id: int) -> bool:
        """
        Cancela uma ordem pendente.

        Args:
            order_id: ID da ordem

        Returns:
            bool: True se cancelada com sucesso
        """
        for order in self.orders:
            if order['id'] == order_id and order['status'] == OrderStatus.PENDING.value:
                order['status'] = OrderStatus.CANCELLED.value
                order['cancel_reason'] = "Cancelada pelo usuário"
                logger.info(f"Ordem cancelada: {order_id}")
                return True

        return False

    def get_statistics(self) -> Dict:
        """
        Calcula estatísticas de trading.

        Returns:
            Dict: Estatísticas completas
        """
        if not self.trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'total_pnl': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'best_trade': 0,
                'worst_trade': 0
            }

        winning_trades = [t for t in self.trades if t['pnl'] > 0]
        losing_trades = [t for t in self.trades if t['pnl'] < 0]

        total_pnl = sum(t['pnl'] for t in self.trades)
        avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades) if losing_trades else 0
        best_trade = max(t['pnl'] for t in self.trades)
        worst_trade = min(t['pnl'] for t in self.trades)

        return {
            'total_trades': len(self.trades),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': (len(winning_trades) / len(self.trades)) * 100,
            'total_pnl': total_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'best_trade': best_trade,
            'worst_trade': worst_trade
        }

    def to_dict(self) -> Dict:
        """Converte o estado do simulador para dicionário."""
        return {
            'initial_balance': self.initial_balance,
            'balance': self.balance,
            'positions': self.positions,
            'orders': self.orders,
            'trades': self.trades,
            'updated_at': datetime.now().isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'TradingSimulator':
        """Cria instância do simulador a partir de dicionário."""
        simulator = cls(initial_balance=data['initial_balance'])
        simulator.balance = data['balance']
        simulator.positions = data['positions']
        simulator.orders = data['orders']
        simulator.trades = data['trades']
        return simulator


def save_simulator_to_mongodb(simulator: TradingSimulator, collection: Collection, user_id: str = "default") -> bool:
    """
    Salva estado do simulador no MongoDB.

    Args:
        simulator: Instância do simulador
        collection: Coleção do MongoDB
        user_id: ID do usuário

    Returns:
        bool: True se salvo com sucesso
    """
    try:
        data = simulator.to_dict()
        data['user_id'] = user_id

        # Atualizar ou inserir
        collection.replace_one(
            {'user_id': user_id},
            data,
            upsert=True
        )

        logger.info(f"Simulador salvo no MongoDB para usuário: {user_id}")
        return True

    except Exception as e:
        logger.error(f"Erro ao salvar simulador no MongoDB: {e}")
        return False


def load_simulator_from_mongodb(collection: Collection, user_id: str = "default") -> Optional[TradingSimulator]:
    """
    Carrega estado do simulador do MongoDB.

    Args:
        collection: Coleção do MongoDB
        user_id: ID do usuário

    Returns:
        TradingSimulator: Instância do simulador ou None se não encontrado
    """
    try:
        data = collection.find_one({'user_id': user_id})

        if data:
            simulator = TradingSimulator.from_dict(data)
            logger.info(f"Simulador carregado do MongoDB para usuário: {user_id}")
            return simulator
        else:
            logger.info(f"Nenhum simulador encontrado para usuário: {user_id}")
            return None

    except Exception as e:
        logger.error(f"Erro ao carregar simulador do MongoDB: {e}")
        return None
