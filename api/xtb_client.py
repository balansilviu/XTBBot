# -*- coding utf-8 -*-

"""
XTBApi.api
~~~~~~~

Main module for XTB API Client
"""

import enum
import json
import logging
import time
from datetime import datetime
from websocket import create_connection
from websocket._exceptions import WebSocketConnectionClosedException

from XTBApi.exceptions import *

LOGGER = logging.getLogger('XTBApi.api')
logging.disable(logging.CRITICAL)


LOGIN_TIMEOUT = 120
MAX_TIME_INTERVAL = 0.200

# Enums
class STATUS(enum.Enum):
    LOGGED = enum.auto()
    NOT_LOGGED = enum.auto()

class MODES(enum.Enum):
    BUY = 0
    SELL = 1
    BUY_LIMIT = 2
    SELL_LIMIT = 3
    BUY_STOP = 4
    SELL_STOP = 5
    BALANCE = 6
    CREDIT = 7

class TRANS_TYPES(enum.Enum):
    OPEN = 0
    PENDING = 1
    CLOSE = 2
    MODIFY = 3
    DELETE = 4

class PERIOD(enum.Enum):
    ONE_MINUTE = 1
    FIVE_MINUTES = 5
    FIFTEEN_MINUTES = 15
    THIRTY_MINUTES = 30
    ONE_HOUR = 60
    FOUR_HOURS = 240
    ONE_DAY = 1440
    ONE_WEEK = 10080
    ONE_MONTH = 43200

# Helper Functions
def _get_data(command, **parameters):
    data = {
        "command": command,
    }
    if parameters:
        data['arguments'] = {}
        for (key, value) in parameters.items():
            data['arguments'][key] = value
    return data

def _check_mode(mode):
    """check if mode is acceptable"""
    modes = [x.value for x in MODES]
    if mode not in modes:
        raise ValueError("mode must be in {}".format(modes))

def _check_period(period):
    """check if period is acceptable"""
    if period not in [x.value for x in PERIOD]:
        raise ValueError("Period: {} not acceptable".format(period))

def _check_volume(volume):
    """normalize volume"""
    if not isinstance(volume, float):
        try:
            return float(volume)
        except Exception:
            raise ValueError("vol must be float")
    else:
        return volume

# Base Client Class
class BaseClient(object):
    """main client class"""

    def __init__(self):
        self.ws = None
        self._login_data = None
        self._time_last_request = time.time() - MAX_TIME_INTERVAL
        self.status = STATUS.NOT_LOGGED
        self.username = []
        self.password = []
        LOGGER.debug("BaseClient initialized")
        self.LOGGER = logging.getLogger('XTBApi.api.BaseClient')

    def _login_decorator(self, func, *args, **kwargs):
        if self.status == STATUS.NOT_LOGGED:
            raise NotLogged()
        try:
            return func(*args, **kwargs)
        except SocketError:
            LOGGER.info("Re-logging in due to LOGIN_TIMEOUT gone")
            self.login(self._login_data[0], self._login_data[1])
            return func(*args, **kwargs)
        except Exception as e:
            LOGGER.warning(e)
            self.login(self._login_data[0], self._login_data[1])
            return func(*args, **kwargs)

    def _send_command(self, dict_data):
        """send command to api"""
        time_interval = time.time() - self._time_last_request
        self.LOGGER.debug("Request interval took {} s.".format(time_interval))
        if time_interval < MAX_TIME_INTERVAL:
            time.sleep(MAX_TIME_INTERVAL - time_interval)
        try:
            self.ws.send(json.dumps(dict_data))
            response = self.ws.recv()
        except WebSocketConnectionClosedException:
            raise SocketError()
        self._time_last_request = time.time()
        res = json.loads(response)
        if res['status'] is False:
            self.LOGGER.error(f"Command failed with response: {res}")
            raise CommandFailed(res)
        if 'returnData' in res.keys():
            self.LOGGER.info("Command done")
            self.LOGGER.debug(res['returnData'])
            return res['returnData']

    def _send_command_with_check(self, dict_data):
        """send command with login check"""
        return self._login_decorator(self._send_command, dict_data)

    def login(self, user_id, password, mode='demo'):
        self.username = user_id
        self.password = password
        """login command"""
        data = _get_data("login", userId=user_id, password=password)
        print(f"Sending data: {data}")  # For debugging
        self.ws = create_connection(f"wss://ws.xtb.com/{mode}")
        response = self._send_command(data)
        self._login_data = (user_id, password)
        self.status = STATUS.LOGGED
        self.LOGGER.info("Login command executed")
        return response
    
    def retry_login(self, mode='demo'):
        """login command"""
        data = _get_data("login", userId=self.username, password=self.password)
        # print(f"Sending data: {data}")  # For debugging
        self.ws = create_connection(f"wss://ws.xtb.com/{mode}")
        response = self._send_command(data)
        self._login_data = (self.username, self.password)
        self.status = STATUS.LOGGED
        self.LOGGER.info("Login command executed")
        return response

    def logout(self):
        """logout command"""
        data = _get_data("logout")
        response = self._send_command(data)
        self.status = STATUS.NOT_LOGGED
        self.LOGGER.info("Logout command executed")
        return response

    def get_all_symbols(self):
        """getAllSymbols command"""
        data = _get_data("getAllSymbols")
        return self._send_command_with_check(data)

    def get_calendar(self):
        """getCalendar command"""
        data = _get_data("getCalendar")
        self.LOGGER.info("Get calendar command executed")
        return self._send_command_with_check(data)

    def get_chart_last_request(self, symbol, period, start):
        """getChartLastRequest command"""
        _check_period(period)
        args = {
            "period": period,
            "start": start * 1000,
            "symbol": symbol
        }
        data = _get_data("getChartLastRequest", info=args)
        self.LOGGER.info(f"Get chart last request for {symbol} of period {period} from {start}...")
        return self._send_command_with_check(data)

    def get_chart_range_request(self, symbol, period, start, end, ticks):
        """getChartRangeRequest command"""
        if not isinstance(ticks, int):
            raise ValueError(f"Ticks value {ticks} must be int")
        self._check_login()
        args = {
            "end": end * 1000,
            "period": period,
            "start": start * 1000,
            "symbol": symbol,
            "ticks": ticks
        }
        data = _get_data("getChartRangeRequest", info=args)
        self.LOGGER.info(f"Get chart range request for {symbol} of {period} from {start} to {end} with ticks of {ticks}...")
        return self._send_command_with_check(data)

    def get_commission(self, symbol, volume):
        """getCommissionDef command"""
        volume = _check_volume(volume)
        data = _get_data("getCommissionDef", symbol=symbol, volume=volume)
        self.LOGGER.info(f"Get commission for {symbol} of {volume}...")
        return self._send_command_with_check(data)

    def get_margin_level(self):
        """getMarginLevel command"""
        data = _get_data("getMarginLevel")
        self.LOGGER.info("Get margin level command executed")
        return self._send_command_with_check(data)

    def get_margin_trade(self, symbol, volume):
        """getMarginTrade command"""
        volume = _check_volume(volume)
        data = _get_data("getMarginTrade", symbol=symbol, volume=volume)
        self.LOGGER.info(f"Get margin trade for {symbol} of {volume}...")
        return self._send_command_with_check(data)

    def get_profit_calculation(self, symbol, mode, volume, op_price, cl_price):
        """getProfitCalculation command"""
        _check_mode(mode)
        volume = _check_volume(volume)
        data = _get_data("getProfitCalculation", closePrice=cl_price, cmd=mode, openPrice=op_price, symbol=symbol, volume=volume)
        self.LOGGER.info(f"Get profit calculation for {symbol} of {volume} from {op_price} to {cl_price} in mode {mode}...")
        return self._send_command_with_check(data)

    def get_server_time(self):
        """getServerTime command"""
        data = _get_data("getServerTime")
        self.LOGGER.info("Get server time command executed")
        return self._send_command_with_check(data)

    def get_symbol(self, symbol):
        """getSymbol command"""
        data = _get_data("getSymbol", symbol=symbol)
        self.LOGGER.info(f"Get symbol {symbol} command executed")
        return self._send_command_with_check(data)

    def get_tick_prices(self, symbols, start, level=0):
        """getTickPrices command"""
        data = _get_data("getTickPrices", level=level, symbols=symbols, timestamp=start)
        self.LOGGER.info(f"Get tick prices of {symbols} from {start} with level {level}...")
        return self._send_command_with_check(data)

    def get_trade_records(self, trade_position_list):
        """getTradeRecords command"""
        data = _get_data("getTradeRecords", orders=trade_position_list)
        self.LOGGER.info(f"Get trade records of len {len(trade_position_list)}...")
        return self._send_command_with_check(data)

    def get_trades(self, opened_only=True):
        """getTrades command"""
        data = _get_data("getTrades", openedOnly=opened_only)
        self.LOGGER.info("Get trades command executed")
        return self._send_command_with_check(data)
    
    def get_trade_status(self, opened_only=True):
        """getTrades command"""
        data = _get_data("getTradeStatus", openedOnly=opened_only)
        self.LOGGER.info("Get trades command executed")
        return self._send_command_with_check(data)

    def get_trades_history(self, start, end):
        """getTradesHistory command"""
        data = _get_data("getTradesHistory", end=end, start=start)
        self.LOGGER.info(f"Get trades history from {start} to {end} command executed")
        return self._send_command_with_check(data)
    
    def get_last_closed_trade(self):
        """getTradesHistory command"""
        return self.get_trades_history(0, 0)[0]

    def get_trading_hours(self, trade_position_list):
        """getTradingHours command"""
        data = _get_data("getTradingHours", symbols=trade_position_list)
        self.LOGGER.info(f"Get trading hours of len {len(trade_position_list)} command executed")
        response = self._send_command_with_check(data)
        for symbol in response:
            for day in symbol['trading']:
                day['fromT'] = int(day['fromT'] / 1000)
                day['toT'] = int(day['toT'] / 1000)
            for day in symbol['quotes']:
                day['fromT'] = int(day['fromT'] / 1000)
                day['toT'] = int(day['toT'] / 1000)
        return response

    def get_version(self):
        """getVersion command"""
        data = _get_data("getVersion")
        self.LOGGER.info("Get version command executed")
        return self._send_command_with_check(data)

    def ping(self):
        """ping command"""
        data = _get_data("ping")
        self.LOGGER.info("Ping command executed")
        self._send_command_with_check(data)

    def trade_transaction(self, symbol, mode, trans_type, volume, stop_loss=0, take_profit=0, **kwargs):
        """tradeTransaction command"""
        if trans_type not in [x.value for x in TRANS_TYPES]:
            raise ValueError(f"Type must be in {[x for x in TRANS_TYPES]}")
        stop_loss = float(stop_loss)
        take_profit = float(take_profit)
        accepted_values = ['order', 'price', 'expiration', 'customComment', 'offset', 'sl', 'tp']
        assert all([val in accepted_values for val in kwargs.keys()])
        _check_mode(mode)
        volume = _check_volume(volume)
        info = {
            'cmd': mode,
            'symbol': symbol,
            'type': trans_type,
            'volume': volume,
            'sl': stop_loss,
            'tp': take_profit
        }
        info.update(kwargs)
        data = _get_data("tradeTransaction", tradeTransInfo=info)
        name_of_mode = [x.name for x in MODES if x.value == mode][0]
        name_of_type = [x.name for x in TRANS_TYPES if x.value == trans_type][0]
        self.LOGGER.info(f"Trade transaction of {symbol} in mode {name_of_mode} with type {name_of_type} for volume {volume}...")
        return self._send_command_with_check(data)

    def trade_transaction_status(self, order_id):
        """tradeTransactionStatus command"""
        data = _get_data("tradeTransactionStatus", order=order_id)
        self.LOGGER.info(f"Trade transaction status for {order_id} command executed")
        return self._send_command_with_check(data)

    def get_user_data(self):
        """getCurrentUserData command"""
        data = _get_data("getCurrentUserData")
        self.LOGGER.info("Get user data command executed")
        return self._send_command_with_check(data)

# Advanced Client Class
class Client(BaseClient):
    """advanced class of client"""
    def __init__(self):
        super().__init__()
        self.trade_rec = {}
        self.LOGGER = logging.getLogger('XTBApi.api.Client')
        self.LOGGER.info("Client initialized")

    def check_if_market_open(self, list_of_symbols):
        """check if market is open for symbol in symbols"""
        _td = datetime.today()
        actual_tmsp = _td.hour * 3600 + _td.minute * 60 + _td.second
        response = self.get_trading_hours(list_of_symbols)
        market_values = {}
        for symbol in response:
            today_values = [day for day in symbol['trading'] if day['day'] == _td.isoweekday()][0]
            if today_values['fromT'] <= actual_tmsp <= today_values['toT']:
                market_values[symbol['symbol']] = True
            else:
                market_values[symbol['symbol']] = False
        return market_values

    def get_lastn_candle_history(self, symbol, timeframe_in_seconds, number):
        """get last n candles of timeframe"""
        acc_tmf = [60, 300, 900, 1800, 3600, 14400, 86400, 604800, 2592000]
        if timeframe_in_seconds not in acc_tmf:
            raise ValueError(f"timeframe not accepted, not in {', '.join([str(x) for x in acc_tmf])}")
        sec_prior = timeframe_in_seconds * number
        LOGGER.debug(f"sym: {symbol}, tmf: {timeframe_in_seconds}, {time.time() - sec_prior}")
        res = {'rateInfos': []}
        while len(res['rateInfos']) < number:
            res = self.get_chart_last_request(symbol, timeframe_in_seconds // 60, time.time() - sec_prior)
            LOGGER.debug(res)
            res['rateInfos'] = res['rateInfos'][-number:]
            sec_prior *= 3
        candle_history = []
        for candle in res['rateInfos']:
            _pr = candle['open']
            op_pr = _pr / 10 ** res['digits']
            cl_pr = (_pr + candle['close']) / 10 ** res['digits']
            hg_pr = (_pr + candle['high']) / 10 ** res['digits']
            lw_pr = (_pr + candle['low']) / 10 ** res['digits']
            new_candle_entry = {'timestamp': candle['ctm'] / 1000, 'open': op_pr, 'close': cl_pr, 'high': hg_pr, 'low': lw_pr, 'volume': candle['vol']}
            candle_history.append(new_candle_entry)
        LOGGER.debug(candle_history)
        return candle_history

    def update_trades(self):
        """update trade list"""
        trades = self.get_trades()
        self.trade_rec.clear()
        for trade in trades:
            obj_trans = Transaction(trade)
            self.trade_rec[obj_trans.order_id] = obj_trans
        self.LOGGER.info(f"Updated {len(self.trade_rec)} trades")
        return self.trade_rec

    def get_trade_profit(self, trans_id):
        """get profit of trade"""
        self.update_trades()
        profit = self.trade_rec[trans_id].actual_profit
        self.LOGGER.info(f"Got trade profit of {profit}")
        return profit

    def open_trade(self, mode, symbol, volume, stop_loss=0, take_profit=0):
        """open trade transaction"""
        if mode in [MODES.BUY.value, MODES.SELL.value]:
            mode = [x for x in MODES if x.value == mode][0]
        elif mode in ['buy', 'sell']:
            modes = {'buy': MODES.BUY, 'sell': MODES.SELL}
            mode = modes[mode]
        else:
            raise ValueError("mode can be buy or sell")
        mode_name = mode.name
        mode = mode.value
        self.LOGGER.debug(f"Opening trade of {symbol} of {volume} with {mode_name}")
        conversion_mode = {MODES.BUY.value: 'ask', MODES.SELL.value: 'bid'}
        price = self.get_symbol(symbol)[conversion_mode[mode]]
        response = self.trade_transaction(symbol, mode, 0, volume, stop_loss=stop_loss, take_profit=take_profit, price=price)
        self.update_trades()
        status = self.trade_transaction_status(response['order'])['requestStatus']
        self.LOGGER.debug(f"open_trade completed with status of {status}")
        if status != 3:
            raise TransactionRejected(status)
        return response
    
    def open_trade_stop_loss(self, mode, symbol, volume, stop_loss=0, take_profit=0):
        """open trade transaction"""
        if mode in [MODES.BUY.value, MODES.SELL.value]:
            mode = [x for x in MODES if x.value == mode][0]
        elif mode in ['buy', 'sell']:
            modes = {'buy': MODES.BUY, 'sell': MODES.SELL}
            mode = modes[mode]
        else:
            raise ValueError("mode can be buy or sell")
        mode_name = mode.name
        mode = mode.value
        self.LOGGER.debug(f"Opening trade of {symbol} of {volume} with {mode_name}")
        conversion_mode = {MODES.BUY.value: 'ask', MODES.SELL.value: 'bid'}
        price = self.get_symbol(symbol)[conversion_mode[mode]]
        if mode == MODES.BUY.value:
            print(price-stop_loss)
            response = self.trade_transaction(symbol, mode, 0, volume, stop_loss=round((price-stop_loss),5), take_profit=take_profit, price=price)
        else:
            response = self.trade_transaction(symbol, mode, 0, volume, stop_loss=round((price+stop_loss),5), take_profit=take_profit, price=price)
        self.update_trades()
        status = self.trade_transaction_status(response['order'])['requestStatus']
        self.LOGGER.debug(f"open_trade completed with status of {status}")
        if status != 3:
            raise TransactionRejected(status)
        return response

    def close_trade(self, trans):
        """close trade transaction"""
        if isinstance(trans, Transaction):
            order_id = trans.order_id
        else:
            order_id = trans
        self.update_trades()
        return self._close_trade_only(order_id)

    def close_all_trades(self):
        """close all trades"""
        self.update_trades()
        self.LOGGER.debug(f"Closing {len(self.trade_rec)} trades")
        trade_ids = self.trade_rec.keys()
        for trade_id in trade_ids:
            try:
                self._close_trade_only(trade_id)
            except Exception as e:
                self.LOGGER.error(f"Error closing trade {trade_id} on attempt: {e}")

    def _close_trade_only(self, order_id):
        """faster but less secure"""
        trade = self.trade_rec[order_id]
        self.LOGGER.debug(f"Closing trade {order_id}")
        try:
            response = self.trade_transaction(trade.symbol, 0, 2, trade.volume, order=trade.order_id, price=trade.price)
        except CommandFailed as e:
            if e.err_code == 'BE51':  # order already closed
                self.LOGGER.debug("BE51 error code noticed")
                return 'BE51'
            else:
                raise
        status = self.trade_transaction_status(response['order'])['requestStatus']
        self.LOGGER.debug(f"close_trade completed with status of {status}")
        if status != 3:
            raise TransactionRejected(status)
        return response

# Transaction Class
class Transaction(object):
    def __init__(self, trans_dict):
        self._trans_dict = trans_dict
        self.mode = {0: 'buy', 1: 'sell'}[trans_dict['cmd']]
        self.order_id = trans_dict['order']
        self.symbol = trans_dict['symbol']
        self.volume = trans_dict['volume']
        self.price = trans_dict['close_price']
        self.actual_profit = trans_dict['profit']
        self.timestamp = trans_dict['open_time'] / 1000
        LOGGER.debug(f"Transaction {self.order_id} initialized")
