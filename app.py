import streamlit as st

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
