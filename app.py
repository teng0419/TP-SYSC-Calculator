import streamlit as st
import numpy as np
import plotly.graph_objects as go
import math

# ==========================================
# UI 與數值輔助函式 (3位有效數字轉換)
# ==========================================
def to_sig_fig(val, sig_figs=3):
    if val == 0 or np.isnan(val) or np.isinf(val):
        return "0.00"
    try:
        val_abs = abs(float(val))
        # 計算數量級
        order = int(math.floor(math.log10(val_abs)))
        # 決定需要捨入到小數點後第幾位
        decimals = sig_figs - 1 - order
        rounded = round(val_abs, decimals)
        
        # 再次檢查進位後的位數 (例如 9.99 捨入後變成 10.0，數量級會進位)
        new_order = int(math.floor(math.log10(rounded))) if rounded != 0 else 0
        if new_order > order:
            decimals = sig_figs - 1 - new_order
            
        if decimals <= 0:
            result = str(int(round(rounded, 0)))
        else:
            fmt = f"{{:.{decimals}f}}"
            result = fmt.format(rounded)
        return "-" + result if val < 0 else result
    except:
        return str(val)

def format_dcr(x):
    return to_sig_fig(x)

def check_item(name, val_str, is_ok):
    color = "#00E000" if is_ok else "#FF0000"
    status = "OK!" if is_ok else "NG!"
    return f"- **{name}**: {val_str} &rarr; <span style='color:{color}; font-weight:bold;'>{status}</span>"

def detail_check(name, actual, limit, unit="", is_lower_bound=False, highlight=False, note=""):
    is_ok = actual >= limit if is_lower_bound else actual <= limit
    color = "#00E000" if is_ok else "#FF0000"
    symbol = "≥" if is_lower_bound else "≤"
    status = "OK!" if is_ok else "NG!"
    bg_style = "background-color: rgba(255, 255, 0, 0.15);" if highlight else "background-color: rgba(255,255,255,0.05);"
    
    # 全面套用 3 位有效數字
    val_disp = to_sig_fig(actual) if isinstance(actual, (float, int, np.floating, np.integer)) else str(actual)
    limit_disp = to_sig_fig(limit) if isinstance(limit, (float, int, np.floating, np.integer)) else str(limit)

    # 檢核框主體 (HTML)
    st.markdown(f"""
    <div class="check-box" style="border-left: 5px solid {color}; {bg_style} margin-bottom: 2px;">
        <div style="display: flex; justify-content: space-between;">
            <strong style="font-size: 1.1em;">{name}</strong>
            <span style="color:{color}; font-weight:bold;">{status}</span>
        </div>
        實際值: <code>{val_disp} {unit}</code> {symbol} 
        限制值: <code>{limit_disp} {unit}</code>
    </div>
    """, unsafe_allow_html=True)
    
    # 將公式移出 HTML 區塊外，交由 Streamlit 內建的 Markdown 引擎正確解析 LaTeX
    if note:
        st.markdown(f"↳ ${note}$")

# --- 頁面基本設定 ---
st.set_page_config(page_title="TP-SYSC計算機", layout="wide")

# ==========================================
# 注入自訂 CSS：精準控制字型，優化表格與檢核框
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
        padding: 12px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    code {
        color: #FFD700 !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title("錐形變斷面耐震間柱 (TP-SYSC) 計算機")
st.markdown("依據 2025《結構工程學刊》TVSC 設計準則優化 | 作者：傻逼巴拉")

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
    target_drift = st.number_input("目標層間側移角 θd (%rad)", min_value=1.0, max_value=5.0, value=3.0, step=0.5)

with st.sidebar.expander("材料性質", expanded=True):
    mat_ic_w = st.selectbox("核心段腹板鋼材 (IC Web)", list(STEEL_DB.keys()), index=1)
    mat_ej_w = st.selectbox("連接段與翼板鋼材 (EJ & Flange)", list(STEEL_DB.keys()), index=1)
    mat_stiff = st.selectbox("加勁板鋼材", list(STEEL_DB.keys()), index=1)
    E_GPa = st.number_input("楊氏模數 E (GPa)", value=200.0, step=1.0)
    nu = 0.3
    
    Fy_IC = STEEL_DB[mat_ic_w]["Fy"]
    Ry_IC = STEEL_DB[mat_ic_w]["Ry"]
    Omega_IC = STEEL_DB[mat_ic_w]["Omega"]
    Fy_EJ = STEEL_DB[mat_ej_w]["Fy"]
    Ry_EJ = STEEL_DB[mat_ej_w]["Ry"]

with st.sidebar.expander("TP-SYSC 高度與角度設定", expanded=True):
    h_SYSC_mm = st.number_input("間柱總高度 h_SYSC (mm)", value=2600.0, step=10.0)
    h_IC_mm = st.number_input("核心段高度 h_IC (mm)", value=750.0, step=1.0)
    
    ic_profile = st.selectbox("選取 IC 段核心斷面", list(RH_DATA.keys()), index=list(RH_DATA.keys()).index("488 X 300 X 11 X 18"))
    d_IC, bf_IC, tw_IC, tf_IC = RH_DATA[ic_profile]

    ts_End = st.number_input("端部板厚度 ts_End (mm)", value=float(tf_IC), step=1.0)
    
    # 改為由 h_SYSC 反推計算 h_EJ
    h_EJ_mm = (h_SYSC_mm - h_IC_mm - 2 * ts_End) / 2.0
    h_SYSC = h_SYSC_mm / 1000.0
    st.info(f"📐 計算所得單邊連接段高度 $h_{{EJ}}$: **{to_sig_fig(h_EJ_mm)}** mm")

    theta_deg = st.number_input("輸入錐形角度 θ (deg)", value=8.5, min_value=0.0, max_value=90.0, step=0.1)
    theta_sol = math.radians(theta_deg)

    # 根據輸入的 theta 篩選 EJ (優化篩選邏輯，給予 2mm 標稱容差確保標準型鋼不被濾掉)
    d_EJ0_min_req = (d_IC + h_EJ_mm * math.tan(theta_sol)) * math.cos(theta_sol)
    filtered_ej_options = [name for name, (d_v, bf_v, tw_v, tf_v) in RH_DATA.items() if (abs(bf_v - bf_IC) <= 20 and d_v >= d_EJ0_min_req - 2.0)]
    if not filtered_ej_options: filtered_ej_options = list(RH_DATA.keys())
    
    # 嘗試將預設 EJ 型鋼設為 616 X 308 X 20 X 34
    try:
        default_ej_idx = filtered_ej_options.index("616 X 308 X 20 X 34")
    except ValueError:
        default_ej_idx = 0
        
    ej_profile = st.selectbox("選取 EJ 段型鋼斷面", filtered_ej_options, index=default_ej_idx)
    d_EJ0, bf_EJ, tw_EJ, tf_EJ = RH_DATA[ej_profile]

with st.sidebar.expander("加勁板配置"):
    n_v = st.number_input("縱向加勁板數量 nL", min_value=0, value=1, step=1)
    n_h = st.number_input("橫向加勁板數量 nT", min_value=0, value=2, step=1)
    ts = st.number_input("加勁板厚度 ts (mm)", min_value=6.0, value=11.0, step=1.0)
    bs = st.number_input("加勁板寬度 bs (mm)", min_value=50.0, value=99.0, step=1.0)

with st.sidebar.expander("邊界構架尺寸"):
    d_c = st.number_input("邊界柱深度 dc (mm)", value=500.0, step=50.0)
    L_b = st.number_input("梁跨距 Lb (m)", value=6.0, step=0.1)
    mat_beam = st.selectbox("邊界梁鋼材", list(STEEL_DB.keys()), index=1)
    rh_beam = st.selectbox("選取邊界梁 RH 尺寸", list(RH_DATA.keys()), index=len(RH_DATA)-1)
    d_b, bf_b, tw_b, tf_b = RH_DATA[rh_beam]
    t_dp = st.number_input("交會區貼板厚度 t_dp (mm)", value=15.0, step=1.0)

# ==========================================
# 核心力學引擎 (修正：串聯柔度法 + 精確積分)
# ==========================================
E = E_GPa * 1000.0; nu = 0.3; G = E / (2 * (1 + nu))
theta_d = target_drift / 100.0

d_EJ1 = d_IC
d_EJ2 = d_EJ1 + 2 * h_EJ_mm * math.tan(theta_sol)

# 1. 核心段性質與柔度 (f_IC)
Ix_IC = (bf_IC * d_IC**3 - (bf_IC - tw_IC) * (d_IC - 2 * tf_IC)**3) / 12.0
Av_IC = d_IC * tw_IC
f_IC = h_IC_mm / (G * Av_IC) + h_IC_mm**3 / (12.0 * E * Ix_IC)

# 2. 連接段斷面性質 (EJ1 & EJ2)
I_EJ1 = (bf_EJ * d_EJ1**3 - (bf_EJ - tw_EJ) * (d_EJ1 - 2 * tf_EJ)**3) / 12.0
I_EJ2 = (bf_EJ * d_EJ2**3 - (bf_EJ - tw_EJ) * (d_EJ2 - 2 * tf_EJ)**3) / 12.0
Av_EJ1 = d_EJ1 * tw_EJ
Av_EJ2 = d_EJ2 * tw_EJ

# 3. EJ 等效性質轉換 (積分精確解)
# 等效剪力面積
Av_eq_EJ = (Av_EJ2 - Av_EJ1) / math.log(Av_EJ2 / Av_EJ1) if abs(Av_EJ2 - Av_EJ1) > 1e-5 else Av_EJ1

# 等效慣性矩輔助參數
b = math.sqrt(I_EJ1)
a = math.sqrt(I_EJ2)
alpha_user = 0.5 * h_IC_mm / (h_EJ_mm + ts_End)

# I_eq_EJ 分母兩項計算 (修正變數名為 a, b)
den_part1 = (alpha_user**2) / (a * b)
den_part2 = (1.0 + b/a + (2.0*b/(b-a)) * math.log(a/b)) / (b - a)**2 if abs(b-a) > 1e-5 else (1.0 / I_EJ1)

I_eq_EJ = (alpha_user**2 + 1.0/3.0) / (den_part1 + den_part2)

# 4. 連接段總柔度 (f_EJ，包含上下兩段)
eta = h_IC_mm / h_SYSC_mm
f_EJ_shear = ((1.0 - eta) * h_SYSC_mm) / (G * Av_eq_EJ)
f_EJ_flex = (h_SYSC_mm**3 - h_IC_mm**3) / (12.0 * E * I_eq_EJ)
f_EJ = f_EJ_shear + f_EJ_flex
f_total = f_IC + f_EJ

# 5. 系統總勁度 (K_eff)
# 整體側向勁度組合計算 (IC 與 兩段 EJ 串聯)
K_EE = 1.0 / (2.0 * f_EJ) # 系統中兩段 EJ 串聯對應之勁度
Ke_IC = 1.0 / (h_IC_mm / (G * tw_IC * d_IC) + h_IC_mm**3 / (12 * E * Ix_IC))
Kp_IC = 1.0 / (h_IC_mm / (0.02 * G * tw_IC * d_IC) + h_IC_mm**3 / (12 * E * Ix_IC))
Ke_F = 1.0 / f_total # 整體初始彈性側向勁度
Kp_F = 1.0 / (1.0 / Kp_IC + 1.0 / K_EE) # 整體降伏後側向勁度

theta_y = 0.6 * Fy_IC * tw_IC * d_IC / (Ke_F * h_SYSC_mm)
theta_ed = (Ke_F / K_EE) * theta_y + (Kp_F / K_EE) * (theta_d - theta_y)

# 強度與極限值
Vn_IC = 0.6 * Fy_IC * tw_IC * d_IC
Vmax = Omega_IC * Ry_IC * Vn_IC 

# 1. 韌性檢核標準
bf_ratio_limit = 0.38 * math.sqrt(E / (Ry_EJ * Fy_EJ))
EJ_ratio_limit = 2.61 * math.sqrt(E / (Ry_EJ * Fy_EJ))

# 2. LTB 放寬標準
Iy_EJ2 = 1/12 * (tf_EJ * bf_EJ**3 * 2 + (d_EJ2 - 2 * tf_EJ) * tw_EJ**3)
A_EJ2 = tf_EJ * bf_EJ * 2 + (d_EJ2 - 2 * tf_EJ) * tw_EJ
ry_EJ2 = math.sqrt(Iy_EJ2 / A_EJ2)
ho = d_EJ2 - tf_EJ
J = (2 * bf_EJ * tf_EJ**3 + (d_EJ2 - 2 * tf_EJ) * tw_EJ**3) / 3
Cw = Iy_EJ2 * ho**2 / 4
Sx_EJ2 = (1/12 * (bf_EJ * d_EJ2**3 - (bf_EJ - tw_EJ) * (d_EJ2 - 2 * tf_EJ)**3)) / (d_EJ2/2)
rts = math.sqrt(math.sqrt(Iy_EJ2 * Cw) / Sx_EJ2) if Sx_EJ2 > 0 else 0
Lr_limit = 1.95 * rts * E / (0.7 * Fy_EJ) * math.sqrt(J / (Sx_EJ2 * ho) + math.sqrt((J / (Sx_EJ2 * ho))**2 + 6.76 * (0.7 * Fy_EJ / E)**2))

# 3. 容量設計 (EJ 段與 IC 翼板)
Vn_EJ_design = 0.9 * (0.6 * Fy_EJ * tw_EJ * d_EJ1)
Zf_IC = bf_IC * tf_IC * (d_IC - tf_IC)
Mn_IC_design = 0.9 * (Ry_IC * Zf_IC * Fy_IC)
Zx_EJ2 = bf_EJ * tf_EJ * (d_EJ2 - tf_EJ) + tw_EJ * (d_EJ2 / 2 - tf_EJ)**2
Mn_EJ_design = 0.9 * (Zx_EJ2 * Fy_EJ)

# 4. 加勁板詳細參數
gamma_d = (h_SYSC_mm / h_IC_mm) * (theta_d - theta_ed)
gamma_y = (0.6 * Fy_IC) / G
nL, nT = n_v, n_h
ds_val = (d_IC - 2 * tf_IC) / (nL + 1.0) if nL > 0 else (d_IC - 2 * tf_IC)
hs_val = h_IC_mm / (nT + 1.0) if nT > 0 else h_IC_mm
alpha_s = ds_val / hs_val
kc = (8.95 + 5.6 / (alpha_s**2)) if alpha_s >= 1.0 else (5.6 + 8.95 / (alpha_s**2))
lambda_nw = (hs_val / tw_IC) * math.sqrt(0.6 * Fy_IC / (kc * E))
hs_tw_limit = math.sqrt(8.5 * kc / (2 * gamma_d - gamma_y)) if (2 * gamma_d - gamma_y) > 0 else 200.0

# 加勁剛度比需求
rs_star_threshold = 2.0 if gamma_d > 0.12 else 1.0
D_plate = E * tw_IC**3 / (12.0 * (1.0 - nu**2))
Is_stiff = ts * bs**3 / 3.0
rs_stiff = E * Is_stiff / (h_IC_mm * D_plate)
alpha_s_log = np.log10(alpha_s) if alpha_s > 0 else 0
rs_star = 152.7 * alpha_s_log**2 + 21.14 * alpha_s_log + 26.34
rs_ratio = rs_stiff / rs_star

# 根據配置逆推最大剪應變需求 gamma_u
gamma_u = 0.5 * (8.5 * kc / ((hs_val / tw_IC) ** 2) + gamma_y)

# 邊界構架計算 
L_b_mm = L_b * 1000.0
Zx_beam = bf_b * tf_b * (d_b - tf_b) + tw_b * (d_b / 2 - tf_b)**2
Mp_beam = Zx_beam * Fy_beam
Vn_beam = 0.6 * Fy_beam * d_b * tw_b

omega_beam = 1.1
V_ult = omega_beam * Ry_IC * Vn_IC
L_prime = (L_b_mm - d_EJ2 - d_c) / 2.0 
M_b2 = 1.1 * Mp_beam
M_b1 = (V_ult * (h_SYSC_mm / 2.0 + d_b / 2.0) - M_b2 * (d_EJ2 / (2.0 * L_prime))) / (1.0 + (d_EJ2 / (2.0 * L_prime)))
V_b = (M_b1 + M_b2) / L_prime
V_u_PZ = (V_ult * h_SYSC_mm / (d_EJ2 - tf_EJ)) - V_b
V_n_PZ = 0.6 * Fy_beam * d_b * (tw_b + t_dp)

dcr_beam_M = M_b1 / Mp_beam
dcr_beam_V = V_b / Vn_beam
dcr_PZ = V_u_PZ / V_n_PZ

# ==========================================
# 用鋼量與 KWR 計算 (kg)
# ==========================================
# 鋼材密度 (kg/mm^3)
rho_steel = 7.85e-6

# 1. IC段重量
A_IC_exact = 2 * bf_IC * tf_IC + (d_IC - 2 * tf_IC) * tw_IC
W_IC = A_IC_exact * h_IC_mm * rho_steel

# 2. EJ段重量 (上下兩段)
A_EJ_avg = 2 * bf_EJ * tf_EJ + ((d_EJ1 + d_EJ2) / 2.0 - 2 * tf_EJ) * tw_EJ
W_EJ = 2 * A_EJ_avg * h_EJ_mm * rho_steel

# 3. 端部板重量 (上下兩塊)
W_ES = 2 * ((d_IC + 20.0) * max(bf_IC, bf_EJ) * ts_End) * rho_steel

# 4. 加勁板重量
W_stiff_T = (2 * nT * (d_IC - 2 * tf_IC) * bs * ts) * rho_steel
W_stiff_L = (2 * nL * h_IC_mm * bs * ts) * rho_steel
W_stiff = W_stiff_T + W_stiff_L

# 總重量
W_total = W_IC + W_EJ + W_ES + W_stiff

# 計算 KWR 勁度重量比
K_eff_kN_mm = Ke_F / 1000.0
KWR = K_eff_kN_mm / W_total


# ==========================================
# 輸出分頁
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs(["⚙️ 韌性設計與容量設計", "🛡️ 加勁板設計", "🏗️ 邊界梁與交會區容量設計", "📐 設計結果與示意圖"])

with tab1:
    st.subheader("1. 韌性檢核 (Ductility Design)")
    detail_check("翼板寬厚比 λf", bf_EJ/(2*tf_EJ), bf_ratio_limit, note=r"\lambda_{f,md} = 0.38\sqrt{E / R_y F_y}")
    detail_check("EJ 腹板寬厚比 λw", (d_EJ2-2*tf_EJ)/tw_EJ, EJ_ratio_limit, note=r"\lambda_{w,md} = 2.61\sqrt{E / R_y F_y}")
    detail_check("未側撐長度 Lb (放寬)", h_SYSC_mm, Lr_limit, "mm", note=r"L_r = 1.95 r_{ts} \frac{E}{0.7F_y} \sqrt{\frac{Jc}{S_x h_o} + \dots}")
    
    st.divider()
    st.subheader("2. 容量設計 (Capacity Design)")
    detail_check("EJ 剪力需求 (Vmax vs φVn)", Vmax/1000, Vn_EJ_design/1000, "kN", note=r"\phi V_{n,EJ} = 0.9(0.6 F_y t_{w,EJ} d_{EJ1})")
    detail_check("EJ 段彎矩需求 (Mu vs φMn)", (Vmax*h_SYSC_mm/2)/1e6, Mn_EJ_design/1e6, "kNm", note=r"M_u = V_{max}h_{TVSC}/2 \le \phi M_{n,EJ}")

with tab2:
    st.subheader("3. 加勁板詳細檢核")
    st.info(f"核心段目標剪應變 γd: **{to_sig_fig(gamma_d * 100)}** %rad")
    st.markdown(r"↳ $\gamma_d = \frac{h_{TVSC}}{h_{IC}}(\theta_d - \theta_{e,d})$")
    detail_check("子板塊寬厚比 hs/tw", hs_val/tw_IC, hs_tw_limit, note=r"h_s/t_w \le \sqrt{8.5k_c / (2\gamma_d - \gamma_y)}")
    detail_check("標準化寬厚比 λnw (上限)", lambda_nw, 0.6, note=r"\lambda_{nw} = \frac{h_s}{t_w}\sqrt{\frac{0.6F_y}{k_c E}} \le 0.6")
    detail_check("標準化寬厚比 λnw (下限)", lambda_nw, 0.145, is_lower_bound=True, note=r"\lambda_{nw} \ge 0.145")
    detail_check("加勁剛度比 rs/rs*", rs_ratio, rs_star_threshold, is_lower_bound=True, note=r"\gamma_s / \gamma_s^* \ge " + str(to_sig_fig(rs_star_threshold)))
    
    st.markdown(f"推算最大剪應變容量 $\gamma_u$: **{to_sig_fig(gamma_u * 100)}** %rad (依據目前加勁板配置)")
    st.markdown(r"↳ $\gamma_u = 0.5\left(\frac{8.5k_c}{(h_s/t_w)^2} + \gamma_y\right)$")

with tab3:
    st.subheader("4. 邊界梁與交會區容量設計")
    detail_check("邊界梁彎矩 DCR (Mb1/Mp)", M_b1/Mp_beam, 1.0, note=r"M_{b1} = \frac{V_{ult}(h_{TVSC}/2 + d_b/2) - M_{b2}(d_{EJ2}/2L')}{1 + d_{EJ2}/2L'}")
    detail_check("邊界梁剪力 DCR (Vb/Vn)", V_b/Vn_beam, 1.0, note=r"V_b = \frac{M_{b1} + M_{b2}}{L'}")
    detail_check("交會區剪力 DCR (Vu/Vn)", V_u_PZ/V_n_PZ, 1.0, note=r"V_{u,PZ} = \frac{V_{ult} h_{TVSC}}{d_{EJ2} - t_f} - V_b")

with tab4:
    # --- 整合彙整 ---
    st.subheader("📊 完整檢核流程彙整")
    
    with st.expander("🔍 查看詳細計算數據", expanded=True):
        col_l, col_r = st.columns(2)
        with col_l:
            detail_check("翼板寬厚比 λf", bf_EJ/(2*tf_EJ), bf_ratio_limit, note=r"\lambda_{f,md} = 0.38\sqrt{E / R_y F_y}")
            detail_check("EJ 腹板寬厚比 λw", (d_EJ2-2*tf_EJ)/tw_EJ, EJ_ratio_limit, note=r"\lambda_{w,md} = 2.61\sqrt{E / R_y F_y}")
            detail_check("未側撐 Lb", h_SYSC_mm, Lr_limit, "mm", note=r"L_r = 1.95 r_{ts} \frac{E}{0.7F_y} \sqrt{\dots}")
            detail_check("EJ 剪力需求", Vmax/1000, Vn_EJ_design/1000, "kN", note=r"\phi V_{n,EJ} = 0.9(0.6 F_y t_{w,EJ} d_{EJ1})")
        with col_r:
            detail_check("加勁板 hs/tw", hs_val/tw_IC, hs_tw_limit, note=r"h_s/t_w \le \sqrt{8.5k_c / (2\gamma_d - \gamma_y)}")
            detail_check("加勁剛度比 rs/rs*", rs_ratio, rs_star_threshold, is_lower_bound=True, note=r"\gamma_s / \gamma_s^* \ge " + str(to_sig_fig(rs_star_threshold)))
            detail_check("邊界梁彎矩 DCR", M_b1/Mp_beam, 1.0, note=r"M_{b1} = \dots")
            detail_check("交會區剪力 DCR", V_u_PZ/V_n_PZ, 1.0, note=r"V_{u,PZ} = \dots")

   # --- 勁度參數驗算面板 (修正處) ---
    with st.expander("🛠️ 勁度參數驗算輸出 (用於手算核對)", expanded=False):
        st.markdown(f"""
        **1. 基本材料常數**
        * $E = {E:.2f}$ MPa, $G = {G:.2f}$ MPa

        **2. EJ 段參數 (單邊)**
        * 幾何比例: $L = {L_half:.2f}$ mm, $\eta = {eta:.6f}$, $L_0 = {L0:.2f}$ mm
        * 原始慣性矩: $I_{{EJ1}} = {I_EJ1:.2f}$, $I_{{EJ2}} = {I_EJ2:.2f}$
        * 微積分參數: $a = {a:.2f}$, $b = {b:.2f}$
        * 微積分精確解: $I_{{int}} = {I_int:.6e}$ mm$^{{-1}}$
        * 彎矩梯度係數: $\alpha = {alpha_user:.6f}$
        * 等效慣性矩: $I_{{eq,EJ}} = {I_eq_EJ:.2f}$
        * 柔度分析: $Term_1 = {term1_shear:.8e}$, $Term_2 = {term2_flex:.8e}$
        * 單邊 EJ 總柔度: $f_{{EJ}} = {f_EJ:.8e}$ mm/N
        * 兩段 EJ 總勁度 (串聯): $K_{{EE}} = {K_EE:.2f}$ N/mm

        **3. 系統整體勁度 (N/mm)**
        * 核心段勁度 $K_{{e,IC}} = {Ke_IC:.2f}$
        * 整體彈性勁度 $K_{{eff}} = {Ke_F:.2f}$ (或 **{K_eff_kN_mm:.6f}** kN/mm)
        """)

    st.divider()
    st.subheader("📝 設計總覽 (Summary)")
    st.markdown(f"""
    - **IC 核心段斷面**: `{ic_profile}` (SN490B)
    - **EJ 連接段型鋼**: `{ej_profile}` (SN490B)
    - **EJ 端深度 $d_{{EJ2}}$**: **{to_sig_fig(d_EJ2)}** mm
    - **推算最大剪應變 $\gamma_u$**: **{to_sig_fig(gamma_u * 100)}** %rad
    - **極限設計剪力 $V_{{max}}$**: **{to_sig_fig(Vmax/1000)}** kN (考慮材料超強與應變硬化)
    - **TP-SYSC 彈性側向勁度 $K_{{eff}}$**: **{K_eff_kN_mm:.6f}** kN/mm
    - **總用鋼量**: **{to_sig_fig(W_total)}** kg (包含 IC, EJ, 端部板及加勁板)
    - **勁度重量比 KWR**: **{to_sig_fig(KWR)}**
    """)

    # 示意圖 (高對比度專屬配色 - 同構件同色系)
    fig = go.Figure()
    c_flange_ic = "#FF9F0A"  # 橘黃色 (IC 翼板)
    c_web_ic = "#FFD60A"     # 亮黃色 (IC 腹板)
    c_flange_ej = "#0A84FF"  # 深藍色 (EJ 翼板)
    c_web_ej = "#5AC8FA"     # 亮藍色 (EJ 腹板)
    c_stiff = "#32D74B"      # 螢光綠 (加勁板)
    c_end_plate = "#BF5AF2"  # 亮紫色 (端部板)
    c_beam_web = "#636366"   # 灰色 (梁腹板)
    c_beam_flange = "#48484A"# 深灰色 (梁翼板)
    c_pz_doubler = "#8E8E93" # 亮灰色 (交會區貼板)
    c_col = "#2C2C2E"        # 背景柱深灰
    line_s = dict(color="white", width=0.0)

    x_L, x_R = -L_b*1000/2, L_b*1000/2
    y_end_bot_s = h_EJ_mm
    y_end_bot_e = y_end_bot_s + ts_End
    y_ic_b = y_end_bot_e
    y_ic_t = y_ic_b + h_IC_mm
    y_end_top_s = y_ic_t
    y_end_top_e = y_end_top_s + ts_End
    
    # 繪製邊界柱與梁
    fig.add_shape(type="rect", x0=x_L-d_c/2, x1=x_L+d_c/2, y0=-d_b, y1=h_SYSC_mm+d_b, fillcolor=c_col, opacity=0.3, line=line_s)
    fig.add_shape(type="rect", x0=x_R-d_c/2, x1=x_R+d_c/2, y0=-d_b, y1=h_SYSC_mm+d_b, fillcolor=c_col, opacity=0.3, line=line_s)
    def draw_beam(y_start, d_bm, tf_bm, is_top=False):
        y_f1_s = y_start + (d_bm if is_top else -d_bm)
        y_f1_e = y_f1_s + (tf_bm if not is_top else -tf_bm)
        fig.add_shape(type="rect", x0=x_L+d_c/2, x1=x_R-d_c/2, y0=y_f1_s, y1=y_f1_e, fillcolor=c_beam_flange, line=line_s)
        y_f2_s = y_start
        y_f2_e = y_f2_s + (-tf_bm if not is_top else tf_bm)
        fig.add_shape(type="rect", x0=x_L+d_c/2, x1=x_R-d_c/2, y0=y_f2_s, y1=y_f2_e, fillcolor=c_beam_flange, line=line_s)
        fig.add_shape(type="rect", x0=x_L+d_c/2, x1=x_R-d_c/2, y0=y_f1_e, y1=y_f2_e, fillcolor=c_beam_web, line=line_s)
    draw_beam(0, d_b, tf_b, is_top=False)
    draw_beam(h_SYSC_mm, d_b, tf_b, is_top=True)

    # 繪製 Panel Zone 交會區加勁板
    for x_p in [-d_EJ2/2, d_EJ2/2]:
        # EJ 延伸入梁的翼板
        fig.add_shape(type="rect", x0=x_p-tf_EJ/2, x1=x_p+tf_EJ/2, y0=-d_b+tf_b, y1=-tf_b, fillcolor=c_flange_ej, line=dict(width=0))
        fig.add_shape(type="rect", x0=x_p-tf_EJ/2, x1=x_p+tf_EJ/2, y0=h_SYSC_mm+tf_b, y1=h_SYSC_mm+d_b-tf_b, fillcolor=c_flange_ej, line=dict(width=0))
    
    # 兩側的交會區貼板 (Doubler Plate)
    fig.add_shape(type="rect", x0=-d_EJ2/2+tf_EJ/2, x1=d_EJ2/2-tf_EJ/2, y0=-d_b+tf_b, y1=-tf_b, fillcolor=c_pz_doubler, line=dict(width=0))
    fig.add_shape(type="rect", x0=-d_EJ2/2+tf_EJ/2, x1=d_EJ2/2-tf_EJ/2, y0=h_SYSC_mm+tf_b, y1=h_SYSC_mm+d_b-tf_b, fillcolor=c_pz_doubler, line=dict(width=0))

    # 繪製 EJ 段
    def draw_ej(ys, ye, ds, de, tfv, cw, flip=False):
        dsm, dlg = (de, ds) if flip else (ds, de)
        ysm, ylg = (ye, ys) if flip else (ys, ye)
        fig.add_trace(go.Scatter(mode='lines', x=[-dsm/2, -dsm/2+tfv, -dlg/2+tfv, -dlg/2, -dsm/2], y=[ysm, ysm, ylg, ylg, ysm], fill="toself", fillcolor=c_flange_ej, line=line_s, showlegend=False))
        fig.add_trace(go.Scatter(mode='lines', x=[dsm/2-tfv, dsm/2, dlg/2, dlg/2-tfv, dsm/2-tfv], y=[ysm, ysm, ylg, ylg, ysm], fill="toself", fillcolor=c_flange_ej, line=line_s, showlegend=False))
        fig.add_trace(go.Scatter(mode='lines', x=[-dsm/2+tfv, dsm/2-tfv, dlg/2-tfv, -dlg/2+tfv, -dsm/2+tfv], y=[ysm, ysm, ylg, ylg, ysm], fill="toself", fillcolor=cw, line=line_s, showlegend=False))
        
        # 新增中心切割虛線，象徵由 H 型鋼切割組裝而成
        fig.add_shape(type="line", x0=0, x1=0, y0=ys, y1=ye, line=dict(color="black", width=2.5, dash="dash"))

    draw_ej(h_SYSC_mm-h_EJ_mm, h_SYSC_mm, d_EJ1, d_EJ2, tf_EJ, c_web_ej, flip=False)
    draw_ej(0, h_EJ_mm, d_EJ2, d_EJ1, tf_EJ, c_web_ej, flip=True)

    # 繪製 端部加勁板
    w_end = d_IC + 20.0
    fig.add_shape(type="rect", x0=-w_end/2, x1=w_end/2, y0=y_end_bot_s, y1=y_end_bot_e, fillcolor=c_end_plate, line=line_s)
    fig.add_shape(type="rect", x0=-w_end/2, x1=w_end/2, y0=y_end_top_s, y1=y_end_top_e, fillcolor=c_end_plate, line=line_s)

    # 繪製 IC 段 (拆分翼板與腹板)
    fig.add_shape(type="rect", x0=-d_IC/2, x1=-d_IC/2+tf_IC, y0=y_ic_b, y1=y_ic_t, fillcolor=c_flange_ic, line=line_s)
    fig.add_shape(type="rect", x0=d_IC/2-tf_IC, x1=d_IC/2, y0=y_ic_b, y1=y_ic_t, fillcolor=c_flange_ic, line=line_s)
    fig.add_shape(type="rect", x0=-d_IC/2+tf_IC, x1=d_IC/2-tf_IC, y0=y_ic_b, y1=y_ic_t, fillcolor=c_web_ic, line=line_s)
    
    # 繪製 IC 段面外加勁板
    hw_ic_net = d_IC - 2 * tf_IC
    if nT > 0:
        for i in range(1, int(nT) + 1):
            yc = y_ic_b + i * (h_IC_mm / (nT + 1))
            fig.add_shape(type="line", x0=-hw_ic_net/2, x1=hw_ic_net/2, y0=yc, y1=yc, line=dict(color=c_stiff, width=3.0))
    if nL > 0:
        for i in range(1, int(nL) + 1):
            xc = -hw_ic_net/2 + i * (hw_ic_net / (nL + 1))
            fig.add_shape(type="line", x0=xc, x1=xc, y0=y_ic_b, y1=y_ic_t, line=dict(color=c_stiff, width=3.0))

    # 隱藏所有格線與座標，突顯結構模型
    fig.update_layout(
        height=700, 
        template="plotly_dark", 
        yaxis=dict(scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False, showticklabels=False),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        margin=dict(l=10,r=10,t=10,b=10)
    )
    st.plotly_chart(fig, use_container_width=True)





