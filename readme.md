# Chat Simulation Project

Project ini adalah aplikasi **chat simulation berbasis AI** dengan:
- **Backend**: FastAPI (Uvicorn)
- **Frontend**: Streamlit
- **Database**: PostgreSQL
- **Use case**: eksplorasi data `sales_orders` secara *read-only* dengan LLM

---

## Database Setup (PostgreSQL)

### Create Table
```sql
CREATE TABLE sales_orders (
    ordernumber        INTEGER,
    quantityordered    INTEGER,
    priceeach          NUMERIC(10,2),
    orderlinenumber    INTEGER,
    sales              NUMERIC(12,2),
    orderdate          TIMESTAMP,
    status             VARCHAR(20),
    qtr_id             INTEGER,
    month_id           INTEGER,
    year_id            INTEGER,
    productline        VARCHAR(50),
    msrp               INTEGER,
    productcode        VARCHAR(20),
    customername       VARCHAR(100),
    phone              VARCHAR(20),
    addressline1       VARCHAR(150),
    addressline2       VARCHAR(150),
    city               VARCHAR(50),
    state              VARCHAR(50),
    postalcode         VARCHAR(20),
    country            VARCHAR(50),
    territory          VARCHAR(20),
    contactlastname    VARCHAR(50),
    contactfirstname   VARCHAR(50),
    dealsize           VARCHAR(20)
);



## Create DATABASE Profile 
CREATE ROLE XXX LOGIN PASSWORD 'YYY';
GRANT CONNECT ON DATABASE XXX TO XXX;
GRANT USAGE ON SCHEMA public TO XXX;
GRANT SELECT ON sales_orders TO XXX;  --> perhatikan aksesnya


## run streamlit (FE) dan uvicorn (BE)
streamlit run main.py
uvicorn auto_chat:app --reload




