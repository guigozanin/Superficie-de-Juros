"""
App Streamlit - Superfície de Juros Brasil x EUA
Visualização interativa das superfícies de juros e comparação de curvas
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from bizdays import Calendar

# Configuração da página
st.set_page_config(
    page_title="Superfície de Juros Brasil x EUA",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para tema dark
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stTabs [data-baseweb="tab-list"] {
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem;
        font-weight: 600;
        color: #fafafa;
    }
    .metric-card {
        background-color: #262730;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        margin: 0.5rem 0;
        color: #fafafa;
    }
    .country-header {
        background: linear-gradient(90deg, #1f77b4, #ff7f0e);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def carregar_dados():
    """Carrega dados processados com cache"""
    dados = {}
    
    # Brasil - carrega dados da Base_Bruta.parquet
    brasil_bruto_path = 'Dados/Base_Bruta.parquet'
    brasil_path = 'Dados/juros_brasil_processado.parquet'
    
    if os.path.exists(brasil_bruto_path):
        dados['brasil_bruto'] = pd.read_parquet(brasil_bruto_path)
    else:
        dados['brasil_bruto'] = None
        
    if os.path.exists(brasil_path):
        dados['brasil'] = pd.read_parquet(brasil_path)
    else:
        dados['brasil'] = None
        st.warning("⚠️ Dados do Brasil não encontrados. Execute o script de coleta e processamento primeiro.")
    
    # EUA
    eua_path = 'Dados/juros_eua_processado.parquet'
    if os.path.exists(eua_path):
        dados['eua'] = pd.read_parquet(eua_path)
    else:
        dados['eua'] = None
        st.warning("⚠️ Dados dos EUA não encontrados. Execute o script de coleta e processamento primeiro.")
    
    return dados

def plot_superficie_3d(df, titulo, pais):
    """Cria gráfico de superfície 3D"""
    if df is None or df.empty:
        st.error(f"Dados não disponíveis para {pais}")
        return None
    
    # Prepara os dados
    if pais == "Brasil":
        # Remove sufixo "_dias" das colunas para melhor visualização
        colunas_display = [col.replace('_dias', 'd') for col in df.columns]
        z_values = df.values * 100  # Converte para percentual (ex: 0.15 -> 15)
        colorscale = 'RdYlGn_r'  # Mudança para mesma cor dos EUA (verde, amarelo, vermelho)
    else:
        # Para EUA, mantém a ordem original das colunas (maior para menor maturidade)
        colunas_display = df.columns.tolist()
        z_values = df.values # Divide por 100 para converter de percentual para decimal (ex: 5.25 -> 0.0525, exibindo como 5.25% no gráfico)
        colorscale = 'RdYlGn_r'
    
    # Cria figura
    fig = go.Figure()
    
    # Superfície principal
    fig.add_trace(
        go.Surface(
            x=colunas_display,
            y=df.index.strftime('%Y-%m-%d'),
            z=z_values,  # Já convertido para percentual acima
            colorscale=colorscale,
            opacity=0.9,
            contours={
                "x": {"show": True, "color": "lightblue", "size": 0.01},
                "y": {"show": True, "color": "lightblue", "size": 0.01},
                "z": {"show": False}
            },
            hovertemplate='<b>Data</b>: %{y}<br>' +
                         '<b>Maturidade</b>: %{x}<br>' +
                         '<b>Taxa</b>: %{z:.2f}%<extra></extra>',
            showscale=True,
            colorbar=dict(title="Taxa (%)")
        )
    )
    
    # Linha da última data
    ultima_data = df.index[-1]
    ultima_curva = df.iloc[-1]
    
    # Ajusta os valores da última curva baseado no país
    if pais == "Brasil":
        z_ultima_curva = ultima_curva.values * 100  # Converte para percentual
    else:  # EUA
        z_ultima_curva = ultima_curva.values / 100  # Divide por 100 para converter de percentual para decimal
    
    fig.add_trace(
        go.Scatter3d(
            x=colunas_display,
            y=[ultima_data.strftime('%Y-%m-%d')] * len(colunas_display),
            z=z_ultima_curva,
            mode='lines+markers',
            line=dict(color='black', width=4),
            marker=dict(size=4, color='red'),
            name=f'Última curva ({ultima_data.strftime("%Y-%m-%d")})',
            hovertemplate='<b>Maturidade</b>: %{x}<br>' +
                         '<b>Taxa</b>: %{z:.2f}%<extra></extra>'
        )
    )
    
    # Layout
    fig.update_layout(
        title=dict(
            text=titulo,
            x=0.5,
            font=dict(size=24, color='#2E86C1'),
            xanchor='center'
        ),
        scene=dict(
            xaxis_title='Maturidade',
            yaxis_title='Data',
            zaxis_title='Taxa (%)',
            aspectratio=dict(x=1, y=2, z=0.7),
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2)
            )
        ),
        height=600,
        margin=dict(l=0, r=0, b=0, t=50),
        font=dict(size=12)
    )
    
    return fig

def processar_dados_brasil_historico(di1):
    """Processa dados brutos do Brasil para curva histórica"""
    try:
        # Carrega calendario de mercado
        MARKET_CALENDAR = Calendar.load('ANBIMA')
        
        # Arrumando os dados
        di1['Maturity'] = di1['Vencimento'].map(MARKET_CALENDAR.following)
        di1['DU'] = di1.apply(lambda x: MARKET_CALENDAR.bizdays(x['DataRef'], x['Maturity']), axis=1)
        di1['Rate'] = (100000 / di1['PUAtual'])**(252 / di1['DU']) - 1
        di1_curve = di1[['DataRef', 'Maturity', 'DU', 'Rate', 'PUAtual']]
        di1_curve.columns = ['DataRef', 'Maturity', 'DU', 'Rate', 'PU']
        
        return di1_curve
    except Exception as e:
        st.error(f"Erro ao processar dados: {e}")
        return None

def plot_curva_di1_matplotlib(di1_curve, refdate_one, refdate_two):
    """Cria gráfico de curva DI1 usando matplotlib com styling específico"""
    try:
        # Encontra as datas mais próximas das datas selecionadas
        datas_disponiveis = sorted(di1_curve['DataRef'].unique())
        
        # Converte para pandas Timestamp se necessário
        if not isinstance(refdate_one, pd.Timestamp):
            refdate_one = pd.Timestamp(refdate_one)
        if not isinstance(refdate_two, pd.Timestamp):
            refdate_two = pd.Timestamp(refdate_two)
        
        # Encontra as datas mais próximas disponíveis nos dados
        datas_series = pd.Series(datas_disponiveis)
        idx1 = (datas_series - refdate_one).abs().idxmin()
        idx2 = (datas_series - refdate_two).abs().idxmin()
        
        data_real_1 = datas_disponiveis[idx1]
        data_real_2 = datas_disponiveis[idx2]
        
        # Get the curve for the dates found
        di1_curve_1 = di1_curve[di1_curve['DataRef'] == data_real_1].copy()
        di1_curve_2 = di1_curve[di1_curve['DataRef'] == data_real_2].copy()
        
        if di1_curve_1.empty or di1_curve_2.empty:
            st.error("Não há dados disponíveis para as datas selecionadas")
            return None
            
        # Sort the curves by maturity
        di1_curve_1 = di1_curve_1.sort_values(by='Maturity')
        di1_curve_2 = di1_curve_2.sort_values(by='Maturity')
        
        # Plotting the curve with custom styling
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Set dark background
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#0e1117')
        
        # Plot curves with specified colors
        ax.plot(di1_curve_1['Maturity'], di1_curve_1['Rate'], '-o', 
                color='#58FFE9', linewidth=2, markersize=6)
        ax.plot(di1_curve_2['Maturity'], di1_curve_2['Rate'], '-o', 
                color="#FF5F71", linewidth=2, markersize=6)
        
        # Styling
        ax.set_ylabel('Taxa de Juros (%)', fontsize=14, color='white')
        ax.set_title('Curvas de Juros Futura DI1', fontsize=18, pad=20, color='white')
        
        # Format Y axis as percentage
        yticks = ax.get_yticks()
        ax.set_yticklabels(['{:.1f}%'.format(x*100) for x in yticks], color='white')
        
        # Format X axis (dates)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
        plt.xticks(rotation=45, color='white')
        
        # Remove grid and spines for cleaner look
        ax.grid(False)
        for spine in ax.spines.values():
            spine.set_color('white')
            spine.set_linewidth(0.5)
        
        # Tick colors
        ax.tick_params(colors='white')
        
        # Legend with real dates found
        ax.legend([data_real_1.strftime('%Y-%m-%d'), data_real_2.strftime('%Y-%m-%d')], 
                 loc='upper right', fontsize=12, frameon=False, labelcolor='white')
        
        plt.tight_layout()
        return fig
        
    except Exception as e:
        st.error(f"Erro ao criar gráfico: {e}")
        return None
def plot_comparacao_curvas(df, data1, data2, pais):
    """Cria gráfico de comparação de curvas"""
    if df is None or df.empty:
        st.error(f"Dados não disponíveis para {pais}")
        return None, None, None
    
    try:
        # Encontra as curvas mais próximas das datas selecionadas
        curva1 = df.loc[df.index.get_loc(data1, method='nearest')]
        curva2 = df.loc[df.index.get_loc(data2, method='nearest')]
        
        # Datas reais encontradas
        data1_real = df.index[df.index.get_loc(data1, method='nearest')]
        data2_real = df.index[df.index.get_loc(data2, method='nearest')]
        
        # Prepara nomes das colunas
        if pais == "Brasil":
            colunas_display = [col.replace('_dias', 'd') for col in df.columns]
        else:
            colunas_display = df.columns.tolist()
        
        # Cria figura
        fig = go.Figure()
        
        # Curva 1
        fig.add_trace(
            go.Scatter(
                x=colunas_display,
                y=curva1.values,
                mode='lines+markers',
                name=f'{data1_real.strftime("%d/%m/%Y")}',
                line=dict(color='#ff7f0e', width=3),
                marker=dict(size=8),
                hovertemplate='<b>Maturidade</b>: %{x}<br>' +
                             '<b>Taxa</b>: %{y:.2%}<extra></extra>'
            )
        )
        
        # Curva 2
        fig.add_trace(
            go.Scatter(
                x=colunas_display,
                y=curva2.values,
                mode='lines+markers',
                name=f'{data2_real.strftime("%d/%m/%Y")}',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8),
                hovertemplate='<b>Maturidade</b>: %{x}<br>' +
                             '<b>Taxa</b>: %{y:.2%}<extra></extra>'
            )
        )
        
        # Layout
        fig.update_layout(
            title=f'Comparação de Curvas de Juros - {pais}',
            xaxis_title='Maturidade',
            yaxis_title='Taxa (%)',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            height=500,
            template='plotly_white'
        )
        
        # Formato percentual no eixo Y
        fig.update_yaxis(tickformat='.1%')
        
        return fig, data1_real, data2_real
        
    except Exception as e:
        st.error(f"Erro ao criar gráfico de comparação: {e}")
        return None, None, None

# Função removida - métricas não serão mais exibidas

def mostrar_historica_brasil(dados):
    """Mostra curvas históricas do Brasil com comparação usando dados brutos"""
    if dados['brasil_bruto'] is None:
        st.error("❌ Dados brutos do Brasil não disponíveis")
        return
    
    st.markdown("## Curva de Juros Futura - Brasil 🇧🇷")
    st.markdown("Visualize e compare curvas de juros futuras DI1 em diferentes datas.")
    
    # Processa os dados brutos
    di1_curve = processar_dados_brasil_historico(dados['brasil_bruto'])
    
    if di1_curve is None:
        return
    
    # Obtém datas disponíveis
    datas_disponiveis = sorted(di1_curve['DataRef'].unique())
    
    if len(datas_disponiveis) < 2:
        st.error("❌ Dados insuficientes para comparação")
        return
    
    # Seleção automática de datas padrão
    # Primeira data do último ano
    last_year = pd.to_datetime(datas_disponiveis[-1]).year
    first_date_last_year = None
    for data in datas_disponiveis:
        if pd.to_datetime(data).year == last_year:
            first_date_last_year = data
            break
    
    # Última data disponível
    last_date = datas_disponiveis[-1]
    
    # Interface para seleção de datas
    st.markdown("### Selecione as datas para comparar")
    
    col1, col2 = st.columns(2)
    
    with col1:
        data1 = st.date_input(
            "Primeira Data",
            value=pd.to_datetime(first_date_last_year).date() if first_date_last_year else pd.to_datetime(datas_disponiveis[0]).date(),
            min_value=pd.to_datetime(datas_disponiveis[0]).date(),
            max_value=pd.to_datetime(datas_disponiveis[-1]).date(),
            key="br_data1_new"
        )
    
    with col2:
        data2 = st.date_input(
            "Segunda Data",
            value=pd.to_datetime(datas_disponiveis[-1]).date(),
            min_value=pd.to_datetime(datas_disponiveis[0]).date(),
            max_value=pd.to_datetime(datas_disponiveis[-1]).date(),
            key="br_data2_new"
        )
    
    # Cria o gráfico de comparação
    if data1 and data2:
        # Converte para datetime
        refdate_one = pd.to_datetime(data1)
        refdate_two = pd.to_datetime(data2)
        
        # Gera o gráfico matplotlib
        fig = plot_curva_di1_matplotlib(di1_curve, refdate_one, refdate_two)
        
        if fig is not None:
            st.pyplot(fig)
            plt.close()  # Libera a memória
    
    # Seção de download dos dados
    st.markdown("---")
    st.markdown("### Download dos Dados")
    st.markdown("Baixe os dados históricos utilizados nesta análise:")
    
    # Converte para CSV para download
    csv_data = di1_curve.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Baixar dados do Brasil (CSV)",
        data=csv_data,
        file_name=f"juros_brasil_historico_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

def mostrar_historica_eua(dados):
    """Mostra curvas históricas dos EUA com comparação usando matplotlib"""
    if dados['eua'] is None:
        st.error("❌ Dados dos EUA não disponíveis")
        return
    
    st.markdown("## Curva de Juros Futura - EUA 🇺🇸")
    st.markdown("Visualize e compare curvas de juros dos EUA em diferentes datas.")
    
    df = dados['eua']
    
    # Obtém datas disponíveis
    datas_disponiveis = sorted(df.index)
    
    if len(datas_disponiveis) < 2:
        st.error("❌ Dados insuficientes para comparação")
        return
    
    # Seleção automática de datas padrão
    # Primeira data do último ano
    last_year = datas_disponiveis[-1].year
    first_date_last_year = None
    for data in datas_disponiveis:
        if data.year == last_year:
            first_date_last_year = data
            break
    
    # Última data disponível
    last_date = datas_disponiveis[-1]
    
    # Interface para seleção de datas
    st.markdown("### Selecione as datas para comparar")
    
    # Formata as datas disponíveis para exibição
    datas_formatadas = [data.strftime("%d/%m/%Y") for data in datas_disponiveis]
    
    # Índices padrão
    idx_primeira = datas_disponiveis.index(first_date_last_year) if first_date_last_year else 0
    idx_ultima = len(datas_disponiveis) - 1
    
    col1, col2 = st.columns(2)
    
    with col1:
        idx_data1 = st.selectbox(
            "Primeira Data",
            range(len(datas_formatadas)),
            index=idx_primeira,
            format_func=lambda x: datas_formatadas[x],
            key="eua_data1_select"
        )
        data1 = datas_disponiveis[idx_data1]
    
    with col2:
        idx_data2 = st.selectbox(
            "Segunda Data",
            range(len(datas_formatadas)),
            index=idx_ultima,
            format_func=lambda x: datas_formatadas[x],
            key="eua_data2_select"
        )
        data2 = datas_disponiveis[idx_data2]
    
    # Cria o gráfico de comparação
    if data1 and data2:
        # Converte para datetime (os objetos já são datetime do pandas)
        data1_ts = pd.Timestamp(data1)
        data2_ts = pd.Timestamp(data2)
        
        # Gera o gráfico matplotlib
        fig = plot_curva_eua_matplotlib(df, data1_ts, data2_ts)
        
        if fig is not None:
            st.pyplot(fig)
            plt.close()  # Libera a memória
    
    # Seção de download dos dados
    st.markdown("---")
    st.markdown("### Download dos Dados")
    st.markdown("Baixe os dados históricos utilizados nesta análise:")
    
    # Converte para CSV para download
    csv_data = df.to_csv().encode('utf-8')
    st.download_button(
        label="Baixar dados dos EUA (CSV)",
        data=csv_data,
        file_name=f"juros_eua_historico_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

def mostrar_superficie_brasil(dados):
    """Mostra superfície 3D do Brasil"""
    if dados['brasil'] is None:
        st.error("❌ Dados do Brasil não disponíveis")
        return
    
    st.markdown("## Superfície de Juros - Brasil 🇧🇷")
    st.markdown("Visualize a evolução temporal completa das curvas de juros brasileiras em três dimensões.")
    
    fig_br = plot_superficie_3d(dados['brasil'], "Superfície de Juros - Brasil", "Brasil")
    if fig_br:
        st.plotly_chart(fig_br, use_container_width=True)
    
    # Seção de download dos dados
    st.markdown("---")
    st.markdown("### Download dos Dados")
    st.markdown("Baixe os dados históricos utilizados nesta análise:")
    
    # Converte para CSV para download
    df = dados['brasil']
    csv_data = df.to_csv().encode('utf-8')
    st.download_button(
        label="Baixar dados do Brasil (CSV)",
        data=csv_data,
        file_name=f"juros_brasil_historico_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

def mostrar_superficie_eua(dados):
    """Mostra superfície 3D dos EUA"""
    if dados['eua'] is None:
        st.error("❌ Dados dos EUA não disponíveis")
        return
    
    st.markdown("## Monitor de Juros Brasil e EUA 🇺🇸")
    st.markdown("Visualize a evolução temporal completa das curvas de juros americanas em três dimensões.")
    
    fig_us = plot_superficie_3d(dados['eua'], "Monitor de Juros Brasil e EUA", "EUA")
    if fig_us:
        st.plotly_chart(fig_us, use_container_width=True)
    
    # Seção de download dos dados
    st.markdown("---")
    st.markdown("### Download dos Dados")
    st.markdown("Baixe os dados históricos utilizados nesta análise:")
    
    # Converte para CSV para download
    df = dados['eua']
    csv_data = df.to_csv().encode('utf-8')
    st.download_button(
        label="Baixar dados dos EUA (CSV)",
        data=csv_data,
        file_name=f"juros_eua_historico_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

def plot_curva_eua_matplotlib(df_eua, data1, data2):
    """Cria gráfico de comparação de curvas dos EUA usando matplotlib"""
    try:
        # Encontra as datas mais próximas das datas selecionadas
        datas_disponiveis = sorted(df_eua.index)
        
        # Converte para pandas Timestamp se necessário
        if not isinstance(data1, pd.Timestamp):
            data1 = pd.Timestamp(data1)
        if not isinstance(data2, pd.Timestamp):
            data2 = pd.Timestamp(data2)
        
        # Encontra as datas mais próximas disponíveis nos dados
        datas_series = pd.Series(datas_disponiveis)
        idx1 = (datas_series - data1).abs().idxmin()
        idx2 = (datas_series - data2).abs().idxmin()
        
        data1_real = datas_disponiveis[idx1]
        data2_real = datas_disponiveis[idx2]
        
        # Encontra as curvas correspondentes às datas encontradas
        curva1 = df_eua.loc[data1_real]
        curva2 = df_eua.loc[data2_real]
        
        # Configura o estilo matplotlib para fundo escuro
        plt.style.use('dark_background')
        
        # Cria o gráfico
        fig, ax = plt.subplots(figsize=(12, 8))
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#0e1117')
        
        # Maturidades dos EUA (inverte a ordem para menor para maior maturidade)
        maturidades = df_eua.columns.tolist()[::-1]  # Inverte a ordem das maturidades
        
        # Inverte também os valores das curvas para coincidir com a nova ordem das maturidades
        curva1_invertida = curva1.values[::-1]
        curva2_invertida = curva2.values[::-1]
        
        # Plota as curvas (divide por 100 para converter de porcentagem para decimal)
        ax.plot(maturidades, curva1_invertida, '-o', 
                color='#58FFE9', linewidth=2, markersize=6, label=data1_real.strftime('%Y-%m-%d'))
        ax.plot(maturidades, curva2_invertida, '-o', 
                color='#FF5F71', linewidth=2, markersize=6, label=data2_real.strftime('%Y-%m-%d'))
        
        # Configurações do gráfico
        ax.set_ylabel('Taxa de Juros (%)', fontsize=14, color='white')
        ax.set_xlabel('Maturidade', fontsize=14, color='white')
        ax.set_title('Curvas de Juros dos EUA', fontsize=18, color='white', pad=20)
        
        # Formata o eixo Y para mostrar percentuais (valores já estão em decimal)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.2f}%'))
        
        # Configura a legenda
        ax.legend(loc='upper right', fontsize=12, frameon=False, 
                 facecolor='none', edgecolor='none')
        
        # Rotaciona labels do eixo X se necessário
        plt.xticks(rotation=45)
        
        # Remove bordas e configura grid
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#333333')
        ax.spines['bottom'].set_color('#333333')
        ax.tick_params(colors='white')
        ax.grid(True, alpha=0.3, color='#333333')
        
        plt.tight_layout()
        
        return fig
        
    except Exception as e:
        st.error(f"Erro ao criar gráfico dos EUA: {e}")
        return None

def main():
    """Função principal do app"""
    
    # Header com logo
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        # Logo da After Market FL
        try:
            logo_path = 'amfl_selo_gradiente_sem_fundo.png'
            if os.path.exists(logo_path):
                st.image(logo_path, width=150)
        except:
            pass  # Se não conseguir carregar o logo, continua sem ele
    
    with col2:
        st.title("Juros Brasil e EUA")
    
    with col3:
        st.write("")  # Espaço em branco para balancear
    
    # Carrega dados
    with st.spinner("Carregando dados..."):
        dados = carregar_dados()
    
    # Verifica se há dados disponíveis
    if dados['brasil'] is None and dados['eua'] is None:
        st.error("❌ Nenhum dado disponível. Execute os scripts de coleta e processamento primeiro.")
        return

    # Sidebar com navegação específica
    with st.sidebar:
        st.header("Índice")
        
        # Estado para controlar qual visualização está ativa
        if 'visualizacao_ativa' not in st.session_state:
            st.session_state.visualizacao_ativa = 'superficie_brasil'
        
        # Botões de navegação
        if st.button("Curva de juros futura Brasil", use_container_width=True):
            st.session_state.visualizacao_ativa = 'historica_brasil'
        
        if st.button("Curva de juros futura EUA", use_container_width=True):
            st.session_state.visualizacao_ativa = 'historica_eua'
        
        if st.button("Superfície de juros Brasil", use_container_width=True):
            st.session_state.visualizacao_ativa = 'superficie_brasil'
        
        if st.button("Superfície de juros EUA", use_container_width=True):
            st.session_state.visualizacao_ativa = 'superficie_eua'
        
        st.markdown("---")
        st.markdown("**Fonte:** BCB, FRED")
        st.markdown("**Desenvolvido por:** [After Market FL](https://aftermarketfl.com.br)")
    
    # Conteúdo principal baseado na seleção
    if st.session_state.visualizacao_ativa == 'historica_brasil':
        mostrar_historica_brasil(dados)
    elif st.session_state.visualizacao_ativa == 'historica_eua':
        mostrar_historica_eua(dados)
    elif st.session_state.visualizacao_ativa == 'superficie_brasil':
        mostrar_superficie_brasil(dados)
    elif st.session_state.visualizacao_ativa == 'superficie_eua':
        mostrar_superficie_eua(dados)


if __name__ == "__main__":
    main()
