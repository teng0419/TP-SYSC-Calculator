import streamlit as st
import numpy as np
import plotly.graph_objects as go
import math

# --- 頁面基本設定 ---
st.set_page_config(page_title="TP-SYSC計算機", layout="wide")

# ==========================================
# 注入自訂 CSS：精準控制字型，避開內建 Icon 亂碼
# ==========================================
st.markdown("""
<style>
    /* 只針對主要的文字容器設定字型，不要用 '*' */
    html, body, [data-testid="stSidebar"], .main {
        font-family: 'Calibri', sans-serif;
    }

    /* 針對標籤、段落等文字調整大小 */
    p, label, li, span, .stMarkdown {
        font-size: 18px !important;
    }

    /* 確保標題大小一致 */
    h1, h2, h3 {
        font-size: 20px !important;
        font-family: 'Calibri', sans-serif !important;
    }
    
    .check-box {
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

st.title("錐形變斷面耐震間柱 (TP-SYSC) 計算機")
st.markdown("作者：傻逼巴拉")

# ==========================================
# 內建資料庫 (CNS RH 型鋼)
# ==========================================
STEEL_DB = {
    "SN400B": {"Fy": 235, "Ry": 1.3, "Omega": 1.5},
    "SN490B": {"Fy": 325, "Ry": 1.2, "Omega": 1.3},
}

RH_DATA = {
    "294 X 302 X 12 X 12": (294, 302, 12, 12), "300 X 300 X 10 X 15": (300, 300, 10, 15),
    "300 X 305 X 15 X 15": (300, 305, 15, 15), "304 X 301 X 11 X 17": (304, 301, 11, 17),
    "312 X 303 X 13 X 21": (312, 303, 13, 21), "318 X 307 X 17 X 24": (318, 307, 17, 24),
    "326 X 310 X 20 X 28": (326, 310, 20, 28), "346 X 174 X 6 X 9": (346, 174, 6, 9),
    "350 X 175 X 7 X 11": (350, 175, 7, 11),   "336 X 249 X 8 X 12": (336, 249, 8, 12),
    "340 X 250 X 9 X 14": (340, 250, 9, 14),   "350 X 252 X 11 X 19": (350, 252, 11, 19),
    "356 X 256 X 15 X 22": (356, 256, 15, 22), "364 X 258 X 17 X 26": (364, 258, 17, 26),
    "338 X 351 X 13 X 13": (338, 351, 13, 13), "344 X 348 X 10 X 16": (344, 348, 10, 16),
    "344 X 354 X 16 X 16": (344, 354, 16, 16), "350 X 350 Theater": (350, 350, 12, 19),
    "350 X 350 X 12 X 19": (350, 350, 12, 19), "350 X 357 X 19 X 19": (350, 357, 19, 19),
    "360 X 354 X 16 X 24": (360, 354, 16, 24), "368 X 356 X 18 X 28": (368, 356, 18, 28),
    "378 X 358 X 20 X 33": (378, 358, 20, 33), "396 X 199 X 7 X 11": (396, 199, 7, 11),
    "400 X 200 X 8 X 13": (400, 200, 8, 13),   "386 X 299 X 9 X 14": (386, 299, 9, 14),
    "390 X 300 X 10 X 16": (390, 300, 10, 16), "400 X 304 X 14 X 21": (400, 304, 14, 21),
    "410 X 308 X 18 X 26": (410, 308, 18, 26), "418 X 310 X 20 X 30": (418, 310, 20, 30),
    "388 X 402 X 15 X 15": (388, 402, 15, 15), "394 X 398 X 11 X 18": (394, 398, 11, 18),
    "394 X 405 X 18 X 18": (394, 405, 18, 18), "400 X 400 X 13 X 21": (400, 400, 13, 21),
    "400 X 408 X 21 X 21": (400, 408, 21, 21), "414 X 405 X 18 X 28": (414, 405, 18, 28),
    "428 X 407 X 20 X 35": (428, 407, 20, 35), "458 X 417 X 30 X 50": (458, 417, 30, 50),
    "446 X 199 X 8 X 12": (446, 199, 8, 12),   "450 X 200 X 9 X 14": (450, 200, 9, 14),
    "456 X 201 X 10 X 17": (456, 201, 10, 17), "466 X 205 X 14 X 22": (466, 205, 14, 22),
    "478 X 208 X 17 X 28": (478, 208, 17, 28), "434 X 299 X 10 X 15": (434, 299, 10, 15),
    "440 X 300 X 11 X 18": (440, 300, 11, 18), "446 X 302 X 13 X 21": (446, 302, 13, 21),
    "450 X 304 X 15 X 23": (450, 304, 15, 23), "458 X 306 X 17 X 27": (458, 306, 17, 27),
    "468 X 308 X 19 X 32": (468, 308, 19, 32), "496 X 199 X 9 X 14": (496, 199, 9, 14),
    "500 X 200 X 10 X 16": (500, 200, 10, 16), "506 X 201 X 11 X 19": (506, 201, 11, 19),
    "512 X 202 X 12 X 22": (512, 202, 12, 22), "518 X 205 X 15 X 25": (518, 205, 15, 25),
    "528 X 208 X 18 X 30": (528, 208, 18, 30), "536 X 210 X 20 X 34": (536, 210, 20, 34),
    "548 X 215 X 25 X 40": (548, 215, 25, 40), "482 X 300 X 11 X 15": (482, 300, 11, 15),
    "488 X 300 X 11 X 18": (488, 300, 11, 18), "494 X 302 X 13 X 21": (494, 302, 13, 21),
    "500 X 304 X 15 X 24": (500, 304, 15, 24), "510 X 306 X 17 X 29": (510, 306, 17, 29),
    "518 X 310 X 21 X 33": (518, 310, 21, 33), "532 X 314 X 25 X 40": (532, 314, 25, 40),
    "596 X 199 X 10 X 15": (596, 199, 10, 15), "600 X 200 X 11 X 17": (600, 200, 11, 17),
    "606 X 201 X 12 X 20": (606, 201, 12, 20), "612 X 202 X 13 X 23": (612, 202, 13, 23),
    "618 X 205 X 16 X 26": (618, 205, 16, 26), "626 X 207 X 18 X 30": (626, 207, 18, 30),
    "634 X 209 X 20 X 34": (634, 209, 20, 34), "646 X 214 X 25 X 40": (646, 214, 25, 40),
    "582 X 300 X 12 X 17": (582, 300, 12, 17), "588 X 300 X 12 X 20": (588, 300, 12, 20),
    "594 X 302 X 14 X 23": (594, 302, 14, 23), "600 X 304 X 16 X 26": (600, 304, 16, 26),
    "608 X 306 X 18 X 30": (608, 306, 18, 30), "616 X 308 X 20 X 34": (616, 308, 20, 34),
    "628 X 312 X 24 X 40": (628, 312, 24, 40), "692 X 300 X 13 X 20": (692, 300, 13, 20),
    "700 X 300 X 13 X 24": (700, 300, 13, 24), "708 X 302 X 15 X 28": (708, 302, 15, 28),
    "712 X 306 X 19 X 30": (712, 306, 19, 30), "718 X 308 X 21 X 33": (718, 308, 21, 33),
    "732 X 311 X 24 X 40": (732, 311, 24, 40), "792 X 300 X 14 X 22": (792, 300, 14, 22),
    "800 X 300 X 14 X 26": (800, 300, 14, 26), "808 X 302 X 16 X 30": (808, 302, 16, 30),
    "816 X 306 X 20 X 34": (816, 306, 20, 34), "828 X 308 X 22 X 40": (828, 308, 22, 40)
}

# ==========================================
# 設計者輸入區
# ==========================================
st.sidebar.header("📝 設計輸入參數")

with st.sidebar.expander("耐震目標", expanded=True):
    target_drift = st.number_input("目標層間側移角θd(%rad)", min_value=1.0, max_value=5.0, value=2.5, step=0.5)

with st.sidebar.expander("材料性質", expanded=True):
    mat_ic_w = st.selectbox("核心段鋼材 (IC)", list(STEEL_DB.keys()), index=1)
    mat_ej_w = st.selectbox("連接段鋼材 (EJ)", list(STEEL_DB.keys()), index=1)
    mat_stiff = st.selectbox("加勁板鋼材", list(STEEL_DB.keys()), index=1)
    E_GPa = st.number_input("楊氏模數 E (GPa)", value=200.0, step=1.0)
    nu = 0.3
    
    Fy_IC = STEEL_DB[mat_ic_w]["Fy"]
    Ry_IC = STEEL_DB[mat_ic_w]["Ry"]
    Omega_IC = STEEL_DB[mat_ic_w]["Omega"]
    Fy_EJ = STEEL_DB[mat_ej_w]["Fy"]

with st.sidebar.expander("TP-SYSC 高度與角度設定", expanded=True):
    h_IC_mm = st.number_input("核心段高度 h_IC (mm)", value=800.0, step=1.0)
    h_EJ_mm = st.number_input("連接段高度 h_EJ (mm)", value=900.0, step=1.0, help="單邊EJ段高度")
    
    ic_profile = st.selectbox("選取 IC 段 RH 斷面", list(RH_DATA.keys()), index=list(RH_DATA.keys()).index("400 X 304 X 14 X 21"))
    d_IC, bf_IC, tw_IC, tf_IC = RH_DATA[ic_profile]

    ts_End = st.number_input("端部加勁板厚度 ts_End (mm)", value=float(tf_IC), step=1.0)
    
    h_SYSC_mm = (h_EJ_mm * 2) + h_IC_mm + (2 * ts_End)
    h_SYSC = h_SYSC_mm / 1000.0

    st.info(f"📐 計算所得間柱總高 $h_{{SYSC}}$: **{h_SYSC:.3f}** m")

    theta_deg = st.number_input("輸入錐形角度 θ (deg)", value=5.0, min_value=0.0, max_value=90.0, step=0.5)
    theta_sol = math.radians(theta_deg)

    tw_EJ_min_req = (Omega_IC * Ry_IC * Fy_IC * tw_IC) / Fy_EJ
    d_EJ0_min_req = (d_IC + h_EJ_mm * math.tan(theta_sol)) * math.cos(theta_sol)

    filtered_ej_options = []
    for name, (d_val, bf_val, tw_val, tf_val) in RH_DATA.items():
        is_width_match = abs(bf_val - bf_IC) <= 20
        is_geo_ok = d_val >= d_EJ0_min_req
        is_strength_ok = tw_val >= tw_EJ_min_req
        if is_width_match and is_geo_ok and is_strength_ok:
            filtered_ej_options.append(name)
    
    if not filtered_ej_options:
        filtered_ej_options = [name for name, (d_v, bf_v, tw_v, tf_v) in RH_DATA.items() if (abs(bf_v - bf_IC) <= 20 and d_v > d_IC)]
    
    ej_profile = st.selectbox(f"選取 EJ 段 RH 斷面 (共 {len(filtered_ej_options)} 個建議項目)", filtered_ej_options)
    d_EJ0, bf_EJ, tw_EJ, tf_EJ = RH_DATA[ej_profile]

with st.sidebar.expander("加勁板配置"):
    n_v = st.number_input("縱向加勁板數量 nL", min_value=0, value=0, step=1)
    n_h = st.number_input("橫向加勁板數量 nT", min_value=0, value=1, step=1)
    ts = st.number_input("加勁板厚度 ts (mm)", min_value=10.0, value=11.0, step=1.0)
    bs = st.number_input("加勁板寬度 bs (mm)", min_value=90.0, value=120.0, step=1.0)

with st.sidebar.expander("邊界構架尺寸"):
    d_c = st.number_input("邊界柱深度 dc (mm)", value=500.0, step=50.0)
    L_b = st.number_input("梁跨距 Lb (m)", value=6.0, step=0.1)
    mat_beam = st.selectbox("邊界梁鋼材", list(STEEL_DB.keys()), index=1)
    rh_beam = st.selectbox("選取邊界梁 RH 尺寸", list(RH_DATA.keys()), index=len(RH_DATA)-1)
    d_b, bf_b, tw_b, tf_b = RH_DATA[rh_beam]
    t_dp = st.number_input("交會區貼板厚度 t_dp (mm)", value=15.0, step=1.0)

# ==========================================
# 核心力學引擎
# ==========================================
Ry_EJ = STEEL_DB[mat_ej_w]["Ry"]
Fy_Stiff = STEEL_DB[mat_stiff]["Fy"]
Fy_beam = STEEL_DB[mat_beam]["Fy"]

E = E_GPa * 1000.0 
G = E / (2 * (1 + nu))
theta_d = target_drift / 100.0

d_EJ1 = d_IC
d_EJ2 = d_EJ1 + 2 * h_EJ_mm * math.tan(theta_sol)

def calc_props(d_val, bf_val, tw_val, tf_val):
    A = tf_val * bf_val * 2 + (d_val - 2 * tf_val) * tw_val
    Ix = 1/12 * (bf_val * d_val**3 - (bf_val - tw_val) * (d_val - 2 * tf_val)**3)
    Iy = 1/12 * (tf_val * bf_val**3 * 2 + (d_val - 2 * tf_val) * tw_val**3)
    Zx = bf_val * tf_val * (d_val - tf_val) + tw_val * (d_val / 2 - tf_val)**2
    Sx = Ix / (d_val / 2)
    ry = math.sqrt(Iy / A) if A > 0 else 0
    return A, Ix, Iy, Zx, Sx, ry

A_IC, Ix_IC, Iy_IC, Zx_IC, Sx_IC, ry_IC = calc_props(d_IC, bf_IC, tw_IC, tf_IC)
A_EJ1, Ix_EJ1, Iy_EJ1, Zx_EJ1, Sx_EJ1, ry_EJ1 = calc_props(d_EJ1, bf_EJ, tw_EJ, tf_EJ)
A_EJ2, Ix_EJ2, Iy_EJ2, Zx_EJ2, Sx_EJ2, ry_EJ2 = calc_props(d_EJ2, bf_EJ, tw_EJ, tf_EJ)

# 寬厚比限制
bf_ratio_limit = 0.38 * math.sqrt(E / (Ry_EJ * Fy_EJ))
EJ_ratio_limit = 2.61 * math.sqrt(E / (Ry_EJ * Fy_EJ))
Lmd_limit = 0.17 * ry_EJ1 * E / (Ry_EJ * Fy_EJ)

val_flange = bf_EJ / (2 * tf_EJ)
val_web = (d_EJ2 - 2 * tf_EJ) / tw_EJ
val_Lb = h_SYSC_mm

# 勁度
Ix_EJ_avg = (Ix_EJ1 + Ix_EJ2) / 2.0
d_EJ_avg = (d_EJ1 + d_EJ2) / 2.0
h_EJ_total = 2 * h_EJ_mm
K_EE = 1.0 / (h_EJ_total / (G * tw_EJ * d_EJ_avg) + (h_SYSC_mm**3 - h_IC_mm**3) / (12 * E * Ix_EJ_avg))
Ke_IC = 1.0 / (h_IC_mm / (G * tw_IC * d_IC) + h_IC_mm**3 / (12 * E * Ix_IC))
Kp_IC = 1.0 / (h_IC_mm / (0.02 * G * tw_IC * d_IC) + h_IC_mm**3 / (12 * E * Ix_IC))
Ke_F = 1.0 / (1.0 / Ke_IC + 1.0 / K_EE)
Kp_F = 1.0 / (1.0 / Kp_IC + 1.0 / K_EE)

theta_y = 0.6 * Fy_IC * tw_IC * d_IC / (Ke_F * h_SYSC_mm)
theta_ed = (Ke_F / K_EE) * theta_y + (Kp_F / K_EE) * (theta_d - theta_y)

# 強度檢核
Vn_IC = 0.6 * Fy_IC * tw_IC * d_IC
Vmax = Omega_IC * Ry_IC * Vn_IC 
Vn_EJ_design = 0.9 * (0.6 * Fy_EJ * tw_EJ * d_EJ1)

Zf_IC = bf_IC * tf_IC * (d_IC - tf_IC)
Mn_IC_design = 0.9 * (Ry_IC * Zf_IC * Fy_IC)

ho = d_EJ2 - tf_EJ
J = (2 * bf_EJ * tf_EJ**3 + (d_EJ2 - 2 * tf_EJ) * tw_EJ**3) / 3
Cw = Iy_EJ2 * ho**2 / 4
rts = math.sqrt(math.sqrt(Iy_EJ2 * Cw) / Sx_EJ2) if Sx_EJ2 > 0 else 0
Lp = 1.76 * ry_EJ1 * math.sqrt(E / Fy_EJ)
Lr = 1.95 * rts * E / (0.7 * Fy_EJ) * math.sqrt(J / (Sx_EJ2 * ho) + math.sqrt((J / (Sx_EJ2 * ho))**2 + 6.76 * (0.7 * Fy_EJ / E)**2))

if val_Lb <= Lp:
    M_EJ_nom = Zx_EJ2 * Fy_EJ
else:
    M_EJ_nom = 0.7 * Fy_EJ * Sx_EJ2 # 簡化保守
Mn_EJ_design = 0.9 * min(M_EJ_nom, Zx_EJ2 * Fy_EJ)

Mu_EJ_req = Vmax * h_SYSC_mm / 2
Mu_IC_req = Vmax * h_IC_mm / 2

dcr_V_EJ = Vmax / Vn_EJ_design
dcr_M_EJ = Mu_EJ_req / Mn_EJ_design
dcr_M_IC = Mu_IC_req / Mn_IC_design

# 加勁板
nL, nT = n_v, n_h
ds_val = (d_IC - 2 * tf_IC) / (nL + 1.0) if nL > 0 else (d_IC - 2 * tf_IC)
hs_val = h_IC_mm / (nT + 1.0) if nT > 0 else h_IC_mm
alpha_s = ds_val / hs_val
kc = (8.95 + 5.6 / (alpha_s**2)) if alpha_s >= 1.0 else (5.6 + 8.95 / (alpha_s**2))
lambda_nw = (hs_val / tw_IC) * math.sqrt(0.6 * Fy_Stiff / (kc * E))
rd = (h_SYSC_mm / h_IC_mm) * (theta_d - theta_ed)
hs_tw_limit = math.sqrt(8.5 * kc / (2 * rd - (0.6 * Fy_Stiff / G))) if (2 * rd - (0.6 * Fy_Stiff / G)) > 0 else 200.0

D_plate = E * tw_IC**3 / (12.0 * (1.0 - nu**2))
Is_stiff = ts * bs**3 / 3.0
rs_stiff = E * Is_stiff / (h_IC_mm * D_plate)
alpha_s_log = np.log10(alpha_s) if alpha_s > 0 else 0
rs_star = 152.7 * alpha_s_log**2 + 21.14 * alpha_s_log + 26.34
rs_ratio = rs_stiff / rs_star

# 邊界梁與需求計算
L_b_mm = L_b * 1000.0
Zx_beam = bf_b * tf_b * (d_b - tf_b) + tw_b * (d_b / 2 - tf_b)**2
Mp_beam = Zx_beam * Fy_beam
Vn_beam = 0.6 * Fy_beam * d_b * tw_b

# 修正：定義 V_ult 以避免 NameError
omega_beam = 1.1
V_ult = omega_beam * Ry_IC * Vn_IC

L_prime = (L_b_mm - d_EJ2 - d_c) / 2.0 
M_b2 = 1.1 * Mp_beam
M_b1 = (V_ult * (h_SYSC_mm / 2.0 + d_b / 2.0) - M_b2 * (d_EJ2 / (2.0 * L_prime))) / (1.0 + (d_EJ2 / (2.0 * L_prime)))
V_b = (M_b1 + M_b2) / L_prime
V_u_PZ = (V_ult * h_SYSC_mm / (d_EJ2 - tf_EJ)) - V_b
V_n_PZ = 0.6 * Fy_beam * d_b * (tw_b + t_dp)

# ==========================================
# 輸出詳細檢核 UI
# ==========================================
def detail_check(name, actual, limit, unit="", is_lower_bound=False):
    is_ok = actual >= limit if is_lower_bound else actual <= limit
    color = "#00E000" if is_ok else "#FF0000"
    symbol = "≥" if is_lower_bound else "≤"
    status = "OK!" if is_ok else "NG!"
    
    st.markdown(f"""
    <div class="check-box" style="border-left: 5px solid {color}; background-color: rgba(255,255,255,0.05);">
        <strong style="font-size: 1.1em;">{name}</strong><br>
        實際值: <code>{actual:.2f} {unit}</code> {symbol} 限制值: <code>{limit:.2f} {unit}</code> 
        &nbsp; &rarr; <span style="color:{color}; font-weight:bold;">{status}</span>
    </div>
    """, unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["⚙️ 韌性與容量檢核", "🛡️ 加勁板設計", "🏗️ 邊界梁與交會區", "📐 設計結果與示意圖"])

with tab1:
    st.subheader("1. 韌性檢核 (Ductility Checks)")
    st.info("確保斷面在塑性轉動下不會發生過早的局部或整體挫曲。")
    detail_check("翼板寬厚比 λf", val_flange, bf_ratio_limit)
    detail_check("EJ段腹板寬厚比 λw", val_web, EJ_ratio_limit)
    detail_check("未側撐長度 Lb", val_Lb, Lmd_limit, "mm")
    
    st.divider()
    st.subheader("2. 容量檢核 (Capacity Checks)")
    st.info("採容量設計原則，確保 EJ 段在核心段 IC 達到極限強度時仍保持彈性。")
    detail_check("EJ段剪力 (Vmax vs φVn)", Vmax/1000, Vn_EJ_design/1000, "kN")
    detail_check("EJ段彎矩 (Mu vs φMn)", Mu_EJ_req/1000000, Mn_EJ_design/1000000, "kNm")
    detail_check("IC段彎矩 (Mu vs φMn)", Mu_IC_req/1000000, Mn_IC_design/1000000, "kNm")

with tab2:
    st.subheader("3. 加勁板幾何與強度檢核")
    st.info("檢核子板塊在大幅剪力變形下的穩定性。")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**幾何範圍限制**")
        detail_check("標準化寬厚比 λnw", lambda_nw, 0.6)
        detail_check("標準化寬厚比 λnw (下限)", lambda_nw, 0.145, is_lower_bound=True)
    with col2:
        st.write("**勁度與厚度需求**")
        detail_check("加勁板厚度 ts", ts, max(0.75*tw_IC, 10.0), "mm", is_lower_bound=True)
        detail_check("最適加勁剛度比 rs/rs*", rs_ratio, 1.0, is_lower_bound=True)

with tab3:
    st.subheader("4. 邊界構架容量設計")
    st.info("根據核心段最大剪力 Vmax 推算梁端需求，確保塑鉸發生在間柱。")
    detail_check("邊界梁彎矩 DCR (Mb1/Mp)", M_b1/Mp_beam, 1.0)
    detail_check("邊界梁剪力 DCR (Vb/Vn)", V_b/Vn_beam, 1.0)
    detail_check("交會區剪力 DCR (Vu/Vn)", V_u_PZ/V_n_PZ, 1.0)

with tab4:
    st.subheader("📝 設計結果總覽 (Summary)")
    st.markdown(f"""
    - **IC 段斷面**: `{ic_profile}`
    - **EJ 段型鋼**: `{ej_profile}`
    - **錐形角度 θ**: `{theta_deg:.2f}°`
    - **EJ 端部深度 $d_{{EJ2}}$**: **{d_EJ2:.1f}** mm
    - **間柱總高度**: `{h_SYSC:.3f} m`
    """)
    
    # 繪製示意圖 (維持原配色)
    fig = go.Figure()
    c_flange_ic, c_flange_ej = "#FFFFFF", "#E0E0E0"
    c_web_ic, c_web_ej = "#FFF99E", "#7CB3FF"
    c_stiff, c_col = "#222222", "#444444"
    c_beam_web, c_beam_flange = "#444444", "#333333"
    c_pz_doubler, c_end_plate = "#777777", "#F28500"
    line_s = dict(color="white", width=0.0)

    x_L, x_R = -L_b*1000/2, L_b*1000/2
    y_ic_b = h_EJ_mm + ts_End
    y_ic_t = y_ic_b + h_IC_mm
    y_end_bot_s, y_end_bot_e = h_EJ_mm, y_ic_b
    y_end_top_s, y_end_top_e = y_ic_t, y_ic_t + ts_End
    
    # 1. 柱與梁
    fig.add_shape(type="rect", x0=x_L-d_c/2, x1=x_L+d_c/2, y0=-d_b, y1=h_SYSC_mm+d_b, fillcolor=c_col, opacity=0.3, line=line_s)
    fig.add_shape(type="rect", x0=x_R-d_c/2, x1=x_R+d_c/2, y0=-d_b, y1=h_SYSC_mm+d_b, fillcolor=c_col, opacity=0.3, line=line_s)
    def draw_boundary_beam(y_start, d_bm, tf_bm, is_top=False):
        y_f1_s = y_start + (d_bm if is_top else -d_bm)
        y_f1_e = y_f1_s + (tf_bm if not is_top else -tf_bm)
        fig.add_shape(type="rect", x0=x_L+d_c/2, x1=x_R-d_c/2, y0=y_f1_s, y1=y_f1_e, fillcolor=c_beam_flange, line=line_s)
        y_f2_s = y_start
        y_f2_e = y_f2_s + (-tf_bm if not is_top else tf_bm)
        fig.add_shape(type="rect", x0=x_L+d_c/2, x1=x_R-d_c/2, y0=y_f2_s, y1=y_f2_e, fillcolor=c_beam_flange, line=line_s)
        fig.add_shape(type="rect", x0=x_L+d_c/2, x1=x_R-d_c/2, y0=y_f1_e, y1=y_f2_e, fillcolor=c_beam_web, line=line_s)
    draw_boundary_beam(0, d_b, tf_b, is_top=False)
    draw_boundary_beam(h_SYSC_mm, d_b, tf_b, is_top=True)

    # 2. Panel Zone
    for x_p in [-d_EJ2/2, d_EJ2/2]:
        fig.add_shape(type="rect", x0=x_p-tf_EJ/2, x1=x_p+tf_EJ/2, y0=-d_b+tf_b, y1=-tf_b, fillcolor=c_flange_ej, line=dict(width=0))
        fig.add_shape(type="rect", x0=x_p-tf_EJ/2, x1=x_p+tf_EJ/2, y0=h_SYSC_mm+tf_b, y1=h_SYSC_mm+d_b-tf_b, fillcolor=c_flange_ej, line=dict(width=0))
    fig.add_shape(type="rect", x0=-d_EJ2/2+tf_EJ/2, x1=d_EJ2/2-tf_EJ/2, y0=-d_b+tf_b, y1=-tf_b, fillcolor=c_pz_doubler, line=dict(width=0))
    fig.add_shape(type="rect", x0=-d_EJ2/2+tf_EJ/2, x1=d_EJ2/2-tf_EJ/2, y0=h_SYSC_mm+tf_b, y1=h_SYSC_mm+d_b-tf_b, fillcolor=c_pz_doubler, line=dict(width=0))

    # 3. IC 段
    fig.add_shape(type="rect", x0=-d_IC/2, x1=-d_IC/2+tf_IC, y0=y_ic_b, y1=y_ic_t, fillcolor=c_flange_ic, line=line_s)
    fig.add_shape(type="rect", x0=d_IC/2-tf_IC, x1=d_IC/2, y0=y_ic_b, y1=y_ic_t, fillcolor=c_flange_ic, line=line_s)
    fig.add_shape(type="rect", x0=-d_IC/2+tf_IC, x1=d_IC/2-tf_IC, y0=y_ic_b, y1=y_ic_t, fillcolor=c_web_ic, line=line_s)
    hw_ic_net = d_IC - 2 * tf_IC
    if nT > 0:
        dy = h_IC_mm / (nT + 1)
        for i in range(1, int(nT) + 1):
            yc = y_ic_b + i * dy
            fig.add_shape(type="line", x0=-hw_ic_net/2, x1=hw_ic_net/2, y0=yc, y1=yc, line=dict(color=c_stiff, width=1.5))
    if nL > 0:
        dx = hw_ic_net / (nL + 1)
        for i in range(1, int(nL) + 1):
            xc = -hw_ic_net/2 + i * dx
            fig.add_shape(type="line", x0=xc, x1=xc, y0=y_ic_b, y1=y_ic_t, line=dict(color=c_stiff, width=1.5))

    # 4. 端部板
    w_end = d_IC + 20.0
    fig.add_shape(type="rect", x0=-w_end/2, x1=w_end/2, y0=y_end_bot_s, y1=y_end_bot_e, fillcolor=c_end_plate, line=line_s)
    fig.add_shape(type="rect", x0=-w_end/2, x1=w_end/2, y0=y_end_top_s, y1=y_end_top_e, fillcolor=c_end_plate, line=line_s)

    # 5. EJ 段
    def draw_ej_clean(ys, ye, ds, de, tfv, cw, flip=False):
        dsm, dlg = (de, ds) if flip else (ds, de)
        ysm, ylg = (ye, ys) if flip else (ys, ye)
        fig.add_trace(go.Scatter(mode='lines', x=[-dsm/2, -dsm/2+tfv, -dlg/2+tfv, -dlg/2, -dsm/2], y=[ysm, ysm, ylg, ylg, ysm], fill="toself", fillcolor=c_flange_ej, line=line_s, showlegend=False))
        fig.add_trace(go.Scatter(mode='lines', x=[dsm/2-tfv, dsm/2, dlg/2, dlg/2-tfv, dsm/2-tfv], y=[ysm, ysm, ylg, ylg, ysm], fill="toself", fillcolor=c_flange_ej, line=line_s, showlegend=False))
        fig.add_trace(go.Scatter(mode='lines', x=[-dsm/2+tfv, dsm/2-tfv, dlg/2-tfv, -dlg/2+tfv, -dsm/2+tfv], y=[ysm, ysm, ylg, ylg, ysm], fill="toself", fillcolor=cw, line=line_s, showlegend=False))
    draw_ej_clean(y_end_top_e, h_SYSC_mm, d_EJ1, d_EJ2, tf_EJ, c_web_ej, flip=False)
    draw_ej_clean(0, y_end_bot_s, d_EJ2, d_EJ1, tf_EJ, c_web_ej, flip=True)

    fig.update_layout(
        height=800, template="plotly_dark", 
        yaxis=dict(scaleanchor="x", scaleratio=1, showticklabels=False, showgrid=False, zeroline=False),
        xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        margin=dict(l=10,r=10,t=10,b=10)
    )
    st.plotly_chart(fig, use_container_width=True)
