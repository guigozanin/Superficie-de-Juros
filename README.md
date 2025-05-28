# 🌍 Superfície de Juros Brasil x EUA

Uma aplicação Streamlit para visualização interativa das superfícies de juros do Brasil e dos Estados Unidos, com análise comparativa de curvas temporais.

## 📋 Características

### 🏔️ Superfícies 3D
- Visualização tridimensional da evolução temporal das curvas de juros
- Representação completa do período histórico disponível
- Destaque da curva mais recente

### 📊 Comparação de Curvas
- Comparação entre curvas de datas selecionáveis
- Análise de mudanças na estrutura a termo
- Métricas de movimento da curva (paralelo, achatamento, inclinação)

### 📈 Análise Temporal
- Evolução histórica por maturidade
- Estatísticas descritivas do período
- Gráficos interativos com múltiplas séries

## 🚀 Como Usar

### Opção 1: Execução Automática (Recomendada)
```bash
python executar_app.py
```
Este script executa todo o pipeline automaticamente:
1. Verifica dependências
2. Coleta dados
3. Processa dados
4. Inicia o app Streamlit

### Opção 2: Execução Manual
```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Coletar dados
python 1_coleta_dados.py

# 3. Processar dados
python 2_processa_dados.py

# 4. Executar app
streamlit run 3_app_streamlit.py
```

## 📁 Estrutura do Projeto

```
Curva de Juros 3D/
├── 1_coleta_dados.py          # Coleta dados do Brasil e EUA
├── 2_processa_dados.py        # Processa dados para visualização
├── 3_app_streamlit.py         # Aplicação Streamlit principal
├── executar_app.py            # Script de execução completa
├── requirements.txt           # Dependências Python
├── README.md                  # Este arquivo
├── Dados/                     # Dados processados
│   ├── Base_Bruta.parquet     # Dados brutos do Brasil
│   ├── juros_eua_bruto.parquet # Dados brutos dos EUA
│   ├── juros_brasil_processado.parquet # Dados processados do Brasil
│   └── juros_eua_processado.parquet    # Dados processados dos EUA
└── Modelo Básico Juros 10 anos BR.py  # Script original
```

## 📊 Fontes de Dados

### 🇧🇷 Brasil
- **Fonte:** B3 (Brasil, Bolsa, Balcão)
- **Dados:** Contratos futuros DI1
- **Maturidades:** 21 dias até 8558 dias úteis
- **Atualização:** Diária (dias úteis)

### 🇺🇸 Estados Unidos
- **Fonte:** FRED (Federal Reserve Economic Data)
- **Dados:** US Treasury Yield Curve
- **Maturidades:** 1 mês até 30 anos
- **Atualização:** Diária

## 🛠️ Dependências

- **streamlit** >= 1.28.0 - Interface web
- **pandas** >= 2.0.0 - Manipulação de dados
- **plotly** >= 5.15.0 - Gráficos interativos
- **scipy** >= 1.10.0 - Interpolação científica
- **bizdays** >= 1.0.10 - Calendário financeiro brasileiro
- **bcb** >= 0.1.9 - API do Banco Central
- **pandas-datareader** >= 0.10.0 - Dados financeiros

## 🎯 Funcionalidades Detalhadas

### Superfícies 3D
- **Visualização:** Representação tridimensional onde X = Maturidade, Y = Tempo, Z = Taxa
- **Interatividade:** Rotação, zoom, hover com informações detalhadas
- **Destaque:** Linha preta marcando a curva mais recente

### Comparação de Curvas
- **Seleção flexível:** Escolha qualquer duas datas disponíveis
- **Ações rápidas:** Botão para comparar início vs fim do ano
- **Análise automática:** Cálculo de mudanças em taxas curtas e longas
- **Interpretação:** Identificação de movimentos paralelos, achatamento ou inclinação

### Métricas em Tempo Real
- **Última atualização:** Data do último dado disponível
- **Taxa curto prazo:** Menor maturidade da curva atual
- **Taxa longo prazo:** Maior maturidade da curva atual
- **Inclinação:** Diferença entre longo e curto prazo

## 🔧 Configuração Avançada

### Personalização de Horizontes (Brasil)
Para modificar as maturidades calculadas, edite a lista `horizons` em `2_processa_dados.py`:

```python
horizons = [
    21, 63, 126,          # Curto prazo
    252, 504, 756,        # Médio prazo
    1008, 1260, 1512,     # Longo prazo
    # ... adicione mais conforme necessário
]
```

### Ajuste de Período de Coleta
Para alterar o período de coleta de dados, modifique em `1_coleta_dados.py`:

```python
# Para coletar desde uma data específica
last_date = datetime.datetime(2020, 1, 1)  # Altere conforme necessário
```

## 🎨 Interface do Usuário

### Design
- **Layout responsivo:** Adapta-se a diferentes tamanhos de tela
- **Cores temáticas:** Azul para Brasil, laranja para EUA
- **Navegação intuitiva:** Tabs organizadas por tipo de análise

### Interatividade
- **Gráficos Plotly:** Zoom, pan, hover, download
- **Seletores de data:** Calendário integrado
- **Métricas dinâmicas:** Atualização automática baseada na seleção

## ⚠️ Troubleshooting

### Erro de Coleta de Dados
```
Erro ao processar a data X: HTTPError
```
**Solução:** Site da B3 pode estar indisponível. Tente novamente mais tarde.

### Erro de Dependências
```
ImportError: No module named 'bizdays'
```
**Solução:** 
```bash
pip install -r requirements.txt
```

### Dados Não Aparecem no App
1. Verifique se os arquivos `.parquet` foram gerados na pasta `Dados/`
2. Execute novamente os scripts de coleta e processamento
3. Verifique conexão com internet para dados dos EUA

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique se todas as dependências estão instaladas
2. Execute os scripts na ordem correta
3. Verifique se há dados na pasta `Dados/`

## 📄 Licença

Desenvolvido por **After Market FL** para análise educacional e profissional do mercado financeiro.

---

**🎯 Dica:** Para melhor experiência, use o navegador em tela cheia e explore as funcionalidades interativas dos gráficos Plotly!
