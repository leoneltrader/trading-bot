# -*- coding: utf-8 -*-

import ccxt
import pandas as pd
import numpy as np
import time
import os  # Para manejar variables de entorno
from datetime import datetime

# Configuración de la API de KuCoin desde variables de entorno
exchange = ccxt.kucoinfutures({
    "apiKey": os.getenv("KUCOIN_API_KEY"),
    "secret": os.getenv("KUCOIN_API_SECRET"),
    "password": os.getenv("KUCOIN_API_PASSWORD"),
    "options": {"defaultType": "future"}
})

# Parámetros de estrategia
PAIRS = ["BTC/USDT:USDT", "ETH/USDT:USDT", "LTC/USDT:USDT", "DOGE/USDT:USDT"]
ATR_MULTIPLIER = 2.5  
LIQUIDATION_THRESHOLD = 1.5  

# Función para obtener datos de mercado
def get_ohlcv(symbol, timeframe="1m", limit=50):
    try:
        bars = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df
    except Exception as e:
        print(f"Error obteniendo datos para {symbol}: {e}")
        return None

# Función para calcular ATR
def calculate_atr(df, period=14):
    df["TR"] = np.maximum(df["high"] - df["low"], np.maximum(abs(df["high"] - df["close"].shift(1)), abs(df["low"] - df["close"].shift(1))))
    df["ATR"] = df["TR"].rolling(window=period).mean()
    return df

# Función para generar señales
def generate_signals():
    signals = []
    for pair in PAIRS:
        df = get_ohlcv(pair)
        if df is None:
            continue
        df = calculate_atr(df)
        last_row = df.iloc[-1]

        if last_row["ATR"] > ATR_MULTIPLIER * df["ATR"].mean():
            direction = "BUY" if last_row["close"] > df["close"].mean() else "SELL"
            entry_price = last_row["close"]
            stop_loss = entry_price * (1.01 if direction == "BUY" else 0.99)
            take_profit = entry_price * (0.99 if direction == "BUY" else 1.01)

            signals.append({
                "timestamp": datetime.utcnow(),
                "pair": pair,
                "signal": direction,
                "entry": round(entry_price, 2),
                "stop_loss": round(stop_loss, 2),
                "take_profit": round(take_profit, 2),
            })
    return signals

# Loop principal
while True:
    signals = generate_signals()
    for signal in signals:
        print(f"{signal['timestamp']} - {signal['pair']} - {signal['signal']} - Entry: {signal['entry']}, SL: {signal['stop_loss']}, TP: {signal['take_profit']}")
    time.sleep(60)

