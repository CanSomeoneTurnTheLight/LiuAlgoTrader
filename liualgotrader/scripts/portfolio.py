import asyncio
import uuid

import fire
from tabulate import tabulate

from liualgotrader.analytics import analysis
from liualgotrader.common.database import create_db_connection
from liualgotrader.common.types import AssetType
from liualgotrader.models.portfolio import Portfolio
from liualgotrader.reprocess.portfolio import account_transactions


def equity(portfolio_id: str):
    """Show current equity breakdown"""
    portfolio = asyncio.run(analysis.get_portfolio_equity(portfolio_id))
    if portfolio.empty:
        print("Empty portfolio")
        return

    print(
        tabulate(
            portfolio,
            headers=["symbol", "qty", "price ($)", "total ($)"],
            numalign="decimal",
            tablefmt="pretty",
            floatfmt=".2f",
            showindex=False,
        )
    )
    print(f"Number of stocks: {len(portfolio)}")


def account(portfolio_id: str):
    """Show account transactions for portfolio"""
    portfolio = asyncio.run(analysis.get_portfolio_cash(portfolio_id))
    if portfolio.empty:
        print("Empty portfolio transactions")
        return

    print(
        tabulate(
            portfolio,
            numalign="decimal",
            tablefmt="pretty",
            headers=["when", "amount ($)"],
            floatfmt=".2f",
        )
    )
    print(f"Number of transactions: {len(portfolio)}")


def recalc(portfolio_id):
    """Re-calculate portfolio's account transactions"""
    account_transactions(portfolio_id)


def create(account_size: float, credit_line: float, asset_type: str):
    """Create a new account"""
    portfolio_id = str(uuid.uuid4())
    try:
        asset = AssetType[asset_type]
    except KeyError:
        print(f"ASSET_TYPE {asset_type} not supported. aborting.")
        return

    asyncio.run(
        Portfolio.save(
            portfolio_id=portfolio_id,
            portfolio_size=account_size,
            credit=credit_line,
            parameters={},
            asset_type=asset,
        )
    )
    print(f"Portfolio ID {portfolio_id} created")


def trades(portfolio_id):
    """Display portfolio trades"""
    portfolio = analysis.load_trades_by_portfolio(portfolio_id)
    portfolio = (
        portfolio[["tstamp", "symbol", "operation", "qty", "price"]]
        .set_index("tstamp")
        .sort_index()
    )
    portfolio["total"] = portfolio.qty * portfolio.price
    portfolio = portfolio.round(2)
    print(
        tabulate(
            portfolio,
            numalign="decimal",
            tablefmt="pretty",
            headers=["when", "symbol", "op", "qty", "price ($)", "total ($)"],
            floatfmt=".2f",
        )
    )
    print(f"Number of trades: {len(portfolio)}")


def list():
    """List active portfolios"""

    data = []
    loop = asyncio.get_event_loop()
    loop.run_until_complete(create_db_connection())
    print("Portfolio(s):")
    data = loop.run_until_complete(Portfolio.list_portfolios())
    data = data[
        [
            "portfolio_id",
            "tstamp",
            "last_transaction",
            "size",
            "assets",
            "parameters",
        ]
    ]

    print(
        tabulate(
            data,
            headers=[
                "Id",
                "Created",
                "Last Used",
                "Size",
                "Asset Type",
                "Parameters",
            ],
            numalign="decimal",
            tablefmt="pretty",
            floatfmt=".2f",
            showindex=False,
        )
    )


def main_cli() -> None:
    fire.Fire(
        {
            "create": create,
            "equity": equity,
            "recalc": recalc,
            "account": account,
            "trades": trades,
            "list": list,
        },
        name="portfolio",
    )
