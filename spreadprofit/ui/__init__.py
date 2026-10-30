"""UI components and visual dashboard for spreadProfit."""

from spreadprofit.ui.charts import ChartsTab
from spreadprofit.ui.main import SpreadProfitApp, main
from spreadprofit.ui.portfolio import PortfolioTab
from spreadprofit.ui.transactions import TransactionsTab

__all__ = ["SpreadProfitApp", "main", "PortfolioTab", "TransactionsTab", "ChartsTab"]
