from abc import abstractmethod
from typing import List
import numpy as np
from signals import calculate_sma, sma_signal, calculate_rsi, rsi_signal, calculate_macd, macd_signal

class StrategyBase:

    @abstractmethod
    def add_inicators(self, data, **kwargs):
        ''' method that adds a columns into the dataframe eg: SMA_10, MACD etc '''
        pass

    @abstractmethod
    def add_signal(self, data, **kwargs):
        ''' method that uses the indicators to add a column 'signal' value with +1 (buy) or -1 (sell) '''
        pass

    def _add_signal(self, data, **kwargs):
        data = self.add_signal(data)
        assert 'signal' in data.columns, "add_signal must add a column 'signal' into the dataframe"
        return data

    def _run( self, data, **kwargs ):
        data = self.add_inicators(data, **kwargs)
        data = self._add_signal(data, **kwargs)
        return data

    def action(self, data, **kwargs):
        data = self._run(data, **kwargs)
        action = data['signal'].to_list()[-1]
        return action
    
class StatefullStrategyBase(StrategyBase):

    PreviousBuyPrice = np.inf
    PreviousSellPrice = 0
    PreviousBuyAverage = 0
    PreviousBuyCount = 0

    def __init__(self, is_statefull = True):
        self.is_statefull = is_statefull

    @abstractmethod
    def add_inicators(self, data, **kwargs):
        ''' method that adds a columns into the dataframe eg: SMA_10, MACD etc '''
        pass

    @abstractmethod
    def add_signal(self, data, **kwargs):
        ''' method that uses the indicators to add a column 'signal' value with +1 (buy) or -1 (sell) '''
        pass

    @classmethod
    def statefull_action(cls, action, current_price):
        if action == 1:
            cls.PreviousBuyAverage = ( (cls.PreviousBuyCount*cls.PreviousBuyAverage)+current_price )/(cls.PreviousBuyCount+1)
            cls.PreviousBuyCount = cls.PreviousBuyCount + 1
            return action
        if (action == -1) and (cls.PreviousBuyAverage < current_price):     #multipying by 1.005 so that we make atleast 0.5% profit on each sell
            print('sold at profit: {} avg buy price: {} current price: {}'.format(current_price-cls.PreviousBuyAverage, cls.PreviousBuyAverage, current_price))
            cls.PreiousSellPrice = current_price
            cls.PreviousBuyAverage = 0
            cls.PreviousBuyCount = 0
            return action
        elif action == -1:
            print('sell recommended but avg buy price: {} > current price: {}'.format(cls.PreviousBuyAverage, current_price))
            return 0
        return 0
    
    def action(self, data, **kwargs):
        action = super().action(data, **kwargs)
        if self.is_statefull:
            current_price = data[self.price_column].to_list()[-1]
            action = self.__class__.statefull_action( action, current_price )
        return action
    
class SMA( StatefullStrategyBase ):

    def __init__( self, short_period = 10, long_period = 50, price_column = 'mid', is_statefull = True ):
        super().__init__(is_statefull=is_statefull)
        self.short_period = short_period
        self.long_period = long_period
        self.price_column = price_column

    def add_inicators(self, data, **kwargs):
        return calculate_sma( data, self.short_period, self.long_period )
    
    def add_signal(self, data, **kwargs):
        data = sma_signal( data )
        data.rename( columns = {'sma_signal': 'signal'}, inplace = True )
        return data
    
class RSI( StatefullStrategyBase ):

    def __init__( self, period = 14, price_column = 'mid', is_statefull = True ):
        super().__init__(is_statefull=is_statefull)
        self.period = period
        self.price_column = price_column

    def add_inicators(self, data, **kwargs):
        return calculate_rsi( data, self.period )
    
    def add_signal(self, data, **kwargs):
        data = rsi_signal( data )
        data.rename( columns = {'rsi_signal': 'signal'}, inplace = True )
        return data
    
class MACD( StatefullStrategyBase ):

    def __init__( self, short_period=12, long_period=26, signal_period=9, price_column = 'mid', is_statefull = True ):
        super().__init__(is_statefull=is_statefull)
        self.short_period = short_period
        self.long_period = long_period
        self.signal_period = signal_period
        self.price_column = price_column

    def add_inicators(self, data, **kwargs):
        return calculate_macd( data, self.short_period, self.long_period, self.signal_period )
    
    def add_signal(self, data, **kwargs):
        data = macd_signal( data )
        data.rename( columns = {'macd_signal': 'signal'}, inplace = True )
        return data
    
class CompositeStrategyBase:

    def __init__( self, strategies:List[StrategyBase], price_column = 'mid', volume_column = 'quoteSize' ):
        self.strategies = strategies
        self.price_column = price_column
        self.volume_column = volume_column

    def action( self, data, **kwargs ):
        action = 0
        for strategy in self.strategies:
            action+=strategy.action( data )
        return action
    
class StatefullCompositeStrategyBase( CompositeStrategyBase ):

    BaseTradeQuantity = 1000
    PreviousBuyPrice = np.inf
    PreviousSellPrice = 0
    PreviousBuyAverage = 0
    PreviousBuyCount = 0
    TotalProfit = 0

    #holds the quantity that is yet to be purchased
    PreviousTickBuyMiss = 0

    #holds the quantity that is yet to be sold
    PreviousTickSellMiss = 0

    @classmethod
    def statefull_action(cls, action, current_price, current_volume):
        if action == 0:
            if cls.PreviousTickBuyMiss:
                action = 1            
            elif cls.PreviousTickSellMiss:
                action = -1
            else:
                return action
        if action in [1, 2, 3]:
            # maintaining a running average of our buying price so that we can use it to sell only when the selling price > avg buying price
            return action
        if (action in [-1, -2, -3]) and (cls.PreviousBuyCount>0) and (cls.PreviousBuyAverage < current_price):            
            return action
        return 0
    
    def action(self, data, **kwargs):
        cls = self.__class__
        action = super().action(data, **kwargs)
        current_price = data[self.price_column].to_list()[-1]
        current_volume = data[self.volume_column].to_list()[-1]
        action = cls.statefull_action( action, current_price, current_volume )

        if action == 0:
            trade_amount = 0
        elif action > 0:
            trade_amount = action * cls.BaseTradeQuantity + cls.PreviousTickBuyMiss
        else:
            trade_amount = cls.PreviousBuyCount

        miss = max( trade_amount - current_volume, 0 )
        trade_amount = trade_amount - miss
        if action>0:
            cls.PreviousTickBuyMiss = miss
        elif action<0:
            cls.PreviousTickSellMiss = miss

        if action == 0:
            trade_amount = 0
        elif action<0:
            print('sold {} units at profit: {} avg buy price: {} current price: {}'.format( trade_amount, current_price-cls.PreviousBuyAverage, cls.PreviousBuyAverage, current_price))
            cls.TotalProfit = cls.TotalProfit + trade_amount*(current_price-cls.PreviousBuyAverage)
            cls.PreviousSellPrice = current_price
            if cls.PreviousBuyCount - trade_amount == 0:
                cls.PreviousBuyCount = 0
                cls.PreviousBuyAverage = 0
            else:
                cls.PreviousBuyAverage = (cls.PreviousBuyAverage*cls.PreviousBuyCount - current_price*trade_amount)/(cls.PreviousBuyCount-trade_amount)
                cls.PreviousBuyCount = cls.PreviousBuyCount - trade_amount
        elif action>0:
            print('bought {} units at {}/unit'.format(trade_amount, current_price))
            cls.PreviousBuyCount = cls.PreviousBuyCount + trade_amount
            cls.PreviousBuyAverage = cls.PreviousBuyAverage + trade_amount*(current_price - cls.PreviousBuyAverage)/float(cls.PreviousBuyCount)

        if action!=0:
            print('total holding: {} at avg buy price: {}'.format(cls.PreviousBuyCount, cls.PreviousBuyAverage))
            print('total profit: {}'.format(cls.TotalProfit))

        return action, trade_amount * ( -1 if action<0 else 1 )
class StateFullComposite( StatefullCompositeStrategyBase ):
    pass