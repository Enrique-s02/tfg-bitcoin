"""
Script para construir la base de datos mensual del TFG:
"Análisis multifactorial de los determinantes del precio de Bitcoin".

El script descarga datos financieros desde Yahoo Finance/yfinance,
datos macroeconómicos desde FRED, transforma todas las series a frecuencia
mensual, crea variables derivadas y exporta el resultado a Excel.

Requisitos:
    pip install pandas numpy yfinance pandas-datareader openpyxl
"""

import numpy as np
import pandas as pd
import yfinance as yf
from pandas_datareader import data as pdr


# ============================================================
# 1. Parámetros generales
# ============================================================

START_DATE = "2016-01-01"
END_DATE = "2026-05-01"  # end es exclusivo en yfinance; así se incluye abril de 2026
OUTPUT_FILE = "base_datos_tfg_bitcoin.xlsx"


# ============================================================
# 2. Funciones auxiliares
# ============================================================

def download_yfinance_monthly(ticker: str, column_name: str) -> pd.DataFrame:
    """
    Descarga una serie financiera diaria desde Yahoo Finance/yfinance
    y la transforma a frecuencia mensual tomando el último cierre disponible
    de cada mes.
    """
    raw = yf.download(
        ticker,
        start=START_DATE,
        end=END_DATE,
        interval="1d",
        auto_adjust=True,
        progress=False,
    )

    if raw.empty:
        raise ValueError(f"No se han descargado datos para el ticker {ticker}")

    # yfinance puede devolver columnas simples o multiíndice según versión/ticker
    close = raw["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    monthly = close.resample("MS").last().to_frame(column_name)
    monthly.index.name = "date"
    return monthly


def download_fred_monthly(series_code: str, column_name: str) -> pd.DataFrame:
    """
    Descarga una serie mensual desde FRED y estandariza su índice temporal
    a inicio de mes para poder unirla con el resto de variables.
    """
    series = pdr.DataReader(series_code, "fred", START_DATE, END_DATE)
    series = series.rename(columns={series_code: column_name})
    series.index = series.index.to_period("M").to_timestamp()
    series.index.name = "date"
    return series


def add_halving_window(dataset: pd.DataFrame) -> pd.DataFrame:
    """
    Crea una variable dummy que vale 1 en el mes del halving y en los dos
    meses posteriores. En el resto de meses toma valor 0.
    """
    halving_dates = [
        "2016-07-09",
        "2020-05-11",
        "2024-04-19",
    ]

    halving_months = set()
    for event_date in halving_dates:
        event_month = pd.Timestamp(event_date).to_period("M").to_timestamp()
        for i in range(3):
            halving_months.add(event_month + pd.DateOffset(months=i))

    dataset["halving_window_3m"] = dataset.index.isin(halving_months).astype(int)
    return dataset


def build_dictionary() -> pd.DataFrame:
    """Crea el diccionario de variables del dataset final."""
    rows = [
        ["date", "Fecha mensual de referencia", "Elaboración propia", "Mensual", "Homogeneización temporal", "Clave temporal para unir todas las series"],
        ["btc_usd", "Precio mensual de Bitcoin en dólares", "Yahoo Finance / yfinance, ticker BTC-USD", "Diaria transformada a mensual", "Último cierre disponible de cada mes", "Variable principal del estudio"],
        ["btc_return", "Rentabilidad mensual de Bitcoin", "Elaboración propia a partir de btc_usd", "Mensual", "Diferencia logarítmica: ln(Pt/Pt-1)", "Mide el cambio relativo mensual de Bitcoin"],
        ["sp500", "Nivel mensual del índice S&P 500", "Yahoo Finance / yfinance, ticker ^GSPC", "Diaria transformada a mensual", "Último cierre disponible de cada mes", "Representa el mercado bursátil estadounidense"],
        ["sp500_return", "Rentabilidad mensual del S&P 500", "Elaboración propia a partir de sp500", "Mensual", "Diferencia logarítmica: ln(Pt/Pt-1)", "Permite comparar Bitcoin con un activo de riesgo tradicional"],
        ["gold_usd", "Precio mensual del oro en dólares", "Yahoo Finance / yfinance, ticker GC=F", "Diaria transformada a mensual", "Último cierre disponible de cada mes", "Representa un activo refugio tradicional"],
        ["gold_return", "Rentabilidad mensual del oro", "Elaboración propia a partir de gold_usd", "Mensual", "Diferencia logarítmica: ln(Pt/Pt-1)", "Permite comparar Bitcoin con el comportamiento del oro"],
        ["fed_funds_rate", "Tipo efectivo de los fondos federales de EE. UU.", "FRED, serie FEDFUNDS", "Mensual", "Dato mensual publicado por FRED", "Proxy de política monetaria y tipos de interés"],
        ["fed_funds_change", "Cambio mensual del tipo FED", "Elaboración propia a partir de fed_funds_rate", "Mensual", "Diferencia mensual: Fed_t - Fed_t-1", "Mide endurecimiento o relajación monetaria"],
        ["cpi_index", "Índice de precios al consumo de EE. UU.", "FRED, serie CPIAUCSL", "Mensual", "Dato mensual publicado por FRED", "Base para calcular la inflación interanual"],
        ["inflation_yoy", "Inflación interanual", "Elaboración propia a partir de cpi_index", "Mensual", "Variación interanual: CPI_t/CPI_t-12 - 1", "Mide la evolución anual del nivel de precios"],
        ["m2_money_stock", "Oferta monetaria M2 de EE. UU.", "FRED, serie M2SL", "Mensual", "Dato mensual publicado por FRED", "Proxy de liquidez monetaria"],
        ["m2_growth_yoy", "Crecimiento interanual de M2", "Elaboración propia a partir de m2_money_stock", "Mensual", "Variación interanual: M2_t/M2_t-12 - 1", "Mide expansión o contracción de la liquidez"],
        ["halving_window_3m", "Dummy de ventana de halving", "Elaboración propia a partir de fechas históricas de halving", "Mensual", "1 en el mes del halving y los dos posteriores; 0 en el resto", "Captura eventos internos relevantes del protocolo Bitcoin"],
        ["btc_volatility_3m", "Volatilidad móvil de Bitcoin a 3 meses", "Elaboración propia a partir de btc_return", "Mensual", "Desviación típica móvil de 3 meses", "Mide la inestabilidad reciente de Bitcoin"],
    ]
    return pd.DataFrame(
        rows,
        columns=["variable", "descripcion", "fuente", "frecuencia", "transformacion", "justificacion"],
    )


def build_sources_table() -> pd.DataFrame:
    """Crea una tabla con las fuentes de datos utilizadas."""
    rows = [
        ["Yahoo Finance / yfinance", "BTC-USD", "Precio histórico de Bitcoin en dólares", "https://finance.yahoo.com/quote/BTC-USD/history"],
        ["Yahoo Finance / yfinance", "^GSPC", "Nivel histórico del índice S&P 500", "https://finance.yahoo.com/quote/%5EGSPC/history"],
        ["Yahoo Finance / yfinance", "GC=F", "Precio histórico del oro", "https://finance.yahoo.com/quote/GC%3DF/history"],
        ["FRED", "FEDFUNDS", "Tipo efectivo de los fondos federales", "https://fred.stlouisfed.org/series/FEDFUNDS"],
        ["FRED", "CPIAUCSL", "Índice de precios al consumo de EE. UU.", "https://fred.stlouisfed.org/series/CPIAUCSL"],
        ["FRED", "M2SL", "Oferta monetaria M2 de EE. UU.", "https://fred.stlouisfed.org/series/M2SL"],
        ["Elaboración propia", "Halving", "Variable dummy creada a partir de las fechas de halving", "Fechas históricas de halvings de Bitcoin"],
    ]
    return pd.DataFrame(rows, columns=["fuente", "codigo", "descripcion", "url"])


def build_cleaning_table(dataset: pd.DataFrame) -> pd.DataFrame:
    """Resume las principales decisiones de limpieza y transformación."""
    rows = [
        ["Homogeneización temporal", "Las series financieras diarias se transformaron a frecuencia mensual tomando el último cierre disponible de cada mes."],
        ["Estandarización de fechas", "Todas las fechas se convirtieron al inicio del mes para poder integrar las series mediante una clave temporal común."],
        ["Integración de datos", "Las series se unieron en un único dataset utilizando la fecha mensual como índice común."],
        ["Orden cronológico", "El dataset se ordenó de forma ascendente desde enero de 2016 hasta abril de 2026."],
        ["Duplicados", f"Número de fechas duplicadas tras la integración: {dataset.index.duplicated().sum()}"],
        ["Valores nulos", "Los nulos de variables calculadas al inicio de la muestra se mantienen cuando son consecuencia natural de la fórmula, por ejemplo rentabilidades o variaciones interanuales."],
        ["Rentabilidades", "Las rentabilidades de Bitcoin, S&P 500 y oro se calcularon mediante diferencias logarítmicas mensuales."],
        ["Variables interanuales", "La inflación y el crecimiento de M2 se calcularon como variaciones respecto al mismo mes del año anterior."],
        ["Variable dummy", "La variable de halving toma valor 1 en el mes del evento y los dos meses posteriores; 0 en el resto."],
    ]
    return pd.DataFrame(rows, columns=["proceso", "descripcion"])


# ============================================================
# 3. Descarga y transformación de datos originales
# ============================================================

# Datos financieros desde Yahoo Finance / yfinance
btc = download_yfinance_monthly("BTC-USD", "btc_usd")
sp500 = download_yfinance_monthly("^GSPC", "sp500")
gold = download_yfinance_monthly("GC=F", "gold_usd")

# Datos macroeconómicos desde FRED
fed_funds = download_fred_monthly("FEDFUNDS", "fed_funds_rate")
cpi = download_fred_monthly("CPIAUCSL", "cpi_index")
m2 = download_fred_monthly("M2SL", "m2_money_stock")


# ============================================================
# 4. Integración del dataset
# ============================================================

dataset = pd.concat([btc, sp500, gold, fed_funds, cpi, m2], axis=1)
dataset = dataset.sort_index()
dataset = dataset[~dataset.index.duplicated(keep="first")]

# Mantener solo el rango temporal de análisis
dataset = dataset.loc[pd.Timestamp(START_DATE):pd.Timestamp("2026-04-01")]


# ============================================================
# 5. Creación de variables derivadas
# ============================================================

# Rentabilidades logarítmicas mensuales
dataset["btc_return"] = np.log(dataset["btc_usd"] / dataset["btc_usd"].shift(1))
dataset["sp500_return"] = np.log(dataset["sp500"] / dataset["sp500"].shift(1))
dataset["gold_return"] = np.log(dataset["gold_usd"] / dataset["gold_usd"].shift(1))

# Cambios y variaciones macroeconómicas
dataset["fed_funds_change"] = dataset["fed_funds_rate"].diff()
dataset["inflation_yoy"] = dataset["cpi_index"].pct_change(12)
dataset["m2_growth_yoy"] = dataset["m2_money_stock"].pct_change(12)

# Dummy de halvings
dataset = add_halving_window(dataset)

# Volatilidad móvil de Bitcoin a 3 meses
dataset["btc_volatility_3m"] = dataset["btc_return"].rolling(window=3).std()


# ============================================================
# 6. Orden final de columnas
# ============================================================

final_columns = [
    "btc_usd",
    "btc_return",
    "sp500",
    "sp500_return",
    "gold_usd",
    "gold_return",
    "fed_funds_rate",
    "fed_funds_change",
    "cpi_index",
    "inflation_yoy",
    "m2_money_stock",
    "m2_growth_yoy",
    "halving_window_3m",
    "btc_volatility_3m",
]

dataset = dataset[final_columns]

# Para Excel, convertimos el índice en columna explícita
dataset_excel = dataset.reset_index()


# ============================================================
# 7. Análisis exploratorio básico
# ============================================================

descriptive_stats = dataset.describe().T.reset_index().rename(columns={"index": "variable"})
correlation_matrix = dataset.corr(numeric_only=True).reset_index().rename(columns={"index": "variable"})
missing_values = dataset.isna().sum().reset_index()
missing_values.columns = ["variable", "num_missing_values"]
missing_values["pct_missing_values"] = missing_values["num_missing_values"] / len(dataset)


# ============================================================
# 8. Exportación a Excel
# ============================================================

with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    dataset_excel.to_excel(writer, sheet_name="Dataset_final", index=False)
    build_dictionary().to_excel(writer, sheet_name="Diccionario_variables", index=False)
    build_sources_table().to_excel(writer, sheet_name="Fuentes_datos", index=False)
    build_cleaning_table(dataset).to_excel(writer, sheet_name="Control_limpieza", index=False)
    descriptive_stats.to_excel(writer, sheet_name="Analisis_exploratorio", index=False)
    correlation_matrix.to_excel(writer, sheet_name="Correlaciones", index=False)
    missing_values.to_excel(writer, sheet_name="Valores_nulos", index=False)

print(f"Base de datos generada correctamente: {OUTPUT_FILE}")
print(f"Filas: {dataset_excel.shape[0]}")
print(f"Columnas: {dataset_excel.shape[1]}")
print("Columnas finales:")
print(list(dataset_excel.columns))
