import streamlit as st

# --- CONEXÃO COM O BANCO ---
supabase = utils.get_supabase_client()

# --- VERIFICAÇÃO ÚNICA ---
usuario = utils.verificar_login(supabase)

if usuario:
    pg = st.navigation(
    {
        "": [st.Page("1_home.py", title="Home", icon=":material/home:")],
        "Cadastro": [
            st.Page("2_page_cadastro_obra.py", title="Cadastro de Obra", icon=":material/add_home_work:"),
            st.Page("3_movimentacao.py", title="Lançamento", icon=":material/list_alt_add:"),
            st.Page("4_extrato.py", title="Importar Extrato", icon=":material/upload_file:"),
        ],
        "Consulta": [
            st.Page("5_consulta_obra.py", title="Consulta de Obra", icon=":material/manage_search:"),
            st.Page("6_consulta_material.py", title="Consulta de Material", icon=":material/construction:"),
        ]
    }
    )
else:
    pg = st.navigation([st.Page(lambda: utils.pagina_login(supabase), title="Login", icon=":material/login:")])

pg.run()
