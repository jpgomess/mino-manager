import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

st.set_page_config(page_title="Importar Extrato", layout="wide")

utils.sidebar_config()
utils.reduzir_espaco_topo()
utils.adicionar_watermark()

# --- Conexão com Supabase ---
def init_connection():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

if "supabase" not in st.session_state:
    st.session_state["supabase"] = init_connection()

supabase = st.session_state["supabase"]

# --- Segurança ---

usuario = utils.verificar_login(supabase)

# --- Título da Página ---

st.title("Importar Extrato Bancário 📥")
st.markdown("Carregue uma planilha Excel para classificar e lançar múltiplas movimentações de uma vez.")

# --- 1. Carregar Dados Auxiliares (Obras) ---
# Precisamos disso para criar o menu suspenso dentro da tabela
try:
    res_obras = supabase.table("obras").select("id, Nome").execute()
    # Criamos dois dicionários:
    # 1. Lista de nomes para o Dropdown
    lista_nomes_obras = [row["Nome"] for row in res_obras.data]
    # 2. Mapa para descobrir o ID depois que o usuário escolher o Nome
    mapa_obras_id = {row["Nome"]: row["id"] for row in res_obras.data}
except Exception as e:
    st.error(f"Erro ao carregar obras: {e}")
    st.stop()

# --- 2. Upload do Arquivo ---
arquivo = st.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx"])

if arquivo:
    try:
        # Lê o arquivo Excel
        df_raw = pd.read_excel(arquivo)

        # Verifica se as colunas esperadas existem
        colunas_esperadas = ["Data", "Detalhes", "Valor"]
        
        df_cols = [c.lower() for c in df_raw.columns]
        if not all(col.lower() in df_cols for col in colunas_esperadas):
            st.error(f"O arquivo precisa ter as colunas: {colunas_esperadas}. Colunas encontradas: {list(df_raw.columns)}")
            st.stop()

        # Remove linhas desnecessárias
        df_extrato = df_raw.copy()[df_raw["Detalhes"] != " "]

        # Remove colunas desnecessárias
        # Formata as colunas
        # Adiciona colunas vazias para Obra, Categoria e Descrição
        df_extrato = pd.DataFrame({
            "Data": pd.to_datetime(df_extrato["Data"], dayfirst=True).dt.date,
            "Detalhes": df_extrato["Detalhes"].astype("string"),
            "Obra": pd.Series(dtype="string"),
            "Categoria": pd.Series(dtype="string"),
            "Valor": df_extrato["Valor"].astype(str).str.replace(".", "", regex=False).str.replace(",", ".", regex=False).astype(float),
            "Descrição": pd.Series(dtype="string"),
        })

        # Preenche Categoria automaticamente com "Depósito" para valores positivos
        df_extrato.loc[df_extrato["Valor"] > 0, "Categoria"] = "Depósito"

        # Transforma todos os valores em positivos
        df_extrato.loc[:, "Valor"] = df_extrato["Valor"].abs()

        # --- 4. Tabela Editável ---
        st.info("Classifique as movimentações abaixo.")

        df_editado = st.data_editor(
            df_extrato,
            column_config={
                "Data": st.column_config.DateColumn(label="Data", disabled=True),
                "Detalhes": st.column_config.TextColumn(label="Detalhes", disabled=True),
                "Obra": st.column_config.TextColumn(label="Obra", required=True),
                "Categoria": st.column_config.SelectboxColumn(
                    label="Categoria",
                    options=["Material", "Mão de Obra", "Depósito", "Outros"],
                    required=True,
                ),
                "Valor": st.column_config.NumberColumn(label="Valor (R$)", format="R$ %.2f", disabled=True),
                "Descrição": st.column_config.TextColumn(label="Descrição", required=True),
            },
            hide_index=True,
            width="stretch",
            num_rows="fixed" # Não deixa adicionar linhas, apenas editar as existentes
        )

        # --- 5. Processamento e Salvamento ---
        col_btn, col_info = st.columns([1, 4])
        
        # Filtra apenas as linhas preenchidas
        df_valido = df_editado.replace(r'^\s*$', pd.NA, regex=True).dropna(subset=["Obra", "Categoria", "Descrição"])

        with col_btn:
            if st.button("Salvar Lançamentos", type="primary", disabled=(len(df_valido) == 0)):
                try:
                    lista_envio = []
                    obras_desconhecidas = []
                    lista_material = []
                    
                    for index, row in df_valido.iterrows():
                        # Verifica se a Obra existe
                        obra = row["Obra"].upper()
                        if obra not in mapa_obras_id:
                            obras_desconhecidas.append(obra)
                            continue

                        # Verifica se é Material para detalhar
                        if row["Categoria"] == "Material":
                            lista_material.append(row)
                            continue

                        # Busca o ID da Obra pelo Nome
                        obra_id = mapa_obras_id[obra]

                        # Monta o objeto para o Supabase
                        item = {
                            "Data": row["Data"].isoformat(),
                            "Detalhes": row["Detalhes"],
                            "obra_id": obra_id,
                            "Categoria": row["Categoria"],
                            "Valor": float(row["Valor"]),
                            "Descrição": row["Descrição"],
                        }
                        lista_envio.append(item)
                    
                    if len(obras_desconhecidas) == 0:
                        # Detalhar e salvar movimentações de "Material"
                        if len(lista_material) > 0:
                            st.session_state["modal"] = "Selecionar"
                            utils.popup_detalhar_material(supabase, lista_material)
                            
                        # Salvar as outras movimentações
                        if len(lista_envio) > 0:
                            utils.salvar_movimentacao(supabase, lista_envio, col_info)
                    else:
                        # Cadastrar novas obra
                        utils.popup_cadastro_obras(supabase, obras_desconhecidas)

                except Exception as e:
                    st.error(f"Erro ao gravar no banco: {e}")

    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {e}. Verifique se é um Excel válido.")