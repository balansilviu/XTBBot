import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def EMA(prices, period):
    # Convertim lista de prețuri la un array numpy de tip float64
    prices = np.array(prices, dtype=np.float64)
    
    # Calculăm factorul de multiplicare pentru EMA
    multiplier = 2 / (period + 1)
    
    # Inițializăm prima valoare EMA cu primul preț din listă
    ema = prices[0]
    
    # Calculăm EMA pentru fiecare preț începând de la al doilea
    for price in prices[1:]:
        ema = (price - ema) * multiplier + ema
    
    # Returnăm ultima valoare EMA calculată
    return ema

def SMA(prices, period):
    # Verificăm dacă lungimea listei de prețuri este mai mică decât perioada
    if len(prices) < period:
        raise ValueError("Numărul de prețuri trebuie să fie mai mare sau egal cu perioada")

    # Calculăm suma ultimelor 'period' prețuri
    sma = sum(prices[-period:]) / period
    
    # Returnăm valoarea SMA
    return sma

def RSI(prices, period=14):
    if len(prices) < period:
        raise ValueError("Numărul de prețuri trebuie să fie mai mare sau egal cu perioada")
    
    # Calculăm modificările zilnice ale prețului
    deltas = np.diff(prices)
    
    # Împărțim câștigurile și pierderile
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # Calculăm media mobilă a câștigurilor și pierderilor
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    # Calculăm RSI-ul inițial
    if avg_loss == 0:
        rs = float('inf')  # În cazul în care nu există pierderi
    else:
        rs = avg_gain / avg_loss
    
    rsi = 100 - (100 / (1 + rs))
    
    # Calculăm RSI pentru restul perioadelor
    for i in range(period, len(prices) - 1):
        gain = gains[i]
        loss = losses[i]
        
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        
        if avg_loss == 0:
            rs = float('inf')
        else:
            rs = avg_gain / avg_loss
        
        rsi = 100 - (100 / (1 + rs))
    
    return rsi



def TRUE_RANGE(df):
    df['high_low'] = df['high'] - df['low']
    df['high_prev_close'] = abs(df['high'] - df['close'].shift(1))
    df['low_prev_close'] = abs(df['low'] - df['close'].shift(1))
    
    df['True_Range'] = df[['high_low', 'high_prev_close', 'low_prev_close']].max(axis=1)
    
    return df

def ATR(df, period=14, atr_type='rma'):
    
    df = TRUE_RANGE(df)
    
    if atr_type == 'rma':
        df['ATR'] = df['True_Range'].ewm(alpha=1/period, adjust=False).mean()
    elif atr_type == 'sma':
        df['ATR'] = df['True_Range'].rolling(window=period).mean()
    elif atr_type == 'ema':
        df['ATR'] = df['True_Range'].ewm(span=period, adjust=False).mean()
    elif atr_type == 'wma':
        weights = pd.Series(range(1, period + 1))
        df['ATR'] = df['True_Range'].rolling(window=period).apply(lambda x: (weights*x).sum() / weights.sum(), raw=True)
    else:
        raise ValueError(f"Unknown ATR type: {atr_type}")
    
    # last_atr = round(df["ATR"].iloc[-1] * 10000 * 2, 1)
    return round(df["ATR"].iloc[-1], 5)

    