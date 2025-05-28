"""
Script de Coleta de Dados - Superfície de Juros
Coleta dados de curvas de juros do Brasil e dos EUA
"""

import pandas as pd
import numpy as np
import requests
import lxml.html
import re
import datetime
from bizdays import Calendar
from bcb import sgs
from scipy.interpolate import interp1d
import pandas_datareader as pdr
import os

# Funções auxiliares do modelo original
def to_numeric(elm):
    s = elm.text
    s = s.strip()
    s = s.replace(',', '.')
    return float(s)

def flatten_names(nx):
    for ix in range(len(nx)):
        if (nx[ix] != ""):
            last_name = nx[ix]
        nx[ix] = last_name
    x = [x[:3] for x in nx]
    return x

def recycle(s, i, m):
    assert len(s) % m == 0
    assert i < m
    assert i >= 0
    l = len(s)
    idx = list(range(i, l, m))
    return [s[i] for i in idx]

def contract_to_maturity(x):
    maturity_code = x[-3:]
    year = int(maturity_code[-2:]) + 2000
    m_ = dict(F = 1, G = 2, H = 3, J = 4, K = 5, M = 6,
              N = 7, Q = 8, U = 9, V = 10, X = 11, Z = 12)
    month_code = maturity_code[0]
    month = int(m_[month_code])
    return datetime.datetime(year, month, 1)

def get_contracts(refdate):
    def _cleanup(x):
        if x is None:
            return ''
        x = x.strip()\
             .replace('.', '')\
             .replace(',', '.')
        return x
    
    url = 'https://www2.bmf.com.br/pages/portal/bmfbovespa/lumis/lum-ajustes-do-pregao-ptBR.asp'
    res = requests.post(url, data=dict(dData1=refdate.strftime('%d/%m/%Y')), verify=False)
    root = lxml.html.fromstring(res.text)

    rx = re.compile(r'Atualizado em: (\d\d/\d\d/\d\d\d\d)')
    mx = rx.search(res.text)
    if mx is None:
        return None
    
    refdate = datetime.datetime.strptime(mx.group(1), '%d/%m/%Y')
    table = root.xpath("//table[contains(@id, 'tblDadosAjustes')]")
    if len(table) == 0:
        return None
    
    data = [_cleanup(td.text) for td in table[0].xpath('//td')]
    df = pd.DataFrame({
        'DataRef': refdate,
        'Mercadoria': flatten_names(recycle(data, 0, 6)),
        'CDVencimento': recycle(data, 1, 6),
        'PUAnterior': recycle(data, 2, 6),
        'PUAtual': recycle(data, 3, 6),
        'Variacao': recycle(data, 4, 6)
    })
    df['Vencimento'] = df['CDVencimento'].map(contract_to_maturity)
    df['PUAnterior'] = df['PUAnterior'].astype('float64')
    df['PUAtual'] = df['PUAtual'].astype('float64')
    df['Variacao'] = df['Variacao'].astype('float64')
    return df

def retrieve_us_yield_curve_data():
    """Coleta dados das curvas de juros dos EUA via FRED"""
    start = '1990-01-01'
    tickers = ['GS30', 'GS10', 'GS5', 'GS3', 'GS2', 'GS1', 'GS6m', 'GS3m', 'GS1m']
    df = pdr.get_data_fred(tickers, start)
    df.columns = ['30Y', '10Y', '5Y', '3Y', '2Y', '1Y', '6M', '3M', '1M']
    df.index = pd.to_datetime(df.index)
    return df

def coleta_dados_brasil():
    """Coleta dados do Brasil"""
    print("Iniciando coleta de dados do Brasil...")
    
    # Caminho para a base existente
    base_path = 'Dados/Base_Bruta.parquet'
    
    # Carrega base existente ou cria uma nova
    if os.path.exists(base_path):
        base = pd.read_parquet(base_path)
        last_date = base['DataRef'].drop_duplicates().sort_values(ascending=False).head(1).iloc[0]
    else:
        base = pd.DataFrame()
        last_date = datetime.datetime(2020, 1, 1)
    
    print(f"Última data na base: {last_date}")
    
    # Calendario de mercado
    MARKET_CALENDAR = Calendar.load('ANBIMA')
    
    # Datas para coletar
    refdate = MARKET_CALENDAR.seq(last_date, 
                                datetime.datetime.today() - datetime.timedelta(days=1))
    
    print(f"Coletando dados para {len(refdate)} datas...")
    
    # Lista para armazenar DataFrames
    lista = []
    
    # Itera sobre cada data
    for i, date in enumerate(refdate):
        try:
            print(f"Processando {i+1}/{len(refdate)}: {date}")
            curve = get_contracts(date)
            
            if curve is not None:
                curve['date'] = date
                lista.append(curve)
            else:
                print(f"Nenhuma curva encontrada para a data {date}")
        
        except Exception as e:
            print(f"Erro ao processar a data {date}: {e}")
    
    if lista:
        # Concatena todos os DataFrames
        df_final = pd.concat(lista, ignore_index=True)
        
        # Filtra apenas DI1
        df_new = df_final[(df_final['Mercadoria'] == 'DI1') & 
                         (df_final['PUAtual'] != 100000.0)].copy()
        df_new = df_new.reset_index(drop=True, inplace=False)
        
        # Append à base existente
        if not base.empty:
            di1 = pd.concat([base, df_new], ignore_index=True)
        else:
            di1 = df_new
        
        # Salva a base atualizada
        os.makedirs(os.path.dirname(base_path), exist_ok=True)
        di1.to_parquet(base_path, index=True)
        print(f"Base atualizada salva: {base_path}")
        
        return di1
    else:
        print("Nenhum dado novo coletado")
        return base

def coleta_dados_eua():
    """Coleta dados dos EUA"""
    print("Coletando dados dos EUA...")
    
    try:
        df_us = retrieve_us_yield_curve_data()
        
        # Salva os dados
        eua_path = 'Dados/juros_eua_bruto.parquet'
        os.makedirs(os.path.dirname(eua_path), exist_ok=True)
        df_us.to_parquet(eua_path)
        print(f"Dados dos EUA salvos: {eua_path}")
        
        return df_us
    
    except Exception as e:
        print(f"Erro ao coletar dados dos EUA: {e}")
        return None

def main():
    """Função principal de coleta"""
    print("=== COLETA DE DADOS - SUPERFÍCIE DE JUROS ===")
    
    # Coleta dados do Brasil
    dados_brasil = coleta_dados_brasil()
    
    # Coleta dados dos EUA
    dados_eua = coleta_dados_eua()
    
    print("=== COLETA FINALIZADA ===")
    
    if dados_brasil is not None:
        print(f"Brasil: {len(dados_brasil)} registros coletados")
    
    if dados_eua is not None:
        print(f"EUA: {len(dados_eua)} registros coletados")

if __name__ == "__main__":
    main()
