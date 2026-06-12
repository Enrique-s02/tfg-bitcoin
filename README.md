# tfg-bitcoin
Código utilizado para la construcción y limpieza de la base de datos del TFG sobre los determinantes del precio de Bitcoin

Este repositorio contiene el código utilizado para construir la base de datos del Trabajo de Fin de Grado sobre los determinantes del precio de Bitcoin.

El archivo principal es `base_de_datos_tfg_btc.py`, donde se realiza el proceso de extracción, limpieza, transformación e integración de los datos.

## Objetivo

El objetivo del código es generar una base de datos mensual que combine variables financieras, macroeconómicas y propias del ecosistema Bitcoin, con el fin de analizar qué factores pueden influir en el comportamiento del precio de Bitcoin.

## Fuentes de datos

Las variables financieras, como Bitcoin, S&P 500 y oro, se obtienen a través de Yahoo Finance mediante la librería `yfinance`.

Las variables macroeconómicas, como los tipos de interés, el índice de precios al consumo y la oferta monetaria M2, se obtienen desde FRED.

La variable de halving se construye manualmente a partir de las fechas históricas de los halvings de Bitcoin.

## Proceso realizado

El código realiza los siguientes pasos:

1. Descarga las series originales desde sus fuentes.
2. Transforma las variables financieras a frecuencia mensual.
3. Integra todas las series usando la fecha como clave común.
4. Limpia la base revisando fechas, duplicados y valores ausentes.
5. Crea variables derivadas como rentabilidades, inflación interanual, crecimiento de M2, variación de tipos y volatilidad móvil de Bitcoin.
6. Exporta el resultado final a un archivo Excel.

## Archivos del repositorio

- `base_de_datos_tfg_btc.py`: código principal para generar la base de datos.
- `requirements_tfg_bitcoin.txt`: librerías necesarias para ejecutar el código.

## Ejecución

Para instalar las librerías necesarias:

```bash
pip install -r requirements_tfg_bitcoin.txt
