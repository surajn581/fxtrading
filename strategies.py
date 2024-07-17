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
    PreiousSellPrice = 0

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
            # TODO
            # update the prev buy price only when current buy price is higher than the last so that if we keep buying
            # the dip, we will not sell them until the current price is higher than our max buy price
            #if current_price > cls.PreviousBuyPrice:
            cls.PreviousBuyPrice = current_price
            return action
        if action == -1 and cls.PreviousBuyPrice*1.005 < current_price:     #multipying by 1.005 so that we make atleast 0.5% profit on each sell
            cls.PreiousSellPrice = current_price
            return action
        return 0
    
    def action(self, data, **kwargs):
        action = super().action(data, **kwargs)
        current_price = data[self.price_column].to_list()[-1]
        action = self.__class__.statefull_action( action, current_price )
        return action
    
class SMA( StatefullStrategyBase ):

    def __init__( self, short_period = 10, long_period = 50, price_column = 'mid' ):
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

    def __init__( self, period = 14, price_column = 'mid' ):
        self.period = period
        self.price_column = price_column

    def add_inicators(self, data, **kwargs):
        return calculate_rsi( data, self.period )
    
    def add_signal(self, data, **kwargs):
        data = rsi_signal( data )
        data.rename( columns = {'rsi_signal': 'signal'}, inplace = True )
        return data
    
class MACD( StatefullStrategyBase ):

    def __init__( self, short_period=12, long_period=26, signal_period=9, price_column = 'mid' ):
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

    def __init__( self, strategies:List[StrategyBase], price_column = 'mid' ):
        self.strategies = strategies
        self.price_column = price_column

    def action( self, data, **kwargs ):
        action = 0
        for strategy in self.strategies:
            action+=strategy.action( data )
        return action
    
class StatefullCompositeStrategyBase( CompositeStrategyBase ):

    PreviousBuyPrice = np.inf
    PreiousSellPrice = 0

    @classmethod
    def statefull_action(cls, action, current_price):
        if action == 1:
            # TODO
            # update the prev buy price only when current buy price is higher than the last so that if we keep buying
            # the dip, we will not sell them until the current price is higher than our max buy price
            #if current_price > cls.PreviousBuyPrice:
            cls.PreviousBuyPrice = current_price
            return action
        if action == -1 and cls.PreviousBuyPrice < current_price:
            cls.PreiousSellPrice = current_price
            return action
        return 0
    
    def action(self, data, **kwargs):
        action = super().action(data, **kwargs)
        current_price = data[self.price_column].to_list()[-1]
        action = self.__class__.statefull_action( action, current_price )
        return action
    
class StateFullComposite( StatefullCompositeStrategyBase ):
    pass