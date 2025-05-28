"""
Script de Processamento de Dados - Superfície de Juros
Processa os dados coletados para criar as superfícies de juros
"""

import pandas as pd
import numpy as np
from bizdays import Calendar
from scipy.interpolate import interp1d
import datetime
import os

def flat_forward_interpolation(x, y):
    """Interpolação flat-forward"""
    return interp1d(x, y, kind='previous', fill_value='extrapolate')

def processa_dados_brasil():
    """Processa dados do Brasil para criar superfície de juros"""
    print("Processando dados do Brasil...")
    
    # Verifica se já temos dados processados
    rates_path = 'Dados/rates_all_horizons_df.parquet'
    
    if os.path.exists(rates_path):
        print("Dados já processados encontrados, carregando...")
        rates_all_horizons_df = pd.read_parquet(rates_path)
        print(f"Carregados {len(rates_all_horizons_df)} registros processados")
        
        # Prepara para visualização
        rates_all_horizons_df2 = rates_all_horizons_df.copy()
        rates_all_horizons_df2["Data"] = pd.to_datetime(rates_all_horizons_df2["refdate"])
        rates_all_horizons_df2.set_index('Data', inplace=True)
        rates_all_horizons_df2 = rates_all_horizons_df2[rates_all_horizons_df2.columns[::-1]]  # Inverte ordem
        rates_all_horizons_df2 = rates_all_horizons_df2.iloc[:,:-1]  # Remove coluna refdate
        
        # Salva dados processados
        brasil_path = 'Dados/juros_brasil_processado.parquet'
        os.makedirs(os.path.dirname(brasil_path), exist_ok=True)
        rates_all_horizons_df2.to_parquet(brasil_path)
        
        print(f"Dados do Brasil processados e salvos: {brasil_path}")
        print(f"Shape final: {rates_all_horizons_df2.shape}")
        
        return rates_all_horizons_df2
    
    # Carrega dados brutos se não houver processados
    base_path = 'Dados/Base_Bruta.parquet'
    
    if not os.path.exists(base_path):
        print(f"Arquivo não encontrado: {base_path}")
        return None
    
    di1 = pd.read_parquet(base_path)
    print(f"Carregados {len(di1)} registros do Brasil")
    
    # Calendário de mercado
    MARKET_CALENDAR = Calendar.load('ANBIMA')
    
    # Arruma os dados
    di1['Maturity'] = di1['Vencimento'].map(MARKET_CALENDAR.following)
    di1['DU'] = di1.apply(lambda x: MARKET_CALENDAR.bizdays(x['DataRef'], x['Maturity']), axis=1)
    di1['Rate'] = (100000 / di1['PUAtual'])**(252 / di1['DU']) - 1
    di1_curve = di1[['DataRef', 'Maturity', 'DU', 'Rate', 'PUAtual']]
    di1_curve.columns = ['refdate', 'forward_date', 'biz_days', 'r_252', 'PU']
    
    print("Dados processados, iniciando interpolação...")
    
    # Interpolação para múltiplas curvas
    unique_dates = di1_curve['refdate'].unique()
    curves = []
    
    for date in unique_dates:
        # Filtra dados para a data específica
        df_curve = di1_curve[(di1_curve['refdate'] == date) & (di1_curve['biz_days'] > 0)]
        
        # Remove duplicatas
        df_curve = df_curve.drop_duplicates(subset='biz_days')
        
        if len(df_curve) > 1:  # Precisa de pelo menos 2 pontos para interpolar
            # Cria curva com interpolação
            curve = flat_forward_interpolation(df_curve['biz_days'], df_curve['r_252'])
            curves.append((date, curve))
    
    print(f"Criadas {len(curves)} curvas interpoladas")
    
    # Define horizontes para interpolação
    horizons = [
        21, 63, 126,
        252, 504, 756, 1008, 1260, 1512, 1764, 2016, 2268, 2520,
        2772, 3024, 3276, 3528, 3780, 4032, 4284, 4536, 4788, 5040,
        5292, 5544, 5796, 6048, 6300, 6552, 6804, 7068, 7308, 7560,
        7812, 8064, 8316, 8558
    ]
    
    # Calcula taxas para diferentes horizontes
    rates_all_horizons = []
    
    for date, curve in curves:
        rates_for_date = {'refdate': date}
        
        for horizon in horizons:
            try:
                rates_for_date[f'{horizon}_dias'] = float(curve(horizon))
            except:
                rates_for_date[f'{horizon}_dias'] = np.nan
        
        rates_all_horizons.append(rates_for_date)
    
    # Converte para DataFrame
    rates_all_horizons_df = pd.DataFrame(rates_all_horizons)
    
    # Remove linhas com muitos NaN
    rates_all_horizons_df = rates_all_horizons_df.dropna(thresh=len(horizons)*0.5)
    
    # Remove outliers na coluna de maior maturidade
    if not rates_all_horizons_df.empty and '8558_dias' in rates_all_horizons_df.columns:
        # Remove apenas se não for NaN
        valid_values = rates_all_horizons_df['8558_dias'].dropna()
        if not valid_values.empty:
            idx_min = valid_values.idxmin()
            rates_all_horizons_df = rates_all_horizons_df.drop(idx_min)
    
    rates_all_horizons_df.reset_index(drop=True, inplace=True)
    
    # Prepara para visualização
    rates_all_horizons_df2 = rates_all_horizons_df.copy()
    rates_all_horizons_df2["Data"] = pd.to_datetime(rates_all_horizons_df2["refdate"])
    rates_all_horizons_df2.set_index('Data', inplace=True)
    rates_all_horizons_df2 = rates_all_horizons_df2[rates_all_horizons_df2.columns[::-1]]  # Inverte ordem
    rates_all_horizons_df2 = rates_all_horizons_df2.iloc[:,:-1]  # Remove coluna refdate
    
    # Salva dados processados
    brasil_path = 'Dados/juros_brasil_processado.parquet'
    os.makedirs(os.path.dirname(brasil_path), exist_ok=True)
    rates_all_horizons_df2.to_parquet(brasil_path)
    
    print(f"Dados do Brasil processados e salvos: {brasil_path}")
    print(f"Shape final: {rates_all_horizons_df2.shape}")
    
    return rates_all_horizons_df2

def processa_dados_eua():
    """Processa dados dos EUA para criar superfície de juros"""
    print("Processando dados dos EUA...")
    
    # Carrega dados brutos
    eua_path = 'Dados/juros_eua_bruto.parquet'
    
    if not os.path.exists(eua_path):
        print(f"Arquivo não encontrado: {eua_path}")
        return None
    
    df_us = pd.read_parquet(eua_path)
    print(f"Carregados {len(df_us)} registros dos EUA")
    
    # Limpa dados
    df_us = df_us.dropna(how='all')
    df_us = df_us.sort_index()
    
    # Reorganiza colunas por ordem de maturidade (do menor para o maior)
    ordered_columns = ['1M', '3M', '6M', '1Y', '2Y', '3Y', '5Y', '10Y', '30Y']
    df_us = df_us[ordered_columns]
    
    # Remove linhas com muitos NaN
    df_us = df_us.dropna(thresh=len(ordered_columns)*0.5)
    
    # Converte porcentagens se necessário
    # Os valores já vêm em porcentagem (ex: 5.25), então não dividimos por 100 aqui
    # Eles serão exibidos corretamente no gráfico como 5.25%
    
    # Inverte ordem das colunas (igual ao Brasil - maior maturidade primeiro)
    df_us = df_us[df_us.columns[::-1]]
    
    # Salva dados processados
    eua_processado_path = 'Dados/juros_eua_processado.parquet'
    os.makedirs(os.path.dirname(eua_processado_path), exist_ok=True)
    df_us.to_parquet(eua_processado_path)
    
    print(f"Dados dos EUA processados e salvos: {eua_processado_path}")
    print(f"Shape final: {df_us.shape}")
    
    return df_us

def criar_datasets_comparacao():
    """Cria datasets específicos para comparação de curvas"""
    print("Criando datasets para comparação...")
    
    # Brasil
    brasil_path = 'Dados/juros_brasil_processado.parquet'
    if os.path.exists(brasil_path):
        df_br = pd.read_parquet(brasil_path)
        
        # Criar dataset com datas específicas para comparação
        if not df_br.empty:
            # Primeira e última data do ano atual
            ano_atual = datetime.datetime.now().year
            dados_ano = df_br[df_br.index.year == ano_atual]
            
            if not dados_ano.empty:
                primeira_data = dados_ano.index.min()
                ultima_data = dados_ano.index.max()
                
                comparacao_br = {
                    'primeira_data_ano': primeira_data,
                    'ultima_data_ano': ultima_data,
                    'curva_primeira': dados_ano.loc[primeira_data],
                    'curva_ultima': dados_ano.loc[ultima_data]
                }
            else:
                # Se não há dados do ano atual, pega as últimas duas datas disponíveis
                comparacao_br = {
                    'primeira_data_ano': df_br.index[-10] if len(df_br) > 10 else df_br.index[0],
                    'ultima_data_ano': df_br.index[-1],
                    'curva_primeira': df_br.iloc[-10] if len(df_br) > 10 else df_br.iloc[0],
                    'curva_ultima': df_br.iloc[-1]
                }
        else:
            comparacao_br = None
    else:
        comparacao_br = None
    
    # EUA
    eua_path = 'Dados/juros_eua_processado.parquet'
    if os.path.exists(eua_path):
        df_us = pd.read_parquet(eua_path)
        
        if not df_us.empty:
            # Primeira e última data do ano atual
            ano_atual = datetime.datetime.now().year
            dados_ano = df_us[df_us.index.year == ano_atual]
            
            if not dados_ano.empty:
                primeira_data = dados_ano.index.min()
                ultima_data = dados_ano.index.max()
                
                comparacao_us = {
                    'primeira_data_ano': primeira_data,
                    'ultima_data_ano': ultima_data,
                    'curva_primeira': dados_ano.loc[primeira_data],
                    'curva_ultima': dados_ano.loc[ultima_data]
                }
            else:
                # Se não há dados do ano atual, pega as últimas duas datas disponíveis
                comparacao_us = {
                    'primeira_data_ano': df_us.index[-10] if len(df_us) > 10 else df_us.index[0],
                    'ultima_data_ano': df_us.index[-1],
                    'curva_primeira': df_us.iloc[-10] if len(df_us) > 10 else df_us.iloc[0],
                    'curva_ultima': df_us.iloc[-1]
                }
        else:
            comparacao_us = None
    else:
        comparacao_us = None
    
    return comparacao_br, comparacao_us

def main():
    """Função principal de processamento"""
    print("=== PROCESSAMENTO DE DADOS - SUPERFÍCIE DE JUROS ===")
    
    # Processa dados do Brasil
    dados_brasil = processa_dados_brasil()
    
    # Processa dados dos EUA
    dados_eua = processa_dados_eua()
    
    # Cria datasets para comparação
    comp_br, comp_us = criar_datasets_comparacao()
    
    print("=== PROCESSAMENTO FINALIZADO ===")
    
    if dados_brasil is not None:
        print(f"Brasil processado: {dados_brasil.shape}")
    
    if dados_eua is not None:
        print(f"EUA processado: {dados_eua.shape}")
    
    print("Datasets prontos para visualização!")

if __name__ == "__main__":
    main()
