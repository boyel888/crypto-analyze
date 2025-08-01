from flask import Flask, request, jsonify
import ccxt
import pandas as pd
import pandas_ta as ta # Library yang sangat membantu untuk indikator teknikal

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# Fungsi untuk membersihkan dan memvalidasi simbol
def validate_symbol(symbol_input):
    # Contoh: btc/usdt -> BTC/USDT
    return symbol_input.upper().replace('-', '/')

@app.route('/api/analyze', methods=['GET'])
def analyze_crypto():
    """
    Endpoint utama untuk menganalisis koin.
    Menerima parameter 'symbol' melalui query string.
    Contoh: /api/analyze?symbol=BTC/USDT
    """
    # 1. Ambil simbol dari parameter request
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({"error": "Parameter 'symbol' tidak ditemukan. Contoh: ?symbol=BTC/USDT"}), 400

    validated_symbol = validate_symbol(symbol)

    try:
        # 2. Inisialisasi exchange (kita pakai Binance sebagai contoh)
        exchange = ccxt.binance()

        # 3. Ambil data harga (OHLCV)
        # Ambil 200 candle terakhir pada timeframe 1 hari untuk perhitungan yang lebih akurat
        ohlcv = exchange.fetch_ohlcv(validated_symbol, '1d', limit=200)
        if not ohlcv:
            return jsonify({"error": f"Tidak dapat menemukan data untuk simbol {validated_symbol}"}), 404

        # 4. Konversi ke Pandas DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        # 5. Hitung Indikator Teknikal menggunakan pandas_ta
        # Anda bisa menambahkan indikator lain dengan mudah di sini
        df.ta.rsi(append=True)      # Relative Strength Index (RSI)
        df.ta.macd(append=True)     # Moving Average Convergence Divergence (MACD)
        df.ta.bbands(append=True)   # Bollinger Bands
        
        # Ambil data terbaru (baris terakhir)
        latest_data = df.iloc[-1]

        # 6. Siapkan hasil dalam format JSON
        result = {
            "symbol": validated_symbol,
            "close_price": latest_data['close'],
            "indicators": {
                "rsi": round(latest_data['RSI_14'], 2) if 'RSI_14' in latest_data else None,
                "macd": {
                    "macd_line": round(latest_data['MACD_12_26_9'], 2) if 'MACD_12_26_9' in latest_data else None,
                    "signal_line": round(latest_data['MACDs_12_26_9'], 2) if 'MACDs_12_26_9' in latest_data else None,
                    "histogram": round(latest_data['MACDh_12_26_9'], 2) if 'MACDh_12_26_9' in latest_data else None,
                },
                "bollinger_bands": {
                    "lower_band": round(latest_data['BBL_20_2.0'], 2) if 'BBL_20_2.0' in latest_data else None,
                    "middle_band": round(latest_data['BBM_20_2.0'], 2) if 'BBM_20_2.0' in latest_data else None,
                    "upper_band": round(latest_data['BBU_20_2.0'], 2) if 'BBU_20_2.0' in latest_data else None,
                }
            },
            "timestamp": latest_data['timestamp'].isoformat()
        }

        return jsonify(result)

    except ccxt.BadSymbol as e:
        return jsonify({"error": f"Simbol tidak valid atau tidak didukung oleh exchange: {str(e)}"}), 400
    except Exception as e:
        # Tangani error umum lainnya
        return jsonify({"error": f"Terjadi kesalahan internal: {str(e)}"}), 500

# Endpoint root untuk memastikan server berjalan
@app.route('/')
def home():
    return "Crypto Analysis API is running. Gunakan endpoint /api/analyze?symbol=NAMAKOIN"
