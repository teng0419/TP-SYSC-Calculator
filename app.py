import streamlit as st
import numpy as np
import plotly.graph_objects as go
import math

# --- 頁面基本設定 ---
st.set_page_config(page_title="耐震間柱計算機", layout="wide")

# ==========================================
# 注入自訂 CSS：全域更改字型為 Calibri 與基礎字體大小 20px
# ==========================================
st.markdown("""
<style>
    /* 強制所有元素使用 Calibri 字型 */
    * {
        font-family: 'Calibri', sans-serif !important;
    }
    /* 將一般段落、標籤、列表字體設定為 20px */
    p, label, li, span {
        font-size: 20px !important;
    }
    /* 標題維持等比例放大，確保版面層次感 */
    h1 { font-size: 20px !important; }
    h2 { font-size: 20px !important; }
    h3 { font-size: 20px !important; }
</style>
""", unsafe_allow_html=True)

st.title("耐震間柱(SYSC)計算機")
st.markdown("版本：v.1.0 作者：傻逼巴拉")

# ==========================================
# 內建鋼材資料庫 (Fy: MPa, Ry: 超強因子, Omega: 應變硬化因子)
# ==========================================
STEEL_DB = {
    "SN400B": {"Fy": 235, "Ry": 1.3, "Omega": 1.5},
    "SN490B": {"Fy": 325, "Ry": 1.2, "Omega": 1.3},
}

# ==========================================
# 內建 CNS RH 型鋼資料庫 (d x bf x tw x tf)
# ==========================================
RH_DB = {
    "496 X 199 X 9 X 14": (496, 199, 9, 14), "500 X 200 X 10 X 16": (500, 200, 10, 16),
    "506 X 201 X 11 x 19": (506, 201, 11, 19), "512 X 202 X 12 X 22": (512, 202, 12, 22),
    "518 X 205 X 15 x 25": (518, 205, 15, 25), "528 X 208 X 18 X 30": (528, 208, 18, 30),
    "536 X 210 X 20 x 34": (536, 210, 20, 34), "548 X 215 X 25 X 40": (548, 215, 25, 40),
    "482 X 300 X 11 x 15": (482, 300, 11, 15), "488 X 300 X 11 X 18": (488, 300, 11, 18),
    "494 X 302 X 13 x 21": (494, 302, 13, 21), "500 X 304 X 15 X 24": (500, 304, 15, 24),
    "510 X 306 X 17 x 29": (510, 306, 17, 29), "518 X 310 X 21 X 33": (518, 310, 21, 33),
    "532 X 314 X 25 x 40": (532, 314, 25, 40), "596 X 199 X 10 X 15": (596, 199, 10, 15),
    "600 X 200 X 11 x 17": (600, 200, 11, 17), "606 X 201 X 12 X 20": (606, 201, 12, 20),
    "612 X 202 X 13 x 23": (612, 202, 13, 23), "618 X 205 X 16 X 26": (618, 205, 16, 26),
    "626 X 207 X 18 x 30": (626, 207, 18, 30), "634 X 209 X 20 X 34": (634, 209, 20, 34),
    "646 X 214 X 25 x 40": (646, 214, 25, 40), "582 X 300 X 12 X 17": (582, 300, 12, 17),
    "588 X 300 X 12 x 20": (588, 300, 12, 20), "594 X 302 X 14 X 23": (594, 302, 14, 23),
    "600 X 304 X 16 x 26": (600, 304, 16, 26), "608 X 306 X 18 X 30": (608, 306, 18, 30),
    "616 X 308 X 20 x 34": (616, 308, 20, 34), "628 X 312 X 24 X 40": (628, 312, 24, 40),
    "692 X 300 X 13 x 20": (692, 300, 13, 20), "700 X 300 X 13 X 24": (700, 300, 13, 24),
    "708 X 302 X 15 x 28": (708, 302, 15, 28), "712 X 306 X 19 X 30": (712, 306, 19, 30),
    "718 X 308 X 21 x 33": (718, 308, 21, 33), "732 X 311 X 24 X 40": (732, 311, 24, 40),
    "792 X 300 X 14 x 22": (792, 300, 14, 22), "800 X 300 X 14 X 26": (800, 300, 14, 26),
    "808 X 302 X 16 x 30": (808, 302, 16, 30), "816 X 306 X 20 X 34": (816, 306, 20, 34),
    "828 X 308 X 22 x 40": (828, 308, 22, 40)
}

# ==========================================
# 設計者輸入區 (微調：加入摺疊選單並保留側邊欄設定)
# ==========================================
st.sidebar.header("📝 設計者輸入參數")

with st.sidebar.expander("耐震目標", expanded=True):
    target_drift = st.number_input("目標層間側移角θd(%rad)", min_value=1.0, max_value=4.0, value=3.0, step=0.5)

with st.sidebar.expander("材料性質"):
    mat_ic_w = st.selectbox("核心段腹板 (IC Web)", list(STEEL_DB.keys()), index=1)
    mat_ic_f = st.selectbox("核心段翼板 (IC Flange)", list(STEEL_DB.keys()), index=1)
    mat_ej_w = st.selectbox("連接段腹板 (EJ Web)", list(STEEL_DB.keys()), index=1)
    mat_ej_f = st.selectbox("連接段翼板 (EJ Flange)", list(STEEL_DB.keys()), index=1)
    mat_stiff = st.selectbox("加勁板 (Stiffener)", list(STEEL_DB.keys()), index=1)
    # 接收 GPa 輸入
    E_GPa = st.number_input("楊氏模數 E (GPa)", value=200.0, step=1.0) 
    nu = st.number_input("柏松比 ν", value=0.3)

with st.sidebar.expander("SYSC斷面尺寸"):
    h_SYSC = st.number_input("間柱高度 h_SYSC (m)", value=2.6, step=0.1)
    h_IC = st.number_input("IC段高度 h_IC (m)", value=h_SYSC/3, step=0.1)
    d = st.number_input("SYSC斷面深度 d_sc (mm)", value=800.0, step=50.0)
    tw_IC = st.number_input("IC段腹板厚度 tw_IC (mm)", value=14.0, step=1.0)
    tw_EJ = st.number_input("EJ段腹板厚度 tw_EJ (mm)", value=28.0, step=1.0)
    bf = st.number_input("SYSC翼板寬度 bf (mm)", value=300.0, step=10.0)
    tf = st.number_input("SYSC翼板厚度 tf (mm)", value=26.0, step=1.0)

with st.sidebar.expander("加勁板配置"):
    n_v = st.number_input("縱向加勁板數量 nL", min_value=0, value=1, step=1)
    n_h = st.number_input("橫向加勁板數量 nT", min_value=0, value=1, step=1)
    ts = st.number_input("加勁板厚度 ts (mm)", min_value=10.0, value=15.0, step=1.0)
    bs = st.number_input("加勁板寬度 bs (mm)", min_value=90.0, value=135.0, step=10.0)

with st.sidebar.expander("邊界梁尺寸"):
    d_c = st.number_input("邊界柱深度 dc (mm)", value=500.0, step=50.0, help="假設為箱型柱")
    L_b = st.number_input("梁跨距 Lb (m)", value=6.0, step=0.1, help="柱心到柱心距離")
    mat_beam = st.selectbox("邊界梁鋼材", list(STEEL_DB.keys()), index=1)
    Fy_beam = STEEL_DB[mat_beam]["Fy"]
    beam_type = st.radio("邊界梁斷面類型", ["CNS 內建 RH 型鋼", "自訂 BH 型鋼"])
    if beam_type == "CNS 內建 RH 型鋼":
        default_rh = list(RH_DB.keys()).index("828 X 308 X 22 x 40") if "828 X 308 X 22 x 40" in RH_DB else 0
        rh_choice = st.selectbox("選擇 RH 尺寸 (d X bf X tw X tf)", list(RH_DB.keys()), index=default_rh)
        d_b, bf_b, tw_b, tf_b = RH_DB[rh_choice]
        st.markdown(f"> **邊界梁**: {d_b} X {bf_b} X {tw_b} X {tf_b}")
    else:
        d_b = st.number_input("梁深度 d_b (mm)", value=800.0, step=10.0)
        bf_b = st.number_input("梁翼板寬 bf_b (mm)", value=300.0, step=10.0)
        tw_b = st.number_input("梁腹板厚 tw_b (mm)", value=14.0, step=1.0)
        tf_b = st.number_input("梁翼板厚 tf_b (mm)", value=26.0, step=1.0)
    t_dp = st.number_input("交會區貼板厚度 t_dp (mm)", min_value=0.0, value=15.0, step=1.0, help="Panel Zone 貼板厚度")

# ==========================================
# 程式自動計算參數 (力學引擎)
# ==========================================
# 取得對應材料參數
Fy_IC = STEEL_DB[mat_ic_w]["Fy"]
Ry_IC = STEEL_DB[mat_ic_w]["Ry"]
Omega_IC = STEEL_DB[mat_ic_w]["Omega"]

Fy_EJ = min(STEEL_DB[mat_ej_w]["Fy"], STEEL_DB[mat_ej_f]["Fy"])
Ry_EJ = STEEL_DB[mat_ej_w]["Ry"]

Fy_Stiff = STEEL_DB[mat_stiff]["Fy"]

# 單位轉換
E = E_GPa * 1000.0 
G = E / (2 * (1 + nu))

h_SYSC_mm = h_SYSC * 1000.0
h_IC_mm = h_IC * 1000.0
L_b_mm = L_b * 1000.0

# --- 根據幾何連動，自動計算樓層高度 H (心到心) ---
H_s_mm = h_SYSC_mm + d_b
H_s = H_s_mm / 1000.0

h_EJ_total = h_SYSC_mm - h_IC_mm
h_EJ_single = h_EJ_total / 2.0

theta_d = target_drift / 100.0

# 1. 斷面性質 (Section Properties)
A_EJ = tf * bf * 2 + (d - 2 * tf) * tw_EJ
A_IC = tf * bf * 2 + (d - 2 * tf) * tw_IC

Ix_EJ = 1/12 * (bf * d**3 - (bf - tw_EJ) * (d - 2 * tf)**3)
Iy_EJ = 1/12 * (tf * bf**3 * 2 + (d - 2 * tf) * tw_EJ**3)
Ix_IC = 1/12 * (bf * d**3 - (bf - tw_IC) * (d - 2 * tf)**3)

ry_EJ = math.sqrt(Iy_EJ / A_EJ) if A_EJ > 0 else 0

# 2. 幾何寬厚比與未側撐檢核極限
Lmd_limit = 0.17 * ry_EJ * E / (Ry_EJ * Fy_EJ)
bf_ratio_limit = 0.38 * math.sqrt(E / (Ry_EJ * Fy_EJ))
EJ_ratio_limit = 2.61 * (1 - 0.49 * 0.125) * math.sqrt(E / (Ry_EJ * Fy_EJ))

val_flange = bf / (2 * tf)
val_web = (d - 2 * tf) / tw_EJ
val_Lb = h_SYSC_mm

# 3. 勁度計算與變形角 (Stiffness & Deformations)
K_EJ = 1.0 / (h_EJ_total / (G * tw_EJ * d) + (h_SYSC_mm**3 - h_IC_mm**3) / (12 * E * Ix_EJ))
Ke_IC = 1.0 / (h_IC_mm / (G * tw_IC * d) + h_IC_mm**3 / (12 * E * Ix_IC))
Kp_IC = 1.0 / (h_IC_mm / (0.02 * G * tw_IC * d) + h_IC_mm**3 / (12 * E * Ix_IC))

K_EE = K_EJ
Ke_F = 1.0 / (1.0 / Ke_IC + 1.0 / K_EE)
Kp_F = 1.0 / (1.0 / Kp_IC + 1.0 / K_EE)
Keff = Ke_F # 整體初始彈性勁度 (N/mm)

theta_y = 0.6 * Fy_IC * tw_IC * d / (Ke_F * h_SYSC_mm)
theta_ed = (Ke_F / K_EE) * theta_y + (Kp_F / K_EE) * (theta_d - theta_y)

# 4. 容量設計參數 (Capacity Design)
Vn_EJ = 0.6 * Fy_EJ * tw_EJ * d
Vn_IC = 0.6 * Fy_IC * tw_IC * d
Vmax = Omega_IC * Ry_IC * Vn_IC  

Sx_EJ = Ix_EJ / (d / 2)
Zx_EJ = bf * tf * (d - tf) + tw_EJ * (d / 2 - tf)**2
Zf_IC = bf * tf * (d - tf)

Mp_EJ = Zx_EJ * Fy_EJ
Mn_IC = Zf_IC * Fy_IC

Lb = h_SYSC_mm
Lp = 1.76 * ry_EJ * math.sqrt(E / Fy_EJ)
ho = d - tf
J = (2 * bf * tf**3 + (d - 2 * tf) * tw_EJ**3) / 3
Cw = Iy_EJ * ho**2 / 4
rts = math.sqrt(math.sqrt(Iy_EJ * Cw) / Sx_EJ) if Sx_EJ > 0 else 0
Lr = 1.95 * rts * E / (0.7 * Fy_EJ) * math.sqrt(J / (Sx_EJ * ho) + math.sqrt((J / (Sx_EJ * ho))**2 + 6.76 * (0.7 * Fy_EJ / E)**2))

if Lb <= Lp:
    M_EJ = Mp_EJ
else:
    M_EJ = 2.3 * (Mp_EJ - (Mp_EJ - 0.7 * Fy_EJ * Sx_EJ) * ((Lb - Lp) / (Lr - Lp)))

Mn_EJ = min(M_EJ, Mp_EJ)

Mu_EJ = Vmax * h_SYSC_mm / 2
Mu_IC = Vmax * h_IC_mm / 2

dcr_V_EJ = Vmax / (0.9 * Vn_EJ)
dcr_M_EJ = Mu_EJ / (0.9 * Mn_EJ)
dcr_M_IC = Mu_IC / (0.9 * Mn_IC)

# 5. 加勁板設計與需求 (Stiffener Check)
nL, nT = n_v, n_h
ds = (d - 2 * tf) / (nL + 1.0) if nL > 0 else (d - 2 * tf)
hs = h_IC_mm / (nT + 1.0) if nT > 0 else h_IC_mm

alpha_s = ds / hs
kc = (8.95 + 5.6 / (alpha_s**2)) if alpha_s >= 1.0 else (5.6 + 8.95 / (alpha_s**2))
lambda_nw = (hs / tw_IC) * math.sqrt(0.6 * Fy_Stiff / (kc * E))

ry_stiff = (0.6 * Fy_Stiff) / G
rd = (h_SYSC_mm / h_IC_mm) * (theta_d - theta_ed)

denominator = 2 * rd - ry_stiff
hs_tw_limit = math.sqrt(8.5 * kc / denominator) if denominator > 0 else float('inf')
hs_tw_actual = hs / tw_IC

D_plate = E * tw_IC**3 / (12.0 * (1.0 - nu**2))
Is = ts * bs**3 / 3.0
rs = E * Is / (h_IC_mm * D_plate)
alpha_s_log = np.log10(alpha_s) if alpha_s > 0 else 0
rs_star = 152.7 * alpha_s_log**2 + 21.14 * alpha_s_log + 26.34

ts_min = math.ceil(max(0.75 * tw_IC, 10.0))
bs_max = min(9.0 * ts, (bf - tw_IC) / 2.0)
rs_ratio = rs / rs_star if rs_star > 0 else float('inf')

# 6. 邊界梁檢核 (Capacity Design of Boundary Beams)
Zx_beam = bf_b * tf_b * (d_b - tf_b) + tw_b * (d_b / 2 - tf_b)**2
Mp_beam = Zx_beam * Fy_beam
Vn_beam = 0.6 * Fy_beam * d_b * tw_b

# 6.1 最大剪力強度 V_ult (依據 AISC 341-22 EBF, omega = 1.1)
omega_beam = 1.1
V_ult = omega_beam * Ry_IC * Vn_IC

# 6.2 邊界梁需求與容量
L_prime = (L_b_mm - d - d_c) / 2.0 
M_b2 = 1.1 * Zx_beam * Fy_beam

# 解聯立方程式求得 M_b1 與 V_b
term_Vult = V_ult * (h_SYSC_mm / 2.0 + d_b / 2.0)
term_Mb2 = M_b2 * (d / (2.0 * L_prime))
denom_Mb1 = 1.0 + (d / (2.0 * L_prime))

M_b1 = (term_Vult - term_Mb2) / denom_Mb1
V_b = (M_b1 + M_b2) / L_prime

dcr_beam_M = M_b1 / Mp_beam
dcr_beam_V = V_b / Vn_beam

# 6.3 交會區 (Panel Zone) 檢核
delta_M = 2.0 * (V_ult * (h_SYSC_mm / 2.0))
V_u_PZ = (delta_M / (d - tf)) - V_b
V_n_PZ = 0.6 * Fy_beam * d_b * (tw_b + t_dp)
dcr_PZ = V_u_PZ / (1.0 * V_n_PZ)

# ==========================================
# 輸出結果與檢核區
# ==========================================

def format_dcr(x):
    if x == 0 or np.isnan(x): return "0.00"
    digits = int(math.floor(math.log10(abs(x))))
    round_digits = 2 - digits
    return f"{round(x, round_digits):.{max(0, round_digits)}f}"

def check_item(name, val_str, is_ok):
    color = "#00E000" if is_ok else "#FF0000"
    status = "OK!" if is_ok else "NG!"
    return f"- **{name}**: {val_str} &rarr; <span style='color:{color}; font-weight:bold;'>{status}</span>"

tab1, tab2, tab3, tab4 = st.tabs(["⚙️ 韌性設計與容量設計", "🛡️ 加勁板設計", "🏗️ 邊界梁容量設計", "📐 設計結果與示意圖"])

with tab1:
    st.subheader("SYSC 力學性質")
    st.markdown(f"""
    - **標稱剪力強度 $V_y$**: {Vn_IC/1000:.0f} kN
    - **極限剪力強度 $V_{{max}}$**: {Vmax/1000:.0f} kN
    - **等效側向彈性勁度 $K_{{eff}}$**: {Keff/1000:.1f} kN/mm
    """)
    st.divider()

    st.subheader("韌性設計檢核 (Ductile Design Checks)")
    checks_ductile = [
        ("翼板寬厚比 $\lambda_f = b_f/2t_f$", val_flange, bf_ratio_limit, "確保翼板不提早發生局部挫曲"),
        ("EJ段腹板寬厚比 $\lambda_w = (d-2t_f)/t_{w,EJ}$", val_web, EJ_ratio_limit, "確保 EJ 段腹板不提早發生局部挫曲"),
        ("未側撐長度 $L_b$ (mm)", val_Lb, Lmd_limit, "確保 SYSC 整體不發生側向扭轉挫曲 (LTB)")
    ]
    for name, val, limit, desc in checks_ductile:
        is_ok = val <= limit
        color = "#00E000" if is_ok else "#FF0000"
        status = "OK!" if is_ok else "NG!"
        st.markdown(f"- **{name}** $= {val:.1f} \le {limit:.1f}$ &rarr; <span style='color:{color}; font-weight:bold;'>{status}</span> ({desc})", unsafe_allow_html=True)

    st.write("")
    st.subheader("容量設計檢核 (Capacity Design DCR Checks)")
    checks_capacity = [
        ("EJ段剪力容量", dcr_V_EJ, "確保 EJ 段在極限剪力下保持彈性"),
        ("EJ段彎矩容量", dcr_M_EJ, "確保 EJ 段在極限彎矩下保持彈性"),
        ("IC段彎矩容量", dcr_M_IC, "確保 IC 段優先發生剪力降伏而非彎曲降伏")
    ]
    for name, dcr, desc in checks_capacity:
        is_ok = dcr <= 1.0
        color = "#00E000" if is_ok else "#FF0000"
        status = "OK!" if is_ok else "NG!"
        st.markdown(f"- **{name}** $DCR = {format_dcr(dcr)} \le 1.0$ &rarr; <span style='color:{color}; font-weight:bold;'>{status}</span> ({desc})", unsafe_allow_html=True)

with tab2:
    st.subheader("加勁板設計檢核 (Stiffener Design Checks)")
    is_ok_alpha = 0.5 <= alpha_s <= 2.0
    c_alpha = "#00E000" if is_ok_alpha else "#FF0000"
    st.markdown(f"- **子板塊寬高比** $\\alpha_s = {alpha_s:.2f}$ (建議範圍: $0.5 \sim 2.0$) &rarr; <span style='color:{c_alpha}; font-weight:bold;'>{'OK!' if is_ok_alpha else 'NG!'}</span>", unsafe_allow_html=True)
    st.markdown(f"- **加勁板配置** $= {int(nL)}L {int(nT)}T$ &rarr; <span style='color:#00E000; font-weight:bold;'>OK!</span> (縱向/橫向配置)", unsafe_allow_html=True)
    is_ok_lam = 0.145 <= lambda_nw <= 0.6
    c_lam = "#00E000" if is_ok_lam else "#FF0000"
    st.markdown(f"- **標準化寬厚比** $\\lambda_{{nw}} = {lambda_nw:.3f}$ (限制值: $0.145 \sim 0.6$) &rarr; <span style='color:{c_lam}; font-weight:bold;'>{'OK!' if is_ok_lam else 'NG!'}</span>", unsafe_allow_html=True)
    is_ok_hs_tw = hs_tw_actual <= hs_tw_limit
    c_hs_tw = "#00E000" if is_ok_hs_tw else "#FF0000"
    limit_str = f"{hs_tw_limit:.1f}" if hs_tw_limit != float('inf') else "∞"
    st.markdown(f"- **子板塊寬厚比** $h_s/t_{{w,IC}} = {hs_tw_actual:.1f} \le {limit_str}$ &rarr; <span style='color:{c_hs_tw}; font-weight:bold;'>{'OK!' if is_ok_hs_tw else 'NG!'}</span> (避免提早挫曲)", unsafe_allow_html=True)
    is_ok_ts = ts >= ts_min
    c_ts = "#00E000" if is_ok_ts else "#FF0000"
    st.markdown(f"- **加勁板厚度** $t_s = {ts:.1f} \ge {ts_min:.1f}$ mm &rarr; <span style='color:{c_ts}; font-weight:bold;'>{'OK!' if is_ok_ts else 'NG!'}</span> (最低需求)", unsafe_allow_html=True)
    is_ok_bs = bs <= bs_max
    c_bs = "#00E000" if is_ok_bs else "#FF0000"
    st.markdown(f"- **加勁板寬度** $b_s = {bs:.1f} \le {bs_max:.1f}$ mm &rarr; <span style='color:{c_bs}; font-weight:bold;'>{'OK!' if is_ok_bs else 'NG!'}</span> (寬度上限)", unsafe_allow_html=True)
    is_ok_rs = rs_ratio >= 1.0
    c_rs = "#00E000" if is_ok_rs else "#FF0000"
    st.markdown(f"- **最適加勁剛度比** $r_s/r_s^* = {rs_ratio:.2f} \ge 1.0$ &rarr; <span style='color:{c_rs}; font-weight:bold;'>{'OK!' if is_ok_rs else 'NG!'}</span> (提供 $r_s={rs:.1f}$, 需求 $r_s^*={rs_star:.1f}$)", unsafe_allow_html=True)

with tab3:
    st.subheader("邊界梁能力設計檢核 (Capacity Design of Boundary Beams)")
    st.markdown(f"""
    - **最大設計剪力 $V_{{ult}}$**: {V_ult/1000:.0f} kN $\\quad(1.1R_yV_y)$
    - **邊界梁塑性彎矩 $M_{{b2}}$**: {M_b2/1000000:.0f} kN-m $\\quad(1.1ZF_y)$
    - **邊界梁淨跨距 $L'$**: {L_prime:.0f} mm
    """)
    st.divider()
    st.markdown(f"""
    **[邊界梁極限需求]**
    - **邊界梁近間柱端彎矩需求 $M_{{b1}}$**: {M_b1/1000000:.0f} kN-m
    - **邊界梁剪力需求 $V_b$**: {V_b/1000:.0f} kN
    """)
    st.write("")
    checks_beam = [
        ("邊界梁彎矩容量檢核 ($M_{b1} \le M_{p,b}$)", dcr_beam_M, "確保邊界梁在靠近 SYSC 處不發生彎矩塑鉸"),
        ("邊界梁剪力容量檢核 ($V_b \le V_{n,b}$)", dcr_beam_V, "確保梁腹板足以抵抗剪力")
    ]
    for name, dcr, desc in checks_beam:
        is_ok = dcr <= 1.0
        color = "#00E000" if is_ok else "#FF0000"
        status = "OK!" if is_ok else "NG!"
        st.markdown(f"- **{name}** $DCR = {format_dcr(dcr)} \le 1.0$ &rarr; <span style='color:{color}; font-weight:bold;'>{status}</span> ({desc})", unsafe_allow_html=True)
    st.write("")
    st.subheader("間柱與邊界梁交會區 (Panel Zone) 檢核")
    st.markdown(f"""
    - **交會區剪力需求 $V_{{u,PZ}}$**: {V_u_PZ/1000:.0f} kN $\\quad(\\frac{{\\Delta M}}{{d_{{sc}} - t_{{f,sc}}}} - V_b)$
    - **交會區剪力容量 $V_{{n,PZ}}$**: {V_n_PZ/1000:.0f} kN $\\quad(0.6 F_{{y,b}} d_b (t_{{w,b}} + t_{{dp}}))$
    """)
    is_ok_pz = dcr_PZ <= 1.0
    c_pz = "#00E000" if is_ok_pz else "#FF0000"
    s_pz = "OK!" if is_ok_pz else "NG!"
    st.markdown(f"- **交會區剪力容量檢核 ($V_{{u,PZ}} \le \phi V_{{n,PZ}}$)** $DCR = {format_dcr(dcr_PZ)} \le 1.0$ &rarr; <span style='color:{c_pz}; font-weight:bold;'>{s_pz}</span> (確保交會區腹板與貼板足夠強)", unsafe_allow_html=True)

with tab4:
    st.subheader("📝 設計結果總覽 (Summary)")
    st.markdown(f"""
    - **標稱剪力強度 $V_y$**: {Vn_IC/1000:.0f} kN
    - **極限剪力強度 $V_{{max}}$**: {Vmax/1000:.0f} kN
    - **等效側向彈性勁度 $K_{{eff}}$**: {Keff/1000:.1f} kN/mm
    - **SYSC 尺寸**: {d:.0f} X {bf:.0f} X {tw_EJ:.0f} X {tf:.0f} (mm)
    - **邊界梁尺寸**: {d_b:.0f} X {bf_b:.0f} X {tw_b:.0f} X {tf_b:.0f} (mm)
    """)
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("**⚙️ 韌性設計與容量設計**")
        st.markdown(check_item("翼板寬厚比", f"${val_flange:.1f} \\le {bf_ratio_limit:.1f}$", val_flange <= bf_ratio_limit), unsafe_allow_html=True)
        st.markdown(check_item("EJ腹板寬厚比", f"${val_web:.1f} \\le {EJ_ratio_limit:.1f}$", val_web <= EJ_ratio_limit), unsafe_allow_html=True)
        st.markdown(check_item("未側撐長度", f"${val_Lb:.0f} \\le {Lmd_limit:.0f}$", val_Lb <= Lmd_limit), unsafe_allow_html=True)
        st.markdown(check_item("EJ段剪力容量", f"DCR = {format_dcr(dcr_V_EJ)}", dcr_V_EJ <= 1.0), unsafe_allow_html=True)
        st.markdown(check_item("EJ段彎矩容量", f"DCR = {format_dcr(dcr_M_EJ)}", dcr_M_EJ <= 1.0), unsafe_allow_html=True)
        st.markdown(check_item("IC段彎矩容量", f"DCR = {format_dcr(dcr_M_IC)}", dcr_M_IC <= 1.0), unsafe_allow_html=True)
    with col_b:
        st.markdown("**🛡️ 加勁板設計**")
        st.markdown(check_item("子板塊寬高比", f"$\\alpha_s = {alpha_s:.2f}$", 0.5 <= alpha_s <= 2.0), unsafe_allow_html=True)
        st.markdown(check_item("標準化寬厚比", f"$\\lambda_{{nw}} = {lambda_nw:.3f}$", 0.145 <= lambda_nw <= 0.6), unsafe_allow_html=True)
        limit_str_hs = f"{hs_tw_limit:.1f}" if hs_tw_limit != float('inf') else "\\infty"
        st.markdown(check_item("子板塊寬厚比", f"${hs_tw_actual:.1f} \\le {limit_str_hs}$", hs_tw_actual <= hs_tw_limit), unsafe_allow_html=True)
        st.markdown(check_item("加勁板厚度", f"$t_s = {ts:.1f} \\ge {ts_min:.1f}$", ts >= ts_min), unsafe_allow_html=True)
        st.markdown(check_item("加勁板寬度", f"$b_s = {bs:.1f} \\le {bs_max:.1f}$", bs <= bs_max), unsafe_allow_html=True)
        st.markdown(check_item("最適加勁剛度比", f"$r_s/r_s^* = {rs_ratio:.2f}$", rs_ratio >= 1.0), unsafe_allow_html=True)
    with col_c:
        st.markdown("**🏗️ 邊界梁容量設計**")
        st.markdown(check_item("邊界梁彎矩容量", f"DCR = {format_dcr(dcr_beam_M)}", dcr_beam_M <= 1.0), unsafe_allow_html=True)
        st.markdown(check_item("邊界梁剪力容量", f"DCR = {format_dcr(dcr_beam_V)}", dcr_beam_V <= 1.0), unsafe_allow_html=True)
        st.markdown(check_item("交會區剪力容量", f"DCR = {format_dcr(dcr_PZ)}", dcr_PZ <= 1.0), unsafe_allow_html=True)

    # ==========================================
    # 幾何配置示意圖 (微調：確保範圍正確)
    # ==========================================
    st.divider()
    st.subheader("SYSC 與構架正視圖配置 (按實際比例繪製)")
    fig_geom = go.Figure()
    hw = d - 2 * tf
    y_bottom, y_ic_bottom, y_ic_top, y_top = 0, h_EJ_single, h_EJ_single + h_IC_mm, h_SYSC_mm
    x_center = 0
    x_left_flange, x_web_start, x_web_end, x_right_flange = -d/2, -d/2+tf, d/2-tf, d/2
    c_flange, c_ej_web, c_ic_web, c_stiff, c_beam_flange, c_beam_web, c_beam_col, c_pz_web = "#E0E0E0", "#1E90FF", "#FF4500", "#FFD700", "#777777", "#444444", "#555555", "#2C3E50"
    line_style = dict(color="white", width=1)
    line_cl = dict(color="rgba(255,255,255,0.4)", width=1.5, dash="dashdot")
    
    x_col_L_left, x_col_L_right = x_center - L_b_mm/2 - d_c/2, x_center - L_b_mm/2 + d_c/2
    x_col_R_left, x_col_R_right = x_center + L_b_mm/2 - d_c/2, x_center + L_b_mm/2 + d_c/2
    y_col_top, y_col_bottom = h_SYSC_mm + d_b, -d_b

    # 繪製柱與梁
    fig_geom.add_shape(type="rect", x0=x_col_L_left, x1=x_col_L_right, y0=y_col_bottom, y1=y_col_top, line=line_style, fillcolor=c_beam_col, opacity=0.6)
    fig_geom.add_shape(type="rect", x0=x_col_R_left, x1=x_col_R_right, y0=y_col_bottom, y1=y_col_top, line=line_style, fillcolor=c_beam_col, opacity=0.6)
    fig_geom.add_shape(type="rect", x0=x_col_L_right, x1=x_col_R_left, y0=-d_b, y1=-d_b + tf_b, line=line_style, fillcolor=c_beam_flange, opacity=0.8)
    fig_geom.add_shape(type="rect", x0=x_col_L_right, x1=x_col_R_left, y0=-d_b + tf_b, y1=-tf_b, line=line_style, fillcolor=c_beam_web, opacity=0.8)
    fig_geom.add_shape(type="rect", x0=x_col_L_right, x1=x_col_R_left, y0=-tf_b, y1=y_bottom, line=line_style, fillcolor=c_beam_flange, opacity=0.8)
    fig_geom.add_shape(type="rect", x0=x_col_L_right, x1=x_col_R_left, y0=y_top, y1=y_top + tf_b, line=line_style, fillcolor=c_beam_flange, opacity=0.8)
    fig_geom.add_shape(type="rect", x0=x_col_L_right, x1=x_col_R_left, y0=y_top + tf_b, y1=y_top + d_b - tf_b, line=line_style, fillcolor=c_beam_web, opacity=0.8)
    fig_geom.add_shape(type="rect", x0=x_col_L_right, x1=x_col_R_left, y0=y_top + d_b - tf_b, y1=y_top + d_b, line=line_style, fillcolor=c_beam_flange, opacity=0.8)

    # 繪製 Panel Zone
    fig_geom.add_shape(type="rect", x0=x_left_flange, x1=x_web_start, y0=-d_b + tf_b, y1=-tf_b, line=line_style, fillcolor=c_flange, opacity=1.0)
    fig_geom.add_shape(type="rect", x0=x_web_end, x1=x_right_flange, y0=-d_b + tf_b, y1=-tf_b, line=line_style, fillcolor=c_flange, opacity=1.0)
    fig_geom.add_shape(type="rect", x0=x_web_start, x1=x_web_end, y0=-d_b + tf_b, y1=-tf_b, line=line_style, fillcolor=c_pz_web, opacity=0.9)
    fig_geom.add_shape(type="rect", x0=x_left_flange, x1=x_web_start, y0=y_top + tf_b, y1=y_top+d_b - tf_b, line=line_style, fillcolor=c_flange, opacity=1.0)
    fig_geom.add_shape(type="rect", x0=x_web_end, x1=x_right_flange, y0=y_top + tf_b, y1=y_top+d_b - tf_b, line=line_style, fillcolor=c_flange, opacity=1.0)
    fig_geom.add_shape(type="rect", x0=x_web_start, x1=x_web_end, y0=y_top + tf_b, y1=y_top+d_b - tf_b, line=line_style, fillcolor=c_pz_web, opacity=0.9)

    # 繪製 SYSC
    fig_geom.add_shape(type="rect", x0=x_web_start, x1=x_web_end, y0=y_bottom, y1=y_ic_bottom, line=line_style, fillcolor=c_ej_web, opacity=0.85)
    fig_geom.add_shape(type="rect", x0=x_web_start, x1=x_web_end, y0=y_ic_bottom, y1=y_ic_top, line=line_style, fillcolor=c_ic_web, opacity=0.85)
    fig_geom.add_shape(type="rect", x0=x_web_start, x1=x_web_end, y0=y_ic_top, y1=y_top, line=line_style, fillcolor=c_ej_web, opacity=0.85)
    fig_geom.add_shape(type="rect", x0=x_left_flange, x1=x_web_start, y0=y_bottom, y1=y_top, line=line_style, fillcolor=c_flange, opacity=1.0)
    fig_geom.add_shape(type="rect", x0=x_web_end, x1=x_right_flange, y0=y_bottom, y1=y_top, line=line_style, fillcolor=c_flange, opacity=1.0)
    
    # 繪製加勁板
    if nL > 0:
        dx = hw / (nL + 1)
        for i in range(1, int(nL) + 1):
            xc = x_web_start + i * dx
            fig_geom.add_shape(type="rect", x0=xc - ts/2, x1=xc + ts/2, y0=y_ic_bottom, y1=y_ic_top, line=line_style, fillcolor=c_stiff)
    if nT > 0:
        dy = h_IC_mm / (nT + 1)
        for i in range(1, int(nT) + 1):
            yc = y_ic_bottom + i * dy
            fig_geom.add_shape(type="rect", x0=x_web_start, x1=x_web_end, y0=yc - ts/2, y1=yc + ts/2, line=line_style, fillcolor=c_stiff)
    fig_geom.add_shape(type="rect", x0=x_web_start, x1=x_web_end, y0=y_ic_bottom - ts/2, y1=y_ic_bottom + ts/2, line=line_style, fillcolor=c_stiff)
    fig_geom.add_shape(type="rect", x0=x_web_start, x1=x_web_end, y0=y_ic_top - ts/2, y1=y_ic_top + ts/2, line=line_style, fillcolor=c_stiff)

    # 標註與中心線
    fig_geom.add_shape(type="line", x0=-L_b_mm/2 - d_c, x1=L_b_mm/2 + d_c, y0=-d_b/2, y1=-d_b/2, line=line_cl)
    fig_geom.add_shape(type="line", x0=-L_b_mm/2 - d_c, x1=L_b_mm/2 + d_c, y0=h_SYSC_mm + d_b/2, y1=h_SYSC_mm + d_b/2, line=line_cl)
    fig_geom.add_shape(type="line", x0=-L_b_mm/2, x1=-L_b_mm/2, y0=-d_b - 400, y1=h_SYSC_mm + d_b + 400, line=line_cl)
    fig_geom.add_shape(type="line", x0=L_b_mm/2, x1=L_b_mm/2, y0=-d_b - 400, y1=h_SYSC_mm + d_b + 400, line=line_cl)

    # 佈局設定
    fig_geom.update_layout(
        font=dict(family="Calibri", size=20),
        xaxis=dict(range=[-L_b_mm/2 - d_c/2 - 400, L_b_mm/2 + d_c/2 + 200], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[-d_b - 500, h_SYSC_mm + d_b + 500], scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False, visible=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=800,
        margin=dict(l=20, r=20, t=30, b=20)
    )
    st.plotly_chart(fig_geom, use_container_width=True)