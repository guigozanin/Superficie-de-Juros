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
from streamlit_option_menu import option_menu

# Função para determinar altura responsiva dos gráficos
def get_responsive_height(tipo="normal"):
    # Detecta o tamanho da tela do usuário via JavaScript
    is_mobile = """
    <script>
        var isMobile = window.matchMedia("(max-width: 768px)").matches;
        var isSmallMobile = window.matchMedia("(max-width: 480px)").matches;
        if (isMobile) {
            document.querySelector("body").classList.add("is-mobile");
        }
        if (isSmallMobile) {
            document.querySelector("body").classList.add("is-small-mobile");
        }
        
        // Armazena tamanho para uso posterior
        localStorage.setItem("viewportWidth", window.innerWidth);
        localStorage.setItem("isMobile", isMobile);
        localStorage.setItem("isSmallMobile", isSmallMobile);
    </script>
    <style>
        .is-mobile {
            --mobile-mode: true;
        }
        .is-small-mobile {
            --small-mobile-mode: true;
        }
    </style>
    """
    st.markdown(is_mobile, unsafe_allow_html=True)
    
    # Valores de altura responsivos baseados no tipo de gráfico
    if tipo == "superficie":
        # Gráficos de superfície 3D (mais altos para visualização adequada)
        return 600  # Altura base ajustada proporcionalmente no CSS
    elif tipo == "dashboard":
        # Painéis de visualização no dashboard
        return 380  # Altura menor para caber múltiplos gráficos
    else:
        # Gráficos regulares de linha
        return 550  # Altura padrão para gráficos normais

# Configuração da página
st.set_page_config(
    page_title="Superfície de Juros Brasil x EUA",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "Aplicativo de visualização de curvas de juros Brasil x EUA"
    }
)
# Nota: O tema escuro é forçado via CSS customizado abaixo, pois o parâmetro 'theme' não é suportado
# em algumas versões do Streamlit

# CSS customizado para tema dark e navegação avançada
st.markdown("""
<style>
    @import url("https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap");
    
    /* Reset e aplicação universal do modo escuro */
    html, body, [class*="css"] {
        background-color: #0e1117 !important;
        color: #f0f2f6 !important;
    }
    
    /* Elementos principais da interface */
    .main, .stApp, .css-1d391kg, .block-container {
        background-color: #0e1117 !important;
        font-family: "Inter", sans-serif;
    }
    
    /* Sidebar e componentes */
    .sidebar .sidebar-content, [data-testid="stSidebar"] {
        background-color: #1a1c24 !important;
        border-right: 1px solid #2d323b !important;
    }
    
    /* Inputs, botões e selects */
    .stTextInput input, .stNumberInput input, .stDateInput input, 
    .stSelectbox > div, .stMultiSelect > div {
        background-color: #262730 !important;
        color: #f0f2f6 !important;
        border-color: #4a4f60 !important;
    }
    
    /* Controles específicos */
    .stDateInput > div[data-baseweb="input"] {
        background-color: #262730 !important;
    }
    
    .stDateInput > div[data-baseweb="input"] > div {
        background-color: #262730 !important;
        color: #f0f2f6 !important;
    }
    
    .stSlider [data-baseweb="slider"] {
        background-color: #3a3f4a !important;
    }
    
    .stSlider [data-baseweb="thumb"] {
        background-color: #4a90e2 !important;
    }
    
    /* Botões */
    button, .stButton button, div[data-testid="stButton"] button {
        background-color: #262730 !important;
        color: #f0f2f6 !important;
        border-color: #4a4f60 !important;
    }
    
    /* Botões de download */
    .stDownloadButton button {
        background-color: #1e3a8a !important;
        color: white !important;
        border: none !important;
        border-radius: 4px !important;
        transition: background-color 0.3s !important;
    }
    
    .stDownloadButton button:hover {
        background-color: #2563eb !important;
    }
    
    /* Painéis e cartões */
    .stTabs [data-baseweb="tab-list"] {
        justify-content: center;
        background-color: #1a1c24 !important;
        border-radius: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem;
        font-weight: 600;
        color: #fafafa !important;
    }
    
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #3a55c5 !important;
    }
    
    /* Cards e headers */
    .metric-card {
        background-color: #262730 !important;
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
    
    /* Chart title e elementos personalizados */
    .chart-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #f0f2f6 !important;
        text-align: center;
        margin: 1rem 0;
        padding: 0.5rem;
        background-color: #1a1c24;
        border-radius: 8px;
    }
    
    /* Data frames e tabelas */
    .dataframe, .css-1b0udgb, .stDataFrame {
        background-color: #262730 !important;
        color: #f0f2f6 !important;
    }
    
    .dataframe th {
        background-color: #3a3f4a !important;
        color: white !important;
    }
    
    .dataframe td {
        background-color: #262730 !important;
        color: #f0f2f6 !important;
    }
    
    /* Texto e cabeçalhos */
    h1, h2, h3, h4, h5, h6, p, span {
        color: #f0f2f6 !important;
    }
    
    /* Plotly hover e tooltips */
    .plotly .modebar, .js-plotly-plot .plotly .modebar {
        background-color: rgba(26, 28, 36, 0.9) !important;
        color: #f0f2f6 !important;
    }
    
    .plotly .modebar-btn path {
        fill: #f0f2f6 !important;
    }
    
    /* Calendários e seletores de data */
    div[data-baseweb="calendar"] {
        background-color: #262730 !important;
        border-color: #4a4f60 !important;
    }
    
    div[data-baseweb="calendar"] button {
        color: #f0f2f6 !important;
    }
    
    div[data-baseweb="calendar"] button:hover {
        background-color: #3a3f4a !important;
    }
    
    div[data-baseweb="calendar"] button[aria-selected="true"] {
        background-color: #4a90e2 !important;
        color: white !important;
    }
    
    /* Mensagens e alertas */
    div[data-testid="stAlert"] {
        background-color: #262730 !important;
        color: #f0f2f6 !important;
        border-color: #4a4f60 !important;
        border-width: 1px !important;
        border-radius: 8px !important;
        padding: 0.75rem 1rem !important;
    }
    
    /* Erro */
    div[data-baseweb="notification"] {
        background-color: #262730 !important;
        border-color: #dc2626 !important;
    }
    
    /* Warnings */
    div[data-testid="stAlert"][kind="warning"] {
        border-color: #f59e0b !important;
    }
    
    /* Success */
    div[data-testid="stAlert"][kind="success"] {
        border-color: #10b981 !important;
    }
    
    /* Info */
    div[data-testid="stAlert"][kind="info"] {
        border-color: #3b82f6 !important;
    }
    
    /* Scrollbars personalizadas */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1c24;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #4a4f60;
        border-radius: 5px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #5a6072;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def carregar_dados():
    """Carrega dados processados com cache"""
    dados = {}
    
    # Brasil - carrega dados da Base_Bruta.parquet
    brasil_bruto_path = "Dados/Base_Bruta.parquet"
    brasil_path = "Dados/juros_brasil_processado.parquet"
    
    if os.path.exists(brasil_bruto_path):
        dados["brasil_bruto"] = pd.read_parquet(brasil_bruto_path)
    else:
        dados["brasil_bruto"] = None
        
    if os.path.exists(brasil_path):
        dados["brasil"] = pd.read_parquet(brasil_path)
    else:
        dados["brasil"] = None
        st.warning("⚠️ Dados do Brasil não encontrados. Execute o script de coleta e processamento primeiro.")
    
    # EUA
    eua_path = "Dados/juros_eua_processado.parquet"
    if os.path.exists(eua_path):
        dados["eua"] = pd.read_parquet(eua_path)
    else:
        dados["eua"] = None
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
        colunas_display = [col.replace("_dias", "d") for col in df.columns]
        z_values = df.values * 100  # Converte para percentual (ex: 0.15 -> 15)
        colorscale = "RdYlGn_r"  # Mudança para mesma cor dos EUA (verde, amarelo, vermelho)
    else:
        # Para EUA, mantém a ordem original das colunas (maior para menor maturidade)
        colunas_display = df.columns.tolist()
        z_values = df.values # Divide por 100 para converter de percentual para decimal (ex: 5.25 -> 0.0525, exibindo como 5.25% no gráfico)
        colorscale = "RdYlGn_r"
    
    # Cria figura
    fig = go.Figure()
    
    # Superfície principal
    fig.add_trace(
        go.Surface(
            x=colunas_display,
            y=df.index.strftime("%Y-%m-%d"),
            z=z_values,  # Já convertido para percentual acima
            colorscale=colorscale,
            opacity=0.9,
            contours={
                "x": {"show": True, "color": "lightblue", "size": 0.01},
                "y": {"show": True, "color": "lightblue", "size": 0.01},
                "z": {"show": False}
            },
            hovertemplate="<b>Data</b>: %{y}<br>" +
                         "<b>Maturidade</b>: %{x}<br>" +
                         "<b>Taxa</b>: %{z:.2f}%<extra></extra>",
            showscale=True,
            colorbar=dict(title="Taxa (%)")
        )
    )
    
    # Layout
    fig.update_layout(
        title="",  # Título vazio para evitar undefined
        showlegend=True,
        scene=dict(
            xaxis=dict(
                title="Maturidade",
                showgrid=True,
                gridcolor="#2d3035",
                backgroundcolor="#0e1117",
                gridwidth=1,
                linecolor="#4a4f60"
            ),
            yaxis=dict(
                title="Data",
                showgrid=True,
                gridcolor="#2d3035",
                backgroundcolor="#0e1117",
                gridwidth=1,
                linecolor="#4a4f60"
            ),
            zaxis=dict(
                title="Taxa (%)",
                showgrid=True,
                gridcolor="#2d3035",
                backgroundcolor="#0e1117",
                gridwidth=1,
                linecolor="#4a4f60"
            ),
            aspectratio=dict(x=1, y=2, z=0.7),
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2)
            ),
            bgcolor="#0e1117"
        ),
        height=get_responsive_height("superficie"),
        margin=dict(l=0, r=0, b=0, t=50),
        font=dict(
            size=12,
            color="#f0f2f6"
        ),
        template="plotly_dark",
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117"
    )
    
    return fig

def processar_dados_brasil_historico(di1):
    """Processa dados brutos do Brasil para curva histórica"""
    try:
        # Carrega calendario de mercado
        MARKET_CALENDAR = Calendar.load("ANBIMA")
        
        # Arrumando os dados
        di1["Maturity"] = di1["Vencimento"].map(MARKET_CALENDAR.following)
        di1["DU"] = di1.apply(lambda x: MARKET_CALENDAR.bizdays(x["DataRef"], x["Maturity"]), axis=1)
        di1["Rate"] = (100000 / di1["PUAtual"])**(252 / di1["DU"]) - 1
        di1_curve = di1[["DataRef", "Maturity", "DU", "Rate", "PUAtual"]]
        di1_curve.columns = ["DataRef", "Maturity", "DU", "Rate", "PU"]
        
        return di1_curve
    except Exception as e:
        st.error(f"Erro ao processar dados: {e}")
        return None

def plot_curva_di1_plotly(di1_curve, refdate_one, refdate_two):
    """Cria gráfico interativo de curva DI1 usando Plotly"""
    try:
        # Encontra as datas mais próximas das datas selecionadas
        datas_disponiveis = sorted(di1_curve["DataRef"].unique())
        
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
        di1_curve_1 = di1_curve[di1_curve["DataRef"] == data_real_1].copy()
        di1_curve_2 = di1_curve[di1_curve["DataRef"] == data_real_2].copy()
        
        if di1_curve_1.empty or di1_curve_2.empty:
            st.error("Não há dados disponíveis para as datas selecionadas")
            return None
            
        # Sort the curves by maturity
        di1_curve_1 = di1_curve_1.sort_values(by="Maturity")
        di1_curve_2 = di1_curve_2.sort_values(by="Maturity")
        
        # Cria figura Plotly
        fig = go.Figure()
        
        # Primeira curva
        fig.add_trace(
            go.Scatter(
                x=di1_curve_1["Maturity"],
                y=di1_curve_1["Rate"],
                mode="lines+markers",
                name=data_real_1.strftime("%Y-%m-%d"),
                line=dict(color="#58FFE9", width=3),
                marker=dict(size=8, color="#58FFE9"),
                hovertemplate="<b>Data</b>: " + data_real_1.strftime("%d/%m/%Y") + "<br>" +
                             "<b>Maturidade</b>: %{x|%Y-%m}<br>" +
                             "<b>Taxa</b>: %{y:.2%}<extra></extra>"
            )
        )
        
        # Segunda curva
        fig.add_trace(
            go.Scatter(
                x=di1_curve_2["Maturity"],
                y=di1_curve_2["Rate"],
                mode="lines+markers",
                name=data_real_2.strftime("%Y-%m-%d"),
                line=dict(color="#FF5F71", width=3),
                marker=dict(size=8, color="#FF5F71"),
                hovertemplate="<b>Data</b>: " + data_real_2.strftime("%d/%m/%Y") + "<br>" +
                             "<b>Maturidade</b>: %{x|%Y-%m}<br>" +
                             "<b>Taxa</b>: %{y:.2%}<extra></extra>"
            )
        )
        
        # Layout
        fig.update_layout(
            title="",  # Título vazio em vez de None
            hovermode="x unified",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=0.98,
                xanchor="center",
                x=0.5,
                font=dict(color="#f0f2f6")
            ),
            height=get_responsive_height("normal"),
            template="plotly_dark",
            plot_bgcolor="#0e1117",
            paper_bgcolor="#0e1117",
            # Configuração explícita dos eixos
            xaxis=dict(
                title="Maturidade",
                tickformat="%Y",  # Formato de ano
                dtick="M24",  # Tick a cada 24 meses (2 anos)
                tickangle=45,  # Rotaciona labels 45 graus
                gridcolor="#2d3035",
                zerolinecolor="#4a4f60",
                color="#f0f2f6"
            ),
            yaxis=dict(
                title="Taxa de Juros (%)",
                tickformat=".1%",
                gridcolor="#2d3035",
                zerolinecolor="#4a4f60",
                color="#f0f2f6"
            ),
            font=dict(
                family="Inter, sans-serif",
                size=12,
                color="#f0f2f6"
            )
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Erro ao criar gráfico: {e}")
        return None

def plot_curva_eua_plotly(df_eua, data1, data2):
    """Cria gráfico interativo de curva dos EUA usando Plotly"""
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
        
        # Maturidades dos EUA (inverte a ordem para menor para maior maturidade)
        maturidades = df_eua.columns.tolist()[::-1]  # Inverte a ordem das maturidades
        
        # Inverte também os valores das curvas para coincidir com a nova ordem das maturidades
        curva1_invertida = curva1.values[::-1]
        curva2_invertida = curva2.values[::-1]
        
        # Cria figura Plotly
        fig = go.Figure()
        
        # Primeira curva
        fig.add_trace(
            go.Scatter(
                x=maturidades,
                y=curva1_invertida,
                mode="lines+markers",
                name=data1_real.strftime("%Y-%m-%d"),
                line=dict(color="#58FFE9", width=3),
                marker=dict(size=8, color="#58FFE9"),
                hovertemplate="<b>Data</b>: " + data1_real.strftime("%d/%m/%Y") + "<br>" +
                             "<b>Maturidade</b>: %{x}<br>" +
                             "<b>Taxa</b>: %{y:.2f}%<extra></extra>"
            )
        )
        
        # Segunda curva
        fig.add_trace(
            go.Scatter(
                x=maturidades,
                y=curva2_invertida,
                mode="lines+markers",
                name=data2_real.strftime("%Y-%m-%d"),
                line=dict(color="#FF5F71", width=3),
                marker=dict(size=8, color="#FF5F71"),
                hovertemplate="<b>Data</b>: " + data2_real.strftime("%d/%m/%Y") + "<br>" +
                             "<b>Maturidade</b>: %{x}<br>" +
                             "<b>Taxa</b>: %{y:.2f}%<extra></extra>"
            )
        )
        
        # Layout
        fig.update_layout(
            title="",  # Título vazio em vez de None
            hovermode="x unified",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="top",
                y=0.98,
                xanchor="center",
                x=0.5,
                font=dict(color="#f0f2f6")
            ),
            height=get_responsive_height("normal"),
            template="plotly_dark",
            plot_bgcolor="#0e1117",
            paper_bgcolor="#0e1117",
            # Configuração explícita dos eixos
            xaxis=dict(
                title="Maturidade",
                tickangle=45,
                gridcolor="#2d3035",
                zerolinecolor="#4a4f60",
                color="#f0f2f6"
            ),
            yaxis=dict(
                title="Taxa de Juros (%)",
                ticksuffix="%",
                gridcolor="#2d3035",
                zerolinecolor="#4a4f60",
                color="#f0f2f6"
            ),
            font=dict(
                family="Inter, sans-serif",
                size=12,
                color="#f0f2f6"
            )
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Erro ao criar gráfico dos EUA: {e}")
        return None

def mostrar_historica_brasil(dados):
    """Mostra curvas históricas do Brasil com comparação usando dados brutos"""
    if dados["brasil_bruto"] is None:
        st.error("Dados brutos do Brasil não disponíveis")
        return
    
    st.markdown("## Curvas de Juros Futura - Brasil 🇧🇷")
    st.markdown("Visualize e compare curvas de juros futuras DI1 em diferentes datas.")
    
    # Processa os dados brutos
    di1_curve = processar_dados_brasil_historico(dados["brasil_bruto"])
    
    if di1_curve is None:
        return
    
    # Obtém datas disponíveis
    datas_disponiveis = sorted(di1_curve["DataRef"].unique())
    
    if len(datas_disponiveis) < 2:
        st.error("Dados insuficientes para comparação")
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
    
    st.markdown("<div class=\"chart-title\">Comparação de Curvas DI1</div>", unsafe_allow_html=True)
    
    # Cria o gráfico de comparação
    if data1 and data2:
        # Converte para datetime
        refdate_one = pd.to_datetime(data1)
        refdate_two = pd.to_datetime(data2)
        
        # Gera o gráfico plotly
        fig = plot_curva_di1_plotly(di1_curve, refdate_one, refdate_two)
        
        if fig is not None:
            # Ajusta altura para mobile
            fig.update_layout(
                height=get_responsive_height("normal"),
                margin=dict(l=20, r=20, t=40, b=40),
                font=dict(size=12)
            )
            st.plotly_chart(fig, use_container_width=True, config={
                "displayModeBar": True,
                "displaylogo": False,
                "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"]
            })
    
    # Seção de download dos dados
    st.markdown("### Download dos Dados")
    st.markdown("Baixe os dados históricos utilizados nesta análise:")
    
    # Converte para CSV para download
    csv_data = di1_curve.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Baixar dados do Brasil (CSV)",
        data=csv_data,
        file_name=f"juros_brasil_historico_{datetime.now().strftime("%Y%m%d")}.csv",
        mime="text/csv"
    )

def mostrar_historica_eua(dados):
    """Mostra curvas históricas dos EUA com comparação usando matplotlib"""
    if dados["eua"] is None:
        st.error("Dados dos EUA não disponíveis")
        return
    
    st.markdown("## Curvas de Juros Futura - EUA 🇺🇸")
    st.markdown("Visualize e compare curvas de juros dos EUA em diferentes datas.")
    
    df = dados["eua"]
    
    # Obtém datas disponíveis
    datas_disponiveis = sorted(df.index)
    
    if len(datas_disponiveis) < 2:
        st.error("Dados insuficientes para comparação")
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
    
    st.markdown("<div class=\"chart-title\">Comparação de Curvas dos EUA</div>", unsafe_allow_html=True)
    
    # Cria o gráfico de comparação
    if data1 and data2:
        # Converte para datetime (os objetos já são datetime do pandas)
        data1_ts = pd.Timestamp(data1)
        data2_ts = pd.Timestamp(data2)
        
        # Gera o gráfico plotly
        fig = plot_curva_eua_plotly(df, data1_ts, data2_ts)
        
        if fig is not None:
            # Ajusta altura para mobile
            fig.update_layout(
                height=get_responsive_height("normal"),
                margin=dict(l=20, r=20, t=40, b=40),
                font=dict(
                    family="Inter, sans-serif",
                    size=12,
                    color="#f0f2f6"
                ),
                plot_bgcolor="#0e1117",
                paper_bgcolor="#0e1117"
            )
            st.plotly_chart(fig, use_container_width=True, config={
                "displayModeBar": True,
                "displaylogo": False,
                "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"]
            })
    
    # Seção de download dos dados
    st.markdown("### Download dos Dados")
    st.markdown("Baixe os dados históricos utilizados nesta análise:")
    
    # Converte para CSV para download
    csv_data = df.to_csv().encode("utf-8")
    st.download_button(
        label="Baixar dados dos EUA (CSV)",
        data=csv_data,
        file_name=f"juros_eua_historico_{datetime.now().strftime("%Y%m%d")}.csv",
        mime="text/csv"
    )

def mostrar_superficie_brasil(dados):
    """Mostra superfície 3D do Brasil"""
    if dados["brasil"] is None:
        st.error("Dados do Brasil não disponíveis")
        return
    
    st.markdown("## Superfície de Juros - Brasil 🇧🇷")
    st.markdown("Visualize a evolução temporal completa das curvas de juros brasileiras em três dimensões.")
    
    st.markdown("<div class=\"chart-title\">Superfície 3D - Evolução das Taxas de Juros</div>", unsafe_allow_html=True)
    
    fig_br = plot_superficie_3d(dados["brasil"], "Superfície de Juros - Brasil", "Brasil")
    if fig_br:
        # Ajusta para mobile
        fig_br.update_layout(
            height=get_responsive_height("superficie"),
            margin=dict(l=10, r=10, t=40, b=10),
            scene=dict(
                camera=dict(
                    eye=dict(x=1.3, y=1.3, z=1.1)  # Câmera mais próxima para mobile
                )
            )
        )
        st.plotly_chart(fig_br, use_container_width=True, config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"]
        })
    
    # Seção de download dos dados
    st.markdown("### Download dos Dados")
    st.markdown("Baixe os dados históricos utilizados nesta análise:")
    
    # Converte para CSV para download
    df = dados["brasil"]
    csv_data = df.to_csv().encode("utf-8")
    st.download_button(
        label="Baixar dados do Brasil (CSV)",
        data=csv_data,
        file_name=f"juros_brasil_historico_{datetime.now().strftime("%Y%m%d")}.csv",
        mime="text/csv"
    )

def mostrar_superficie_eua(dados):
    """Mostra superfície 3D dos EUA"""
    if dados["eua"] is None:
        st.error("Dados dos EUA não disponíveis")
        return
    
    st.markdown("## Superfície de Juros - EUA 🇺🇸")
    st.markdown("Visualize a evolução temporal completa das curvas de juros americanas em três dimensões.")
    
    st.markdown("<div class=\"chart-title\">Superfície 3D - Evolução das Taxas de Juros</div>", unsafe_allow_html=True)
    
    fig_us = plot_superficie_3d(dados["eua"], "Superfície de Juros - EUA", "EUA")
    if fig_us:
        # Ajusta para mobile
        fig_us.update_layout(
            height=get_responsive_height("superficie"),
            margin=dict(l=10, r=10, t=40, b=10),
            scene=dict(
                camera=dict(
                    eye=dict(x=1.3, y=1.3, z=1.1)  # Câmera mais próxima para mobile
                )
            )
        )
        st.plotly_chart(fig_us, use_container_width=True, config={
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"]
        })
    
    # Seção de download dos dados
    st.markdown("### Download dos Dados")
    st.markdown("Baixe os dados históricos utilizados nesta análise:")
    
    # Converte para CSV para download
    df = dados["eua"]
    csv_data = df.to_csv().encode("utf-8")
    st.download_button(
        label="Baixar dados dos EUA (CSV)",
        data=csv_data,
        file_name=f"juros_eua_historico_{datetime.now().strftime("%Y%m%d")}.csv",
        mime="text/csv"
    )

def criar_dashboard_comparativo(dados):
    """Cria dashboard com comparação visual entre Brasil e EUA"""
    st.markdown("## 📊 Dashboard Comparativo Brasil vs EUA")
    st.markdown("Visualize simultaneamente as curvas e superfícies de juros dos dois países.")
    
    # Toggle para escolher tipo de visualização
    tipo_vis = st.radio(
        "Escolha o tipo de visualização:",
        ["Curvas Comparativas", "Superfícies 3D"],
        horizontal=True
    )
    
    if tipo_vis == "Curvas Comparativas":
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<div class=\"chart-title\">🇧🇷 Curvas Brasil (Últimas 2 Datas)</div>", unsafe_allow_html=True)
            
            if dados["brasil_bruto"] is not None:
                di1_curve = processar_dados_brasil_historico(dados["brasil_bruto"])
                if di1_curve is not None:
                    datas = sorted(di1_curve["DataRef"].unique())
                    if len(datas) >= 2:
                        fig_br = plot_curva_di1_plotly(di1_curve, datas[-2], datas[-1])
                        if fig_br:
                            fig_br.update_layout(height=get_responsive_height("dashboard"), margin=dict(l=10, r=10, t=30, b=10))
                            st.plotly_chart(fig_br, use_container_width=True, key="dash_br")
        
        with col2:
            st.markdown("<div class=\"chart-title\">🇺🇸 Curvas EUA (Últimas 2 Datas)</div>", unsafe_allow_html=True)
            
            if dados["eua"] is not None:
                datas_eua = sorted(dados["eua"].index)
                if len(datas_eua) >= 2:
                    fig_eua = plot_curva_eua_plotly(dados["eua"], datas_eua[-2], datas_eua[-1])
                    if fig_eua:
                        fig_eua.update_layout(height=get_responsive_height("dashboard"), margin=dict(l=10, r=10, t=30, b=10))
                        st.plotly_chart(fig_eua, use_container_width=True, key="dash_eua")
    
    else:  # Superfícies 3D
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<div class=\"chart-title\">🇧🇷 Superfície Brasil</div>", unsafe_allow_html=True)
            
            if dados["brasil"] is not None:
                fig_br_3d = plot_superficie_3d(dados["brasil"], "", "Brasil")
                if fig_br_3d:
                    fig_br_3d.update_layout(
                        height=get_responsive_height("dashboard"), 
                        margin=dict(l=0, r=0, t=0, b=0),
                        scene=dict(
                            camera=dict(eye=dict(x=1.2, y=1.2, z=1.0)),
                            bgcolor="#0e1117"
                        ),
                        plot_bgcolor="#0e1117",
                        paper_bgcolor="#0e1117",
                        font=dict(
                            family="Inter, sans-serif",
                            size=12,
                            color="#f0f2f6"
                        )
                    )
                    st.plotly_chart(fig_br_3d, use_container_width=True, key="dash_br_3d")
        
        with col2:
            st.markdown("<div class=\"chart-title\">🇺🇸 Superfície EUA</div>", unsafe_allow_html=True)
            
            if dados["eua"] is not None:
                fig_eua_3d = plot_superficie_3d(dados["eua"], "", "EUA")
                if fig_eua_3d:
                    fig_eua_3d.update_layout(
                        height=get_responsive_height("dashboard"), 
                        margin=dict(l=0, r=0, t=0, b=0),
                        scene=dict(
                            camera=dict(eye=dict(x=1.2, y=1.2, z=1.0)),
                            bgcolor="#0e1117"
                        ),
                        plot_bgcolor="#0e1117",
                        paper_bgcolor="#0e1117",
                        font=dict(
                            family="Inter, sans-serif",
                            size=12,
                            color="#f0f2f6"
                        )
                    )
                    st.plotly_chart(fig_eua_3d, use_container_width=True, key="dash_eua_3d")

def main():
    """Função principal do app"""
    
    # Detectar dispositivo para otimizações específicas
    st.markdown("""
    <script>
        // Detecta dispositivo e salva para uso no app
        document.addEventListener("DOMContentLoaded", function() {
            const isMobile = window.innerWidth <= 768;
            const isSmallMobile = window.innerWidth <= 480;
            
            // Armazena para uso pelo Python via sessionState
            window.parent.postMessage({
                type: "streamlit:setComponentValue",
                value: {
                    isMobile: isMobile,
                    isSmallMobile: isSmallMobile,
                    viewportWidth: window.innerWidth
                }
            }, "*");
            
            // Ajusta zoom para melhor visualização mobile
            if (isSmallMobile) {
                document.querySelector(".main").style.zoom = "0.9";
            }
        });
    </script>
    """, unsafe_allow_html=True)
    
    # Carrega dados
    with st.spinner("Carregando dados..."):
        dados = carregar_dados()
    
    # Verifica se há dados disponíveis
    if dados["brasil"] is None and dados["eua"] is None:
        st.error("Nenhum dado disponível. Execute os scripts de coleta e processamento primeiro.")
        return

    # Header customizado sem logo
    st.markdown("""
    <div class="header-container" style="display: flex; align-items: center; gap: 1.5rem; justify-content: center;">
        <div style="flex: 1;">
            <h1 class="header-title" style="margin-bottom: 0.2rem;">Monitor de Juros Brasil & EUA</h1>
            <p class="header-subtitle">Visualização interativa das superfícies de juros e comparação de curvas</p>
            <div style="text-align: center; margin-top: 1rem;">
                <span style="color: #58FFE9; font-size: 0.9rem;">
                    ● Status: Online |
                    Dados atualizados |
                    Plotly Interativo
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Barra de navegação avançada
    selected = option_menu(
        menu_title=None,  # required
        options=["📊 Curvas Brasil", "📈 Curvas EUA", "🇧🇷 Superfície Brasil", "🇺🇸 Superfície EUA"],  # required
        icons=["activity", "trending-up", "bar-chart-fill", "graph-up"],  # optional
        menu_icon="cast",  # optional
        default_index=0,  # optional
        orientation="horizontal",
        styles={
            "container": {
                "padding": "0!important", 
                "background-color": "#0e1117",
                "border-radius": "10px",
                "box-shadow": "0 4px 6px rgba(0, 0, 0, 0.1)"
            },
            "icon": {
                "color": "#58FFE9", 
                "font-size": "18px"
            },
            "nav-link": {
                "font-size": "16px",
                "text-align": "center",
                "margin": "0px",
                "padding": "12px 24px",
                "background-color": "#262730",
                "color": "#fafafa",
                "border-radius": "8px",
                "margin": "2px",
                "transition": "all 0.3s ease",
                "font-weight": "500"
            },
            "nav-link-selected": {
                "background-color": "#58FFE9",
                "color": "#0e1117",
                "font-weight": "600",
                "transform": "translateY(-2px)",
                "box-shadow": "0 4px 8px rgba(88, 255, 233, 0.3)"
            },
            "nav-link:hover": {
                "background-color": "#3a3a3a",
                "transform": "translateY(-1px)"
            }
        }
    )
    
    # Mapeia a seleção para os estados internos
    mapping = {
        "📊 Curvas Brasil": "historica_brasil",
        "📈 Curvas EUA": "historica_eua",
        "🇧🇷 Superfície Brasil": "superficie_brasil",
        "🇺🇸 Superfície EUA": "superficie_eua"
    }
    
    # Estado para controlar qual visualização está ativa
    if "visualizacao_ativa" not in st.session_state:
        st.session_state.visualizacao_ativa = "historica_brasil"
    
    # Atualiza o estado baseado na seleção
    st.session_state.visualizacao_ativa = mapping[selected]
    
    # Rodapé simplificado
    col_info1, col_info2, col_info3 = st.columns(3)
    
    with col_info1:
        st.markdown("**Fonte de Dados:** BCB, FRED")
    
    with col_info2:
        st.markdown(f"**Atualização:** {datetime.now().strftime("%d/%m/%Y às %H:%M")}")
    
    with col_info3:
        st.markdown("**Desenvolvido por:** [After Market FL](https://aftermarketfl.com.br)")
    
    # Conteúdo principal baseado na seleção
    if st.session_state.visualizacao_ativa == "historica_brasil":
        mostrar_historica_brasil(dados)
    elif st.session_state.visualizacao_ativa == "historica_eua":
        mostrar_historica_eua(dados)
    elif st.session_state.visualizacao_ativa == "superficie_brasil":
        mostrar_superficie_brasil(dados)
    elif st.session_state.visualizacao_ativa == "superficie_eua":
        mostrar_superficie_eua(dados)
    else:
        mostrar_historica_brasil(dados)  # Default para curva Brasil


if __name__ == "__main__":
    main()

