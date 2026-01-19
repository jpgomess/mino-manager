import streamlit as st
from supabase import create_client
import utils

# --- Inicialização do Supabase (Global) ---
if "supabase" not in st.session_state:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    st.session_state["supabase"] = create_client(url, key)

supabase = st.session_state["supabase"]

# --- Verificação de Autenticação ---
usuario = utils.recuperar_sessao(supabase)

# --- Definição das Páginas ---
if not usuario:
    # Se NÃO estiver logado, a única página existente é a de Login
    # Usamos um wrapper para chamar a função tela_login do utils
    def pagina_login():
        utils.tela_login(supabase)

    pg = st.navigation([st.Page(pagina_login, title="Login", icon=":material/login:")])

else:
    # Se ESTIVER logado, carrega a estrutura completa
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

pg.run()