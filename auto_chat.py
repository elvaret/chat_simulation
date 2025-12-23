from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text, inspect
from langchain_google_genai import ChatGoogleGenerativeAI
import pandas as pd
import re
import os
import json
import time
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any
from google.api_core.exceptions import ResourceExhausted



## Config awal
load_dotenv()
DATABASE_URL = "postgresql+psycopg://username:password@host:port/database" ## DATABASE PROFILE
# ini bs ganti dengan model lain, bsa pake gpt, gemini, tapi pastikan dulu karakteristik llmnya, 
# coba cek di dokumentasi masing masing provider ok (misal: gemini-1.5-flash)
MODEL_NAME = "gemini-2.5-flash-lite" 
MAX_ROWS = 100
ALLOWED_TABLES = "sales_orders"
engine = create_engine(DATABASE_URL)
llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    temperature=0,
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)
app = FastAPI()
inspector = inspect(engine)



## function get column dan cleaning llm output
def get_table_schema(table_name: str) -> dict:
    columns = inspector.get_columns(table_name)
    return {col["name"]: str(col["type"]) for col in columns}

def sanitize_sql(sql: str) -> str:
    """
    membersihkan output SQL. Fungsi ini akan membuang tulisan tdk perlu yang ada setelah tanda titik koma (;).
    """
    sql = re.sub(r"^```(?:sql)?", "", sql.strip(), flags=re.IGNORECASE)
    sql = re.sub(r"```$", "", sql).strip()
    sql = re.sub(r"--.*", "", sql)
    if ";" in sql:
        sql = sql.split(";")[0] + ";"
        
    return sql.strip()
def clean_json_text(text: str) -> str:
    """Membersihkan output JSON dari markdown -> bisa diparse"""
    text = text.strip()
    pattern = r"^```(?:json)?\s*(.*?)\s*```$"
    match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1)
    return text




## Prompting
SQL_PROMPT = """
You are a senior data analyst.
Table schema: sales_orders ({schema})

Rules:
1. Generate a valid PostgreSQL SELECT query.
2. Use ONLY the table 'sales_orders'.
3. Always LIMIT {limit} unless it's an aggregation.
4. Do NOT include markdown formatting (```sql).

Question: {question}
SQL Query:
"""

ANALYSIS_PROMPT = """
You are a data storyteller.
I will give you data from a SQL query.

Data Columns: {columns}
Data Sample (first 5 rows): {sample}

User Question: {question}

Task:
1. Provide a concise text interpretation/answer based on the data.
2. Recommend a chart if the data is suitable for visualization.

Return JSON ONLY in this format:
{{
  "answer": "Your text explanation here.",
  "chart": {{
    "type": "bar|line|pie",
    "x": "column_name_from_data",
    "y": "column_name_from_data"
  }}
}}
If no chart is needed, set "chart": null.
"""



## Validasi Pydantic
class QueryRequest(BaseModel):
    question: str

class ChartSpec(BaseModel):
    type: str
    x: str
    y: str

class QueryResponse(BaseModel):
    answer: str
    chart: Optional[ChartSpec]
    data: Optional[List[Dict[str, Any]]] = None 




## Endpoint LLM Chat Analysis
TABLE_SCHEMA = get_table_schema(ALLOWED_TABLES)
@app.post("/auto-chat-data", response_model=QueryResponse)
def auto_chat_data(req: QueryRequest):
    schema_str = ", ".join(TABLE_SCHEMA.keys())
    sql_prompt = SQL_PROMPT.format(
        question=req.question,
        limit=MAX_ROWS,
        schema=schema_str
    )
    try:
        raw_sql = llm.invoke(sql_prompt).content
        sql = sanitize_sql(raw_sql)
        print(f"DEBUG SQL: {sql}")
        with engine.connect() as conn:
            df = pd.read_sql(text(sql), conn)
        if df.empty:
            return QueryResponse(
                answer="Maaf, data tidak ditemukan untuk pertanyaan tersebut.", 
                chart=None, 
                data=[]
            )
        df_display = df.copy()
        for col in df_display.select_dtypes(include=['datetime', 'datetimetz']).columns:
            df_display[col] = df_display[col].astype(str)

        analysis_prompt = ANALYSIS_PROMPT.format(
            columns=list(df.columns),
            sample=df_display.head(5).to_dict(orient='records'),
            question=req.question
        )
        raw_analysis = llm.invoke(analysis_prompt).content
        print(f"Analisis llm: {raw_analysis}")
        cleaned_json = clean_json_text(raw_analysis)
        try:
            result = json.loads(cleaned_json)
        except json.JSONDecodeError:
            return QueryResponse(
                answer="Berikut datanya (gagal memproses analiis otomatis).",
                chart=None,
                data=df_display.to_dict(orient="records")
            )
        chart = result.get("chart")
        if chart:
            if chart["x"] not in df.columns or chart["y"] not in df.columns:
                chart = None 
        return QueryResponse(
            answer=result["answer"],
            chart=chart,
            data=df_display.to_dict(orient="records")
        )
    except ResourceExhausted:
        raise HTTPException(status_code=429, detail="Kuota gratis API google Gemini abis. wait...")
    except Exception as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))




