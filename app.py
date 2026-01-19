import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Sotuv Treemap", layout="wide")
st.title("📊 Sotuv va Foyda Treemap Diagramalari (2025 Dekabr)")

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
# 3. Kunlik sof foyda
# ==========================
daily = sales.groupby('Период')['amount_sale'].sum().reset_index()
daily_returns = returns.groupby('Период')['amount_return'].sum().reset_index()
daily = daily.merge(daily_returns, on='Период', how='left').fillna(0)
daily['net_profit'] = daily['amount_sale'] - daily['amount_return']
daily['status'] = np.where(daily['net_profit']>0,'FOYDA','ZARAR')

# ==========================
# 4. Klient kesimi
# ==========================
client_profit = sales.groupby('client')['amount_sale'].sum() - returns.groupby('client')['amount_return'].sum()
client_profit = client_profit.fillna(0).reset_index()
client_profit.columns = ['client', 'net_profit']
client_profit['status'] = np.where(client_profit['net_profit']>0,'FOYDA','ZARAR')

# ==========================
# 5. Interaktiv filterlar
# ==========================
st.sidebar.subheader("📊 Diagramma filterlari")
diagram_type = st.sidebar.selectbox("Diagramma turi", ["Kunlik treemap", "Klient treemap"])
status_filter = st.sidebar.multiselect("Status filter", ["FOYDA", "ZARAR"], default=["FOYDA","ZARAR"])

# ==========================
# 6. Diagramma: Kunlik treemap
# ==========================
if diagram_type == "Kunlik treemap":
    df = daily[daily['status'].isin(status_filter)]
    if df.empty:
        st.warning("Tanlangan status uchun kunlik ma’lumot mavjud emas")
    else:
        fig = px.treemap(
            df,
            path=['status', 'Период'],
            values='net_profit',
            color='net_profit',
            color_continuous_scale='RdYlGn',
            hover_data={'amount_sale': True, 'amount_return': True, 'net_profit': ':.2f'},
            title="📅 Kunlik sof foyda/zarar treemap"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("💡 Rang yashil → foyda, qizil → zarar. Bosilganda kun darajasini ochadi.")

# ==========================
# 7. Diagramma: Klient treemap
# ==========================
if diagram_type == "Klient treemap":
    df = client_profit[client_profit['status'].isin(status_filter)]
    if df.empty:
        st.warning("Tanlangan status uchun klient ma’lumot mavjud emas")
    else:
        fig = px.treemap(
            df,
            path=['status','client'],
            values='net_profit',
            color='net_profit',
            color_continuous_scale='RdYlGn',
            hover_data={'net_profit': ':.2f'},
            title="🧑‍💼 Klientlar sof foyda/zarar treemap"
        )
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("💡 Rang yashil → foyda, qizil → zarar. Bosilganda klient tafsiloti ko‘rinadi.")
