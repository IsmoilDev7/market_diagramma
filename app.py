import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Sotuv Analitikasi", layout="wide")
st.title("📊 Sotuv va Foyda Analitikasi (2025 Dekabr)")

# ==========================
# 1. Excel upload
# ==========================
st.sidebar.header("📤 Excel fayllarni yuklash")
sales_file = st.sidebar.file_uploader("📈 Sotuvlar (sales.xlsx)", type=["xlsx"])
returns_file = st.sidebar.file_uploader("🔄 Qaytishlar (returns.xlsx)", type=["xlsx"])

if not sales_file or not returns_file:
    st.warning("Ikkala Excel faylni ham yuklang")
    st.stop()

# ==========================
# 2. Ma'lumotlarni yuklash
# ==========================
@st.cache_data
def load_data(sales_file, returns_file):
    sales = pd.read_excel(sales_file)
    returns = pd.read_excel(returns_file)

    sales['Период'] = pd.to_datetime(sales['Период'], errors='coerce')
    returns['Период'] = pd.to_datetime(returns['Период'], errors='coerce')
    sales = sales.dropna(subset=['Период'])
    returns = returns.dropna(subset=['Период'])

    sales = sales.rename(columns={
        'Контрагент': 'client',
        'Номенклатура': 'product',
        'Количество': 'qty_sale',
        'Сумма': 'amount_sale'
    })
    returns = returns.rename(columns={
        'Контрагент': 'client',
        'Номенклатура': 'product',
        'Возрат количество': 'qty_return',
        'Возврат сумма': 'amount_return'
    })

    sales['amount_sale'] = pd.to_numeric(sales['amount_sale'], errors='coerce').fillna(0)
    returns['amount_return'] = pd.to_numeric(returns['amount_return'], errors='coerce').fillna(0)
    
    return sales, returns

sales, returns = load_data(sales_file, returns_file)

# ==========================
# 3. Filtrlar
# ==========================
st.sidebar.subheader("📊 Filterlar")
status_filter = st.sidebar.multiselect("Status", ["FOYDA","ZARAR"], default=["FOYDA","ZARAR"])
clients_filter = st.sidebar.multiselect("Klientlar", sales['client'].unique())
products_filter = st.sidebar.multiselect("Mahsulotlar", sales['product'].unique())
date_range = st.sidebar.date_input("Sana oraligi", [sales['Период'].min(), sales['Период'].max()])

# Filterlash
df_sales = sales.copy()
df_returns = returns.copy()

if clients_filter:
    df_sales = df_sales[df_sales['client'].isin(clients_filter)]
    df_returns = df_returns[df_returns['client'].isin(clients_filter)]
if products_filter:
    df_sales = df_sales[df_sales['product'].isin(products_filter)]
    df_returns = df_returns[df_returns['product'].isin(products_filter)]

df_sales = df_sales[(df_sales['Период'].dt.date >= date_range[0]) & (df_sales['Период'].dt.date <= date_range[1])]
df_returns = df_returns[(df_returns['Период'].dt.date >= date_range[0]) & (df_returns['Период'].dt.date <= date_range[1])]

# ==========================
# 4. Kunlik sof foyda/zarar
# ==========================
daily = df_sales.groupby('Период')['amount_sale'].sum().reset_index()
daily_returns = df_returns.groupby('Период')['amount_return'].sum().reset_index()
daily = daily.merge(daily_returns, on='Период', how='left').fillna(0)
daily['net_profit'] = daily['amount_sale'] - daily['amount_return']
daily['status'] = np.where(daily['net_profit']>0,'FOYDA','ZARAR')
daily = daily[daily['status'].isin(status_filter)]

st.subheader("📅 Kunlik sof foyda/zarar (Bar chart)")
fig_daily = px.bar(
    daily,
    x='Период',
    y='net_profit',
    color='status',
    color_discrete_map={'FOYDA':'green', 'ZARAR':'red'},
    hover_data={'amount_sale': True, 'amount_return': True, 'net_profit': ':.2f'},
    labels={'Период':'Sana', 'net_profit':'Sof foyda'}
)
st.plotly_chart(fig_daily, use_container_width=True)

# ==========================
# 5. Klient kesimi
# ==========================
client_profit = df_sales.groupby('client')['amount_sale'].sum() - df_returns.groupby('client')['amount_return'].sum()
client_profit = client_profit.fillna(0).reset_index()
client_profit.columns = ['client', 'net_profit']
client_profit['status'] = np.where(client_profit['net_profit']>0,'FOYDA','ZARAR')
client_profit = client_profit[client_profit['status'].isin(status_filter)]

st.subheader("🧑‍💼 Klient kesimi (Gorizontal bar chart)")
fig_client = px.bar(
    client_profit.sort_values('net_profit', ascending=True),
    x='net_profit',
    y='client',
    color='net_profit',
    color_continuous_scale='RdYlGn',
    orientation='h',
    hover_data={'net_profit': ':.2f'},
    labels={'client':'Klient', 'net_profit':'Sof foyda'}
)
st.plotly_chart(fig_client, use_container_width=True)

# ==========================
# 6. Foyda/Zarar ulushi
# ==========================
summary_status = daily.groupby('status')['net_profit'].sum().reset_index()
st.subheader("📊 Foyda/Zarar ulushi (Pie chart)")
fig_pie = px.pie(
    summary_status,
    values='net_profit',
    names='status',
    color='status',
    color_discrete_map={'FOYDA':'green', 'ZARAR':'red'},
    hover_data=['net_profit']
)
fig_pie.update_traces(textinfo='label+percent', texttemplate='%{label}: %{value:,.2f}')
st.plotly_chart(fig_pie, use_container_width=True)

# ==========================
# 7. Mahsulot kesimi
# ==========================
product_profit = df_sales.groupby('product')['amount_sale'].sum() - df_returns.groupby('product')['amount_return'].sum()
product_profit = product_profit.fillna(0).reset_index()
product_profit.columns = ['product','net_profit']
product_profit['status'] = np.where(product_profit['net_profit']>0,'FOYDA','ZARAR')
product_profit = product_profit[product_profit['status'].isin(status_filter)]

st.subheader("📦 Mahsulot kesimi (Treemap)")
fig_product = px.treemap(
    product_profit,
    path=['status','product'],
    values='net_profit',
    color='net_profit',
    color_continuous_scale='RdYlGn',
    hover_data={'net_profit': ':.2f'}
)
st.plotly_chart(fig_product, use_container_width=True)
