import streamlit as st
import requests
import plotly.express as px
import pandas as pd



## Connect backend
API_URL = "http://localhost:8000/auto-chat-data"

## FE
st.set_page_config(page_title="AI Data Analyst Simulation", layout="wide")
st.markdown(
    "<h2 style='text-align:center;'>AI Data Analyst Dashboard (ESGUL Preview)</h2>",
    unsafe_allow_html=True
)
with st.form(key="query_form"):
    question = st.text_input("Tanya data Anda (contoh: Top 5 kota dengan penjualan tertinggi):")
    submit_button = st.form_submit_button("Analisa Data")
if submit_button and question:
    with st.spinner("Sedang berpikir & query database..."):
        try:
            response = requests.post(
                API_URL,
                json={"question": question},
                timeout=60
            )
            if response.status_code == 429:
                st.warning("tunggu sbtr, AI sedang 'cooling down'. Silakan coba 30 detik lagi (ini limit kuota Free Tier).")
                st.stop()
            if response.status_code != 200:
                st.error(f"Error Server: {response.text}")
                st.stop()
            result = response.json()
            st.markdown("### Hasil analisis llm")
            st.info(result["answer"])
            data_rows = result.get("data")
            chart_config = result.get("chart")
            if data_rows:
                df_result = pd.DataFrame(data_rows)
                col1, col2 = st.columns([2, 1])
                with col1:
                    if chart_config:
                        st.markdown(f"**Visualisasi ({chart_config['type']})**")
                        try:
                            if chart_config["type"] == "bar":
                                fig = px.bar(df_result, x=chart_config["x"], y=chart_config["y"], template="plotly_white")
                            elif chart_config["type"] == "line":
                                fig = px.line(df_result, x=chart_config["x"], y=chart_config["y"], markers=True, template="plotly_white")
                            elif chart_config["type"] == "pie":
                                fig = px.pie(df_result, names=chart_config["x"], values=chart_config["y"], template="plotly_white")
                            st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.warning(f"Gagal render chart: {e}")
                    else:
                        st.text("Tidak ada grafik yang cocok untuk data ini.")
                with col2:
                    st.markdown("**Data Tabel**")
                    st.dataframe(df_result, use_container_width=True)
            else:
                st.warning("Tidak ada data yang ditemukan.")
        except requests.exceptions.ConnectionError:
            st.error("Gagal terhubung ke backend. Pastikan `auto_chat.py` sudah berjalan: uvicorn server.")
        except Exception as e:
            st.error(f"Terjadi kesalahan aplikasi: {e}")