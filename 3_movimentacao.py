import streamlit as st
from supabase import create_client
import pandas as pd
import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import utils

st.set_page_config(page_title="Lançar Movimentação", layout="wide")

utils.sidebar_config()
utils.reduzir_espaco_topo()
utils.adicionar_watermark()

# --- Conexão com Supabase ---

supabase = utils.get_supabase_client()

# --- Título da Página ---

st.title("Lançar Movimentações 💸")

# 1. Buscar Obras para a Lista Suspensa
# Buscamos apenas ID e Nome para preencher o selectbox
response = supabase.table("obras").select("id, Nome").execute()
obras_dict = {row["Nome"]: row["id"] for row in response.data} # Cria um mapa {Nome: ID}

if not obras_dict:
    st.warning("Nenhuma obra cadastrada. Cadastre uma obra antes de lançar gastos.")
    st.stop()

# Selectbox retorna o Nome, mas nós queremos o ID para salvar no banco
obra_selecionada_nome = st.selectbox("Selecione a Obra", list(obras_dict.keys()))
obra_id = obras_dict[obra_selecionada_nome]

# 2. Seleção de Categoria

categoria = st.pills(
    "Tipo de Movimentação",
    ["Depósito", "Mão de Obra", "Material", "Outros"],
    selection_mode="single",
)

if categoria != None:

    # Formulário visual
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        data_mov = col1.date_input(label="Data", value=datetime.date.today())
        descricao = col3.text_input(label="Descrição", placeholder="Ex: Pagamento pedreiro, Compra Tintas")

        # --- Lógica Específica para MATERIAIS ---
        if categoria == "Material":
            
            # Criamos um DataFrame vazio para servir de template
            df_template = pd.DataFrame({
                "Item": pd.Series(dtype="string"),
                "Subcategoria": pd.Series(dtype="string"),
                "Quantidade": pd.Series(dtype="float"),
                "Valor (R$)": pd.Series(dtype="float")
            })

            itens_compra = st.data_editor(
                df_template,
                num_rows="dynamic",
                column_config={
                    "Item": st.column_config.TextColumn(required=True),
                    "Subcategoria": st.column_config.SelectboxColumn(options=utils.SUBCATEGORIAS_MATERIAIS),
                    "Quantidade": st.column_config.NumberColumn(min_value=0.1, step=1.0, required=True),
                    "Valor (R$)": st.column_config.NumberColumn(min_value=0.0, format="R$ %.2f", required=True)
                },
                hide_index=True,
                width="stretch"
            )

            total_calculado = 0.0

            if not itens_compra['Valor (R$)'].empty:
                total_calculado = itens_compra["Valor (R$)"].sum()

            valor = col2.number_input("Valor Total (R$)", value=total_calculado, format="%.2f", disabled=True)

        else:
            valor = col2.number_input("Valor Total (R$)", min_value=0.0, format="%.2f")

        # Botão de Salvar
        if st.button(f"Confirmar Lançamento em '{categoria}'"):
            try:
                if valor <= 0:
                    st.error("O valor deve ser maior que zero.")
                
                elif categoria == "Material":
                    if itens_compra.empty:
                        st.error("Adicione pelo menos um item na tabela.")
                    else:
                        # Transformamos o DataFrame em uma lista de itens para o JSON
                        itens_list = []
                        for index, row in itens_compra.iterrows():
                            if not row["Item"].strip():
                                st.error("Por favor, preencha todos os campos.")
                                st.stop()

                            itens_list.append({
                                "Item": row["Item"],
                                "Subcategoria": row["Subcategoria"],
                                "Quantidade": row["Quantidade"],
                                "Valor": row["Valor (R$)"]
                            })
                        
                        lista_envio = [{
                            "Data": data_mov.isoformat(),
                            "Detalhes": None,
                            "obra_id": obra_id,
                            "Categoria": categoria,
                            "Valor": valor,
                            "Descrição": descricao,
                            "Itens": itens_list
                        }]
                        
                        # Salvar movimentação
                        utils.salvar_movimentacao(supabase, lista_envio)
                
                # Se for OUTRAS categorias, salvamos UMA linha
                else:
                    if not descricao.strip():
                        st.error("Por favor, preencha todos os campos.")
                    else:
                        lista_envio = [{
                            "Data": data_mov.isoformat(),
                            "Detalhes": None,
                            "obra_id": obra_id,
                            "Categoria": categoria,
                            "Valor": valor,
                            "Descrição": descricao,
                        }]
                        
                        # Salvar movimentações em lote
                        utils.salvar_movimentacao(supabase, lista_envio)
                        
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
