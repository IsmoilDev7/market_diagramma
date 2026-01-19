import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Sotuv Diagramalari", layout="wide")
st.title("📊 Sotuv va Foyda Diagramalari (2025 Dekabr)")

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
# 2. Ma'lumotlarni yuklash va tozalash
# ==========================
@st.cache_data
def load_data(sales_file, returns_file):
    sales = pd.read_excel(sales_file)
    returns = pd.read_excel(returns_file)
    
    # datetime format va bo'sh qiymatlarni tozalash
    sales['Период'] = pd.to_datetime(sales['Период'], errors='coerce')
    returns['Период'] = pd.to_datetime(returns['Период'], errors='coerce')
    sales = sales.dropna(subset=['Период'])
    returns = returns.dropna(subset=['Период'])
    
    # Ustunlar nomini inglizcha
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
    
    # numeric conversion
    sales['amount_sale'] = pd.to_numeric(sales['amount_sale'], errors='coerce').fillna(0)
    returns['amount_return'] = pd.to_numeric(returns['amount_return'], errors='coerce').fillna(0)
    
    return sales, returns

sales, returns = load_data(sales_file, returns_file)

# ==========================
# 3. Kunlik foyda / zarar
# ==========================
daily_sales = sales.groupby('Период')['amount_sale'].sum()
daily_returns = returns.groupby('Период')['amount_return'].sum()
daily = pd.concat([daily_sales, daily_returns], axis=1).fillna(0)
daily['net_profit'] = daily['amount_sale'] - daily['amount_return']
daily['status'] = np.where(daily['net_profit'] > 0, 'FOYDA', 'ZARAR')

# ==========================
# 4. Klient kesimi
# ==========================
client_sales = sales.groupby('client')['amount_sale'].sum()
client_returns = returns.groupby('client')['amount_return'].sum()
client_profit = (client_sales - client_returns).fillna(0).reset_index()
client_profit.columns = ['client', 'net_profit']
client_profit['status'] = np.where(client_profit['net_profit'] > 0, 'FOYDA', 'ZARAR')

# ==========================
# 5. Diagramma 1: Kunlik foyda/zarar
# ==========================
st.subheader("📅 Kunlik foyda / zarar (2025 Dekabr)")
daily_summary = daily.groupby('status')['net_profit'].sum().reset_index()

fig_daily = px.pie(
    daily_summary,
    values='net_profit',
    names='status',
    title="Kunlik foyda va zarar ulushi",
    color='status',
    color_discrete_map={'FOYDA':'green', 'ZARAR':'red'},
    hover_data=['net_profit']  # faqat ustun nomi
)
# Sonlarni diagrammada 2 decimal bilan ko'rsatish
fig_daily.update_traces(
    textposition='inside',
    texttemplate='%{label}: %{value:,.2f}'
)
st.plotly_chart(fig_daily, use_container_width=True)
st.markdown("💡 Yashil → foyda, Qizil → zarar. Hover va bosilganda tafsilot ko‘rinadi.")

# ==========================
# 6. Diagramma 2: Klient kesimi
# ==========================
st.subheader("🧑‍💼 Klient kesimida foyda/zarar")
client_summary = client_profit.groupby('status')['net_profit'].sum().reset_index()

fig_client = px.pie(
    client_summary,
    values='net_profit',
    names='status',
    title="Klientlar bo‘yicha sof foyda va zarar",
    color='status',
    color_discrete_map={'FOYDA':'green', 'ZARAR':'red'},
    hover_data=['net_profit']
)
fig_client.update_traces(
    textposition='inside',
    texttemplate='%{label}: %{value:,.2f}'
)
st.plotly_chart(fig_client, use_container_width=True)
st.markdown("💡 Yashil → foyda, Qizil → zarar. Hover va bosilganda tafsilot ko‘rinadi.")

# ==========================
# 7. Individual klientlar diagrammasi
# ==========================
st.subheader("👤 Individual klientlar tafsiloti")
selected_status = st.radio("Foyda yoki zarar klientlar", options=['FOYDA', 'ZARAR'])
filtered_clients = client_profit[client_profit['status'] == selected_status]

fig_client_individual = px.pie(
    filtered_clients,
    values='net_profit',
    names='client',
    title=f"{selected_status} klientlar bo‘yicha ulush",
    hover_data=['net_profit']
)
fig_client_individual.update_traces(
    textposition='inside',
    texttemplate='%{label}: %{value:,.2f}'
)
st.plotly_chart(fig_client_individual, use_container_width=True)
st.markdown("💡 Bosilganda klient nomi va net foydasi ko‘rinadi.")
