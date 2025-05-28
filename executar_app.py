#!/usr/bin/env python3
"""
Script de Execução Completa - Superfície de Juros
Executa todo o pipeline: coleta -> processamento -> app
"""

import subprocess
import sys
import os
from datetime import datetime

def executar_comando(comando, descricao):
    """Executa um comando e trata erros"""
    print(f"\n{'='*60}")
    print(f"🔄 {descricao}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(comando, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {descricao} - Concluído com sucesso!")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro em {descricao}:")
        print(f"Código de erro: {e.returncode}")
        if e.stdout:
            print(f"Saída: {e.stdout}")
        if e.stderr:
            print(f"Erro: {e.stderr}")
        return False

def verificar_dependencias():
    """Verifica se as dependências estão instaladas"""
    print("🔍 Verificando dependências...")
    
    dependencias = [
        'streamlit', 'pandas', 'numpy', 'plotly', 'scipy', 
        'requests', 'lxml', 'bizdays', 'bcb', 'pandas_datareader'
    ]
    
    faltando = []
    for dep in dependencias:
        try:
            __import__(dep)
        except ImportError:
            faltando.append(dep)
    
    if faltando:
        print(f"❌ Dependências faltando: {', '.join(faltando)}")
        print("📦 Instalando dependências...")
        if executar_comando("pip install -r requirements.txt", "Instalação de dependências"):
            print("✅ Dependências instaladas com sucesso!")
        else:
            print("❌ Falha na instalação das dependências")
            return False
    else:
        print("✅ Todas as dependências estão instaladas!")
    
    return True

def main():
    """Função principal"""
    print(f"""
    🌍 SUPERFÍCIE DE JUROS BRASIL x EUA
    {'='*50}
    Iniciado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    
    Este script executará:
    1️⃣  Verificação de dependências
    2️⃣  Coleta de dados (Brasil e EUA)
    3️⃣  Processamento dos dados
    4️⃣  Inicialização do app Streamlit
    """)
    
    # Muda para o diretório correto
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    print(f"📁 Diretório de trabalho: {script_dir}")
    
    # 1. Verificar dependências
    if not verificar_dependencias():
        print("❌ Falha na verificação de dependências. Abortando.")
        return
    
    # 2. Coleta de dados
    if not executar_comando("python 1_coleta_dados.py", "Coleta de dados"):
        print("⚠️  Falha na coleta de dados, mas continuando...")
    
    # 3. Processamento de dados
    if not executar_comando("python 2_processa_dados.py", "Processamento de dados"):
        print("⚠️  Falha no processamento de dados, mas continuando...")
    
    # 4. Verificar se há dados para o app
    dados_brasil = "Dados/juros_brasil_processado.parquet"
    dados_eua = "Dados/juros_eua_processado.parquet"
    
    if not (os.path.exists(dados_brasil) or os.path.exists(dados_eua)):
        print("❌ Nenhum dado processado encontrado. Verifique os scripts de coleta e processamento.")
        return
    
    # 5. Iniciar app Streamlit
    print(f"\n{'='*60}")
    print("🚀 INICIANDO APP STREAMLIT")
    print(f"{'='*60}")
    print("📱 O app será aberto no seu navegador automaticamente")
    print("🔗 URL: http://localhost:8501")
    print("⏹️  Para parar o app, pressione Ctrl+C no terminal")
    print(f"{'='*60}\n")
    
    # Comando do Streamlit
    comando_streamlit = "streamlit run 3_app_streamlit.py --server.headless false"
    
    try:
        subprocess.run(comando_streamlit, shell=True, check=True)
    except KeyboardInterrupt:
        print("\n🛑 App interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao executar o app: {e}")

if __name__ == "__main__":
    main()
