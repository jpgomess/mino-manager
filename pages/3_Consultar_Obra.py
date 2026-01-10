import streamlit as st
from supabase import create_client
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

st.set_page_config(page_title="Consultar Obra", layout="wide")

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

st.title("Painel da Obra 📊")

# 1. Carregar Lista de Obras
response = supabase.table("obras").select("id, Nome").execute()
obras_dict = {row["Nome"]: row["id"] for row in response.data}

if not obras_dict:
    st.warning("Nenhuma obra encontrada.")
    st.stop()

# Selectbox para escolher a obra
obra_nome = st.selectbox("Selecione a Obra para analisar:", list(obras_dict.keys()))
obra_id = obras_dict[obra_nome]

# 2. Buscar Detalhes da Obra Selecionada
dados_obra = supabase.table("obras").select("*").eq("id", obra_id).execute().data[0]

# 3. Buscar Todas as Movimentações dessa Obra
movimentacoes = supabase.table("movimentacoes").select("*").eq("obra_id", obra_id).execute().data

# --- Exibir Informações da Obra ---

with st.expander("Detalhes da Obra"):
    col1, col2 = st.columns(2)
    col1.markdown(f"**Nome da Obra:** {dados_obra['Nome']}")
    col1.markdown(f"**Endereço:** {dados_obra.get('Endereço', 'N/A')}")
    col1.markdown(f"**Orçamento:** R$ {float(dados_obra['Orçamento']):,.2f}")
    col2.markdown(f"**Cliente:** {dados_obra.get('Cliente_Nome', 'N/A')}")
    col2.markdown(f"**CPF do Cliente:** {dados_obra.get('Cliente_CPF', 'N/A')}")
    col_data1, col_data2 = col2.columns(2)
    col_data1.markdown(f"**Data de Início:** {dados_obra.get('Data_Início', 'N/A')}")
    col_data2.markdown(f"**Data de Término:** {dados_obra.get('Data_Fim', 'N/A')}")

# --- Exibir Informações Gerais (Cards no Topo) ---
col1, col2, col3 = st.columns(3)

orcamento_total = float(dados_obra["Orçamento"]) if dados_obra["Orçamento"] else 0.0

if movimentacoes:
    df = pd.DataFrame(movimentacoes)
    # Garante que a coluna valor é numérica
    df["Valor"] = pd.to_numeric(df["Valor"])
    
    total_gasto = df["Valor"].sum()
    saldo = orcamento_total - total_gasto
    
    # Cálculos por Categoria (para gráficos)
    gastos_por_cat = df.groupby("Categoria")["Valor"].sum().reset_index()
else:
    df = pd.DataFrame() # Tabela vazia
    total_gasto = 0.0
    saldo = orcamento_total

# Métricas Visuais (KPIs)
col1.metric("Orçamento Total", f"R$ {orcamento_total:,.2f}")
col2.metric("Total Gasto", f"R$ {total_gasto:,.2f}", delta=f"-{(total_gasto/orcamento_total)*100:.1f}%" if orcamento_total > 0 else "")
col3.metric("Saldo Disponível", f"R$ {saldo:,.2f}")

# --- Conteúdo Detalhado (Tabs conforme Item 2.d e 4.a do PDF) ---
tab_tabela, tab_graficos = st.tabs(["📝 Extrato Detalhado", "📈 Visão Gráfica"])

with tab_tabela:
    if not df.empty:
        st.subheader("Extrato de Lançamentos")
        # Filtros rápidos
        filtro_cat = st.multiselect("Filtrar Categoria:", df["Categoria"].unique())
        
        df_show = df.copy()
        if filtro_cat:
            df_show = df_show[df_show["Categoria"].isin(filtro_cat)]
            
        # Limpeza visual da tabela
        colunas_visiveis = ["Data", "Detalhes", "Quantidade", "Valor", "Categoria", "Descrição"]
        st.dataframe(
            df_show[colunas_visiveis], 
            width="stretch",
            column_config={
                "Valor": st.column_config.NumberColumn(format="R$ %.2f"),
                "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY")
            }
        )

with tab_graficos:
    if not df.empty:
        col_g1, col_g2 = st.columns(2)
        
        # Gráfico de Pizza (Gastos por Categoria)
        fig_pizza = px.pie(gastos_por_cat, values='Valor', names='Categoria', title='Gastos por Categoria')
        fig_pizza.update_layout(plot_bgcolor='rgba(0, 0, 0, 0)',  paper_bgcolor='rgba(0, 0, 0, 0)', legend=dict(bgcolor='rgba(0, 0, 0, 0)'))

        col_g1.plotly_chart(fig_pizza, width="stretch")
        
        # Gráfico de Barras (Evolução no Tempo se houver data)
        if "Data" in df.columns:
            df_temp = df.sort_values("Data")
            fig_barras = px.bar(df_temp, x="Data", y="Valor", color="Categoria", title="Gastos ao Longo do Tempo")
            fig_barras.update_layout(plot_bgcolor='rgba(0, 0, 0, 0)',  paper_bgcolor='rgba(0, 0, 0, 0)', legend=dict(bgcolor='rgba(0, 0, 0, 0)'))

            col_g2.plotly_chart(fig_barras, width="stretch")

if df.empty:
    st.info("Nenhuma movimentação lançada nesta obra ainda.")