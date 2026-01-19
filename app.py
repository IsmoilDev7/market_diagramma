import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Sotuv Diagramalari", layout="wide")
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
# 2. Ma'lumotlarni yuklash va tozalash
# ==========================
@st.cache_data
def load_data(sales_file, returns_file):
    sales = pd.read_excel(sales_file)
    returns = pd.read_excel(returns_file)

    # datetime va bo'sh qiymatlarni tuzatish
    sales['Период'] = pd.to_datetime(sales['Период'], errors='coerce')
    returns['Период'] = pd.to_datetime(returns['Период'], errors='coerce')
    sales = sales.dropna(subset=['Период'])
    returns = returns.dropna(subset=['Период'])

    # ustunlarni nomlash
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

    # numeric konvertatsiya
    sales['amount_sale'] = pd.to_numeric(sales['amount_sale'], errors='coerce').fillna(0)
    returns['amount_return'] = pd.to_numeric(returns['amount_return'], errors='coerce').fillna(0)

    return sales, returns

sales, returns = load_data(sales_file, returns_file)

# ==========================
# 3. Kunlik foyda / zarar
# ==========================
daily = sales.groupby('Период')['amount_sale'].sum().reset_index()
daily_returns = returns.groupby('Период')['amount_return'].sum().reset_index()
daily = daily.merge(daily_returns, on='Период', how='left').fillna(0)
daily['net_profit'] = daily['amount_sale'] - daily['amount_return']
daily['status'] = np.where(daily['net_profit'] > 0, 'FOYDA', 'ZARAR')

# ==========================
# 4. Klient kesimi
# ==========================
client_profit = sales.groupby('client')['amount_sale'].sum() - returns.groupby('client')['amount_return'].sum()
client_profit = client_profit.fillna(0).reset_index()
client_profit.columns = ['client', 'net_profit']
client_profit['status'] = np.where(client_profit['net_profit'] > 0, 'FOYDA', 'ZARAR')

# ==========================
# 5. Bar chart: Kunlik foyda / zarar
# ==========================
st.subheader("📅 Kunlik foyda / zarar (Bar chart)")
fig_daily = px.bar(
    daily,
    x='Период',
    y='net_profit',
    color='status',
    color_discrete_map={'FOYDA':'green', 'ZARAR':'red'},
    hover_data={'amount_sale': True, 'amount_return': True, 'net_profit': ':.2f'},
    labels={'Период':'Sana', 'net_profit':'Sof foyda'}
)
fig_daily.update_layout(barmode='group')
st.plotly_chart(fig_daily, use_container_width=True)
st.markdown("💡 Yashil → foyda, Qizil → zarar. Hover qilganda tafsilot ko‘rinadi.")

# ==========================
# 6. Bar chart: Klient kesimi
# ==========================
st.subheader("🧑‍💼 Klient kesimida sof foyda/zarar")
fig_client = px.bar(
    client_profit,
    x='client',
    y='net_profit',
    color='status',
    color_discrete_map={'FOYDA':'green', 'ZARAR':'red'},
    hover_data={'net_profit': ':.2f'},
    labels={'client':'Klient', 'net_profit':'Sof foyda'}
)
st.plotly_chart(fig_client, use_container_width=True)
st.markdown("💡 Yashil → foyda, Qizil → zarar. Hover qilganda net foyda ko‘rinadi.")

# ==========================
# 7. Individual klientlar filtri
# ==========================
st.subheader("👤 Individual klientlar tafsiloti")
selected_status = st.radio("Foyda yoki zarar klientlar", ['FOYDA','ZARAR'])
filtered_clients = client_profit[client_profit['status']==selected_status]

fig_client_individual = px.bar(
    filtered_clients,
    x='client',
    y='net_profit',
    color='net_profit',
    color_continuous_scale='RdYlGn',
    hover_data={'net_profit': ':.2f'},
    labels={'client':'Klient', 'net_profit':'Sof foyda'}
)
st.plotly_chart(fig_client_individual, use_container_width=True)
st.markdown("💡 Rang → sof foyda miqdori. Hover qilganda aniq qiymat ko‘rinadi.")
