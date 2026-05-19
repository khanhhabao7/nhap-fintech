from flask import Flask, render_template, request, jsonify
import random
import math
import uuid

app = Flask(__name__, template_folder='templates')
app.secret_key = 'startup-game-secret'

# ===================== DỮ LIỆU CỐ ĐỊNH =====================
SCENARIOS = [
    {"id":1,"name":"Tin tốt nhẹ","cat":"Market","delta":{"price":0.05,"cogs":0,"hype":10,"sentiment":5,"transparency":0,"reg_risk":0}},
    {"id":2,"name":"Tin tốt vừa","cat":"Market","delta":{"price":0.1,"cogs":-0.05,"hype":20,"sentiment":10,"transparency":0,"reg_risk":0}},
    {"id":3,"name":"Tin xấu nhẹ","cat":"Market","delta":{"price":-0.05,"cogs":0.03,"hype":-10,"sentiment":-5,"transparency":0,"reg_risk":0}},
    {"id":4,"name":"Tin xấu vừa","cat":"Market","delta":{"price":-0.1,"cogs":0.05,"hype":-20,"sentiment":-15,"transparency":-5,"reg_risk":5}},
    {"id":5,"name":"Khủng hoảng nhẹ","cat":"Market","delta":{"price":-0.15,"cogs":0.1,"hype":-30,"sentiment":-20,"transparency":-10,"reg_risk":10}},
    {"id":6,"name":"Khủng hoảng nặng","cat":"Market","delta":{"price":-0.25,"cogs":0.15,"hype":-40,"sentiment":-30,"transparency":-20,"reg_risk":20}},
    {"id":7,"name":"Máy móc hỏng nhẹ","cat":"Internal","delta":{"cogs":0.05,"hype":-5,"transparency":-5,"trust_all":-5,"runway":-1}},
    {"id":8,"name":"Lỗi sản xuất vừa","cat":"Internal","delta":{"cogs":0.1,"hype":-10,"transparency":-10,"trust_all":-10,"runway":-2}},
    {"id":9,"name":"Rò rỉ dữ liệu","cat":"Internal","delta":{"cogs":0,"hype":-15,"transparency":-20,"trust_all":-15,"runway":0}},
    {"id":10,"name":"Nhân sự chủ chốt nghỉ","cat":"Internal","delta":{"cogs":0.03,"hype":-10,"transparency":-5,"trust_all":-5,"runway":0}},
    {"id":11,"name":"Được giải thưởng","cat":"Internal","delta":{"cogs":-0.05,"hype":15,"transparency":10,"trust_all":10,"runway":0}},
    {"id":12,"name":"Audit nội bộ tốt","cat":"Internal","delta":{"cogs":0,"hype":5,"transparency":15,"trust_all":10,"runway":0}},
    {"id":13,"name":"Đối thủ giảm giá","cat":"External","delta":{"price":-0.05,"marketing_eff":-0.1,"hype":-5,"transparency":0}},
    {"id":14,"name":"Đối thủ ra sản phẩm mới","cat":"External","delta":{"price":-0.1,"marketing_eff":-0.2,"hype":-15,"transparency":-5}},
    {"id":15,"name":"Hợp tác chiến lược","cat":"External","delta":{"price":0.05,"marketing_eff":0.15,"hype":15,"transparency":5}},
    {"id":16,"name":"Bị kiện bản quyền","cat":"External","delta":{"price":-0.08,"marketing_eff":-0.15,"hype":-20,"transparency":-10}},
    {"id":17,"name":"Được cấp bằng sáng chế","cat":"External","delta":{"price":0.1,"marketing_eff":0.1,"hype":10,"transparency":5}},
    {"id":18,"name":"Tin đồn thâu tóm","cat":"External","delta":{"price":0.15,"marketing_eff":0.05,"hype":25,"transparency":-5}},
    {"id":19,"name":"Thanh tra đột xuất","cat":"Regulatory","delta":{"reg_risk":25,"transparency":-10,"trust_all":-10,"legal_cost_percent":5}},
    {"id":20,"name":"Được cấp phép sandbox","cat":"Regulatory","delta":{"reg_risk":-30,"transparency":15,"trust_all":15,"legal_cost_percent":-3}},
    {"id":21,"name":"Thay đổi luật có lợi","cat":"Regulatory","delta":{"reg_risk":-15,"transparency":5,"trust_all":5,"legal_cost_percent":0}},
    {"id":22,"name":"Thay đổi luật bất lợi","cat":"Regulatory","delta":{"reg_risk":25,"transparency":-10,"trust_all":-10,"legal_cost_percent":5}},
    {"id":23,"name":"Kiểm toán thuế","cat":"Regulatory","delta":{"reg_risk":10,"transparency":-5,"trust_all":-5,"legal_cost_percent":2}},
    {"id":24,"name":"Chứng nhận quốc tế","cat":"Regulatory","delta":{"reg_risk":-10,"transparency":10,"trust_all":10,"legal_cost_percent":-2}},
]

ACTIVE_CARDS_FULL = [
    {"id":"A1","name":"Marketing Blitz","cost":2,"type":"red","desc":"Tăng Hype, giảm Transparency","effect":{"hype":25,"transparency":-5,"cost_percent":3}},
    {"id":"A2","name":"Viral Campaign","cost":3,"type":"red","desc":"Tăng Hype mạnh","effect":{"hype":40,"transparency":-10,"cost_percent":5}},
    {"id":"A3","name":"Flash Sale","cost":2,"type":"red","desc":"Giảm giá tạm thời, tăng Hype","effect":{"price_percent":-15,"hype":15}},
    {"id":"A4","name":"Influencer Deal","cost":2,"type":"red","desc":"Tăng Hype và Visibility","effect":{"hype":20,"visibility":15,"cost_percent":2}},
    {"id":"A6","name":"FOMO Campaign","cost":2,"type":"red","desc":"Tăng Hype, thêm funding","effect":{"hype":20,"funding_boost_percent":5}},
    {"id":"A7","name":"Celebrity Endorsement","cost":2,"type":"red","desc":"Tăng Hype, giảm nhẹ minh bạch","effect":{"hype":25,"transparency":-3,"cost_percent":4}},
    {"id":"A9","name":"Limited Offer","cost":1,"type":"red","desc":"Tăng Hype, Visibility nhẹ","effect":{"hype":10,"visibility":5}},
    {"id":"A10","name":"Shill Army","cost":2,"type":"red","desc":"Tăng Hype cao, giảm minh bạch","effect":{"hype":30,"transparency":-15,"cost_percent":2}},
    {"id":"A11","name":"Pre-sale Discount","cost":2,"type":"red","desc":"Giảm giá, tăng funding","effect":{"price_percent":-10,"funding_boost_percent":10}},
    {"id":"A12","name":"Media Blast","cost":2,"type":"red","desc":"Tăng Hype, Visibility","effect":{"hype":20,"visibility":10,"cost_percent":1}},
    {"id":"A13","name":"Meme Marketing","cost":1,"type":"red","desc":"Tăng Hype nhẹ, giảm minh bạch","effect":{"hype":15,"transparency":-2}},
    {"id":"A14","name":"Aggressive Pricing","cost":2,"type":"red","desc":"Giảm giá sâu, tăng Hype","effect":{"price_percent":-20,"hype":10}},
    {"id":"D1","name":"Cost Cutting","cost":1,"type":"green","desc":"Giảm COGS, tăng minh bạch","effect":{"cogs_percent":-3,"transparency":5}},
    {"id":"D2","name":"Community Update","cost":1,"type":"green","desc":"Tăng Hype nhẹ, minh bạch","effect":{"hype":5,"transparency":3}},
    {"id":"D3","name":"Third Party Audit","cost":2,"type":"green","desc":"Tăng minh bạch, giảm rủi ro","effect":{"transparency":15,"reg_risk":-10,"cost_percent":5}},
    {"id":"D4","name":"Vesting Pledge","cost":1,"type":"green","desc":"Tăng minh bạch, trust","effect":{"transparency":10,"trust_all":5}},
    {"id":"D5","name":"Emergency Fund","cost":2,"type":"green","desc":"Tăng runway","effect":{"runway":2,"cost_percent":5}},
    {"id":"D6","name":"Open Book","cost":2,"type":"green","desc":"Tăng minh bạch mạnh","effect":{"transparency":20,"cost_percent":2}},
    {"id":"D8","name":"Legal Shield","cost":2,"type":"green","desc":"Giảm rủi ro pháp lý","effect":{"reg_risk":-15,"cost_percent":3}},
    {"id":"D9","name":"Slow & Steady","cost":1,"type":"green","desc":"Tăng minh bạch, Hype nhẹ","effect":{"transparency":5,"hype":2}},
    {"id":"D10","name":"Crisis Management","cost":2,"type":"green","desc":"Giảm 50% delta tiêu cực","effect":{"halve_negative_delta":1}},
    {"id":"D11","name":"Supply Chain Fix","cost":2,"type":"green","desc":"Giảm COGS, tăng minh bạch","effect":{"cogs_percent":-5,"transparency":5}},
    {"id":"D12","name":"Investor Call","cost":1,"type":"green","desc":"Tăng trust tất cả bot","effect":{"trust_all":10,"cost_percent":1}},
    {"id":"D13","name":"Transparency Report","cost":2,"type":"green","desc":"Tăng minh bạch, giảm Hype","effect":{"transparency":15,"hype":-5}},
    {"id":"T1","name":"Whale Discount","cost":3,"type":"purple","desc":"Tăng funding, giảm trust Whale","effect":{"funding_boost_percent":15,"trust_whale":-10,"cost_percent":2}},
    {"id":"T3","name":"Secondary Offering","cost":3,"type":"purple","desc":"Tăng funding, giảm trust","effect":{"funding_boost_percent":20,"trust_all":-15}},
    {"id":"T4","name":"DAO Vote","cost":2,"type":"purple","desc":"Tăng minh bạch, trust","effect":{"transparency":5,"trust_all":5}},
    {"id":"T6","name":"Treasury Diversify","cost":2,"type":"purple","desc":"Giảm rủi ro, tăng trust","effect":{"reg_risk":-10,"trust_all":10}},
    {"id":"T7","name":"Token Split","cost":2,"type":"purple","desc":"Tăng funding, Hype","effect":{"funding_boost_percent":5,"hype":10}},
    {"id":"T8","name":"Governance Proposal","cost":1,"type":"purple","desc":"Tăng minh bạch, trust","effect":{"transparency":5,"trust_all":5}},
    {"id":"T9","name":"Vesting Extension","cost":2,"type":"purple","desc":"Tăng trust, minh bạch","effect":{"trust_all":20,"transparency":10,"cost_percent":2}},
    {"id":"T11","name":"Strategic Partnership","cost":2,"type":"purple","desc":"Tăng trust, giảm rủi ro","effect":{"trust_all":15,"reg_risk":-5,"cost_percent":3}},
    {"id":"T13","name":"Airdrop to Holders","cost":2,"type":"purple","desc":"Tăng trust, Hype","effect":{"trust_all":10,"hype":15,"cost_percent":4}},
    {"id":"T14","name":"Equity Swap","cost":3,"type":"purple","desc":"Tăng funding mạnh, giảm trust","effect":{"funding_boost_percent":30,"trust_all":-20}},
]

REACTION_CARDS = [
    {"id":"R1","name":"Lock‑up Extension","trigger":"on_bot_withdraw","desc":"Giảm bán tháo khi bot rút","cost_percent":2,"effect":{"sell_pressure_reduce":0.5}},
    {"id":"R2","name":"Emergency PR","trigger":"on_scenario_market_bad","desc":"Giảm 50% delta xấu","cost_percent":3,"effect":{"halve_negative_delta":1}},
    {"id":"R3","name":"Whale Whisperer","trigger":"on_whale_trust<30","desc":"Tăng trust của Whale","cost_percent":5,"effect":{"whale_trust":10}},
    {"id":"R4","name":"Damage Control","trigger":"on_transparency<30","desc":"Tăng transparency, giảm Hype","cost_percent":2,"effect":{"transparency":10,"hype":-5}},
    {"id":"R5","name":"Liquidity Injection","trigger":"on_circuit_breaker","desc":"Rút ngắn circuit breaker","cost_percent":8,"effect":{"circuit_breaker_reduce":1}},
    {"id":"R6","name":"Legal Emergency","trigger":"on_reg_risk>70","desc":"Giảm rủi ro pháp lý","cost_percent":4,"effect":{"reg_risk":-20}},
    {"id":"R7","name":"Security Patch","trigger":"on_security<30","desc":"Tăng security","cost_percent":3,"effect":{"security":15}},
    {"id":"R8","name":"FOMO Suppression","trigger":"on_hype>80","desc":"Giảm Hype, tăng transparency","cost_percent":1,"effect":{"hype":-15,"transparency":5}},
    {"id":"R9","name":"Investor Assurance","trigger":"on_trust_any_bot<20","desc":"Tăng trust cho bot đó","cost_percent":2,"effect":{"trust_single":15}},
    {"id":"R10","name":"Runway Boost","trigger":"on_runway<3","desc":"Thêm 3 tháng runway","cost_percent":10,"effect":{"runway":3}},
]

random.seed(42)
BOTS = []
for i in range(1, 201):
    bot_type = random.choices(["FOMO","Value Hunter","Whale","Random"], weights=[50,30,10,10])[0]
    wealth_class = random.choices(["small","medium","large"], weights=[40,40,20])[0]
    wealth = {"small":random.randint(10000,50000), "medium":random.randint(100000,500000), "large":random.randint(500000,2000000)}[wealth_class]
    hype_sens = round(random.uniform(1.5, 2.5), 2)
    trans_sens = round(random.uniform(0.5,1.2),2)
    decay = round(random.uniform(0.1,0.3),2)
    if bot_type == "FOMO":
        weights = {"intrinsic":0.1,"valuation":0.1,"roi_norm":0.1,"scalability":0.05,"transparency":0.05,"hype":0.5,"visibility":0.09,"funding_prog":0.09,"liquidity":0.02}
    elif bot_type == "Value Hunter":
        weights = {"intrinsic":0.27,"valuation":0.2,"roi_norm":0.15,"scalability":0.03,"transparency":0.14,"hype":0.1,"funding_prog":0.05,"liquidity":0.06}
    elif bot_type == "Whale":
        weights = {"intrinsic":0.17,"valuation":0.2,"roi_norm":0.15,"scalability":0.03,"transparency":0.18,"hype":0.15,"funding_prog":0.05,"liquidity":0.07}
    else:
        weights = {"intrinsic":0.1,"valuation":0.1,"roi_norm":0.1,"scalability":0.05,"transparency":0.05,"hype":0.2,"visibility":0.05,"funding_prog":0.09,"liquidity":0.18}
    BOTS.append({"id":i,"type":bot_type,"wealth_class":wealth_class,"wealth":wealth,"hype_sens":hype_sens,"trans_sens":trans_sens,"memory_decay_rate":decay,"weights":weights})

# ===================== HÀM TÍNH TOÁN =====================
def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def calculate_metrics(proj):
    total_fees = proj["fee_ecom"] + proj["fee_retail"] + proj["fee_direct"]
    ch_fees = total_fees / 100.0
    price_real = proj["price"] * (1 - ch_fees)
    cogs_unit = (proj["material"] + proj["packaging"] + proj["labor"]) * (1 + proj["defect_rate"] / 100.0)
    gm = (price_real - cogs_unit) / price_real if price_real > 0 else 0
    monthly_burn = proj["fixed_cost"] + proj["marketing_cost"] + (proj["loan"] * proj["interest_rate"] / 100 / 12)
    burn_rate = monthly_burn / proj["target_funding"] if proj["target_funding"] > 0 else 0
    growth = (proj["units_m6"] / proj["units_m1"]) - 1 if proj["units_m1"] > 0 else 0
    unit_econ = clamp(20 + 20 * (1 - math.exp(-5 * (gm - 0.2) / 0.6)), 20, 40) if gm > 0.2 else 20
    burn_score = clamp(10 + 20 * (1 - math.exp(-4 * (0.3 - burn_rate) / 0.25)), 10, 30) if burn_rate < 0.3 else 10
    scal_score = clamp(10 + 20 * (1 - math.exp(-3 * growth / 0.5)), 10, 30) if growth > 0 else 10
    intrinsic = unit_econ + burn_score + scal_score

    total_invested = proj.get("total_invested", 0)
    revenue_year = proj["units_m6"] * 12 * price_real
    ps_ratio = 5.0
    hype = proj.get("hype", 50)
    if hype > 70: ps_ratio += 2
    elif hype < 30: ps_ratio -= 1
    if growth > 0.5: ps_ratio += 1.5
    elif growth < -0.2: ps_ratio -= 1
    ps_ratio = max(1.5, min(15, ps_ratio))
    estimated_valuation = revenue_year * ps_ratio
    if total_invested > 0:
        raw_roi = ((estimated_valuation - total_invested) / total_invested) * 100
        raw_roi = max(0, raw_roi)
    else:
        raw_roi = 0
    roi_norm = min(100, 20 * math.log10(raw_roi + 1))

    mult = estimated_valuation / revenue_year if revenue_year > 0 else 1000
    if mult < 1: val_score = 30 - (1-mult)/1*30
    elif mult <= 3: val_score = 80 + (mult-1)/2*20
    elif mult <= 5: val_score = 80 - (mult-3)/2*40
    else: val_score = max(0, 40 - (mult-5)/2*40)
    val_score = clamp(val_score, 0, 100)

    base_reg = 20 if proj.get("has_license", False) else 80
    if proj.get("legal_cost_spent", 0) >= 0.05 * proj["target_funding"]: base_reg += 20
    reg_risk = clamp(base_reg - proj["transparency"] / 10, 0, 100)

    avail_cash = proj.get("available_cash", proj["owner_equity"] + proj["loan"])
    runway = math.floor(avail_cash / monthly_burn) if monthly_burn > 0 else 999
    liquidity = 100

    return {
        "intrinsic": intrinsic, "valuation_sanity": val_score, "roi_norm": roi_norm,
        "growth": growth, "monthly_burn": monthly_burn, "available_cash": avail_cash,
        "runway": runway, "liquidity": liquidity, "funding_progress": proj.get("funding_progress", 0),
        "estimated_valuation": estimated_valuation, "raw_roi": raw_roi
    }

def attractiveness(project, bot, metrics):
    raw = 0
    total_w = 0
    for key, w in bot["weights"].items():
        if key=="intrinsic": val = metrics["intrinsic"]
        elif key=="valuation": val = metrics["valuation_sanity"]
        elif key=="roi_norm": val = metrics["roi_norm"]
        elif key=="scalability": val = clamp(metrics["growth"]*100,0,100)
        elif key=="transparency": val = project["transparency"]
        elif key=="hype": val = project["hype"]
        elif key=="visibility": val = project.get("visibility", 50)
        elif key=="funding_prog": val = metrics["funding_progress"]*100
        elif key=="liquidity": val = metrics["liquidity"]
        else: continue
        sens = bot["hype_sens"] if key=="hype" else (bot["trans_sens"] if key=="transparency" else 1.0)
        raw += val * w * sens
        total_w += w
    if total_w == 0: return 0
    raw_A = (raw / total_w) * 100
    if metrics["valuation_sanity"] < 40:
        raw_A = max(0, raw_A - (40 - metrics["valuation_sanity"]) * 1.5)
    trust = project["trust_scores"].get(bot["id"], 50)
    noise = random.uniform(-5,5) if bot["type"] != "Random" else random.uniform(-10,10)
    return raw_A * (trust / 100) + noise

def final_score(proj, phases_used, metrics):
    if proj["funding_progress"] < 0.5:
        return 0
    funding_score = proj["funding_progress"] * 30
    speed_score = (100 - phases_used) * 0.2
    roi_score = min(30, max(0, (metrics["roi_norm"] / 100) * 30))
    trans_score = (proj["transparency"] / 100) * 20
    raw = funding_score + speed_score + roi_score + trans_score
    perf_phase = raw / phases_used if phases_used > 0 else 0
    return perf_phase * proj.get("scale_factor", 1.0) * (1 + proj["funding_progress"])

# ===================== VALIDATION =====================
def validate_project(proj):
    required = ['price', 'fee_ecom', 'fee_retail', 'fee_direct', 'material', 'packaging', 'labor',
                'defect_rate', 'units_m1', 'units_m3', 'units_m6', 'fixed_cost', 'marketing_cost',
                'owner_equity', 'loan', 'interest_rate', 'equity_offered', 'target_funding', 'scale']
    for field in required:
        if field not in proj or proj[field] is None:
            return False, f"Missing field: {field}"
        if isinstance(proj[field], (int, float)) and proj[field] < 0:
            return False, f"{field} cannot be negative"

    scale = proj['scale']
    target = proj['target_funding']
    if scale == 'Small':
        if not (30000 <= target <= 80000):
            return False, "Target funding for Small must be 30,000 – 80,000 USD"
        proj['scale_factor'] = 0.8
        proj['max_phase'] = 5
    elif scale == 'Medium':
        if not (100000 <= target <= 200000):
            return False, "Target funding for Medium must be 100,000 – 200,000 USD"
        proj['scale_factor'] = 1.0
        proj['max_phase'] = 7
    elif scale == 'Large':
        if not (250000 <= target <= 500000):
            return False, "Target funding for Large must be 250,000 – 500,000 USD"
        proj['scale_factor'] = 1.5
        proj['max_phase'] = 9
    else:
        return False, "Scale must be Small, Medium, or Large"

    if not (10 <= proj['price'] <= 1000):
        return False, "Retail price must be between 10 and 1000 USD"
    if not (0 <= proj['fee_ecom'] <= 100):
        return False, "E-commerce fee must be 0-100%"
    if not (0 <= proj['fee_retail'] <= 100):
        return False, "Retail fee must be 0-100%"
    if not (0 <= proj['fee_direct'] <= 100):
        return False, "Direct channel fee must be 0-100%"
    total_fees = proj['fee_ecom'] + proj['fee_retail'] + proj['fee_direct']
    if total_fees > 100:
        return False, "Total channel fees cannot exceed 100%"

    if not (0.1 <= proj['material'] <= 100):
        return False, "Direct materials must be 0.1 – 100 USD"
    if not (0.1 <= proj['packaging'] <= 100):
        return False, "Direct packaging must be 0.1 – 100 USD"
    if not (0.1 <= proj['labor'] <= 100):
        return False, "Direct labor must be 0.1 – 100 USD"
    if not (0 <= proj['defect_rate'] <= 10):
        return False, "Defect allowance must be 0 – 10%"

    for m in ['units_m1', 'units_m3', 'units_m6']:
        if not (0 <= proj[m] <= 100000):
            return False, f"{m} must be between 0 and 100,000"
    if not (proj['units_m6'] >= proj['units_m3'] >= proj['units_m1']):
        return False, "Units must be non-decreasing: m6 >= m3 >= m1"

    if not (1000 <= proj['fixed_cost'] <= 100000):
        return False, "Fixed operating cost must be 1,000 – 100,000 USD/month"
    if not (0 <= proj['marketing_cost'] <= 100000):
        return False, "Marketing cost must be 0 – 100,000 USD/month"

    if not (0 <= proj['owner_equity'] <= 300000):
        return False, "Owner equity must be 0 – 300,000 USD"
    if not (0 <= proj['loan'] <= 300000):
        return False, "Bank loan must be 0 – 300,000 USD"
    if not (5 <= proj['interest_rate'] <= 100):
        return False, "Loan interest rate must be 5 – 100%"
    if not (0.1 <= proj['equity_offered'] <= 99.9):
        return False, "Equity offered must be 0.1 – 99.9%"

    net_price = proj['price'] * (1 - total_fees / 100.0)
    cogs = (proj['material'] + proj['packaging'] + proj['labor']) * (1 + proj['defect_rate'] / 100.0)
    if net_price <= cogs:
        return False, f"Net price after fees (${net_price:.2f}) must be greater than COGS (${cogs:.2f})"

    annual_revenue = proj['units_m6'] * 12 * net_price
    ps_ratio = annual_revenue / target if target > 0 else 0
    if ps_ratio < 0.3:
        return False, f"Projected annual revenue (${annual_revenue:,.0f}) is too low for target funding (${target:,.0f}). P/S ratio = {ps_ratio:.2f} (minimum 0.3)"

    return True, "OK"

# ===================== QUẢN LÝ PHÒNG =====================
rooms = {}

def get_bots_for_phase(phase, total_bots=200):
    ratio = min(1.0, phase * 0.2)
    count = int(total_bots * ratio)
    return BOTS[:count]

@app.route('/')
def index():
    return render_template('host.html')

@app.route('/play/<room_id>/<int:player_index>')
def play_page(room_id, player_index):
    if room_id not in rooms:
        return "Phòng không tồn tại", 404
    room = rooms[room_id]
    if player_index < 0 or player_index >= room['num_players']:
        return "Chỉ số người chơi không hợp lệ", 400
    if room['players'][player_index] is not None:
        # Cho phép reconnect nếu đã join
        return render_template('play.html',
                               room_id=room_id,
                               player_index=player_index,
                               max_players=room['num_players'])
    return render_template('play.html', room_id=room_id, player_index=player_index, max_players=room['num_players'])

@app.route('/api/create_room', methods=['POST'])
def create_room():
    data = request.json
    num_players = int(data.get('num_players', 4))
    if not 2 <= num_players <= 10:
        return jsonify({'error': 'Số người chơi phải từ 2 đến 10'}), 400
    
    room_id = str(uuid.uuid4())[:8]
    base_url = request.host_url.rstrip('/')
    
    rooms[room_id] = {
        'num_players': num_players,
        'players': [None] * num_players,
        'phase': 0,
        'max_phase': 0,
        'status': 'waiting_for_projects',     # Trạng thái mới
        'bot_alloc': None,
        'logs': ["Phòng đã tạo. Chờ người chơi submit dự án..."],
        'player_ready': [False] * num_players,   # ready cho submit project
        'deck_ready': [False] * num_players,     # ready cho chọn deck
        'pending_cards': {},
        'phase_energy': [3] * num_players,
        'mulligan_used': [False] * num_players,
        'reaction_hand': [None] * num_players,
        'game_ended': False,
        'player_triggers': [{} for _ in range(num_players)],
        'bot_memory': {bot['id']: {'attractiveness_history': [[] for _ in range(num_players)]} for bot in BOTS},
        'submitted_players': 0                    # Đếm số người đã submit project
    }
    
    join_links = [f"{base_url}/play/{room_id}/{i}" for i in range(num_players)]
    
    return jsonify({
        'room_id': room_id, 
        'join_links': join_links,
        'status': 'waiting_for_projects'
    })

@app.route('/api/submit_project', methods=['POST'])
def submit_project():
    data = request.json
    room_id = data['room_id']
    player_index = data['player_index']
    project_data = data['project']

    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    room = rooms[room_id]

    if player_index >= len(room['players']):
        return jsonify({'error': 'Player index không hợp lệ'}), 400

    if room['players'][player_index] is not None:
        return jsonify({'error': 'Bạn đã submit dự án rồi'}), 400

    # ==================== KHỞI TẠO DỰ ÁN ====================
    project_data.update({
        'trust_scores': {bot['id']: 50 for bot in BOTS},
        'status': 'active',
        'funding_progress': 0.0,
        'total_invested': 0,
        'available_cash': project_data.get('owner_equity', 50000) + project_data.get('loan', 30000),
        'legal_cost_spent': 0,
        'current_phase': 0,
        'hype': project_data.get('hype', 50),
        'transparency': project_data.get('transparency', 50),
        'visibility': project_data.get('visibility', 50),
        'active_deck': None,      # sẽ gán sau
        'reaction_hand': None,
        'current_hand': [],
        'energy_left': 3,
    })

    room['players'][player_index] = project_data
    room['player_ready'][player_index] = True
    room['submitted_players'] += 1

    room['logs'].append(f"✅ Player {player_index + 1} đã submit dự án.")

    # Tự động thông báo nếu đủ người tối thiểu
    if room['submitted_players'] >= 2:
        room['logs'].append(f"Đã có {room['submitted_players']}/{room['num_players']} người chơi submit dự án.")

    return jsonify({
        'ok': True,
        'submitted_count': room['submitted_players'],
        'total_players': room['num_players'],
        'message': 'Dự án đã được gửi thành công!'
    })
@app.route('/api/start_deck_phase', methods=['POST'])
def start_deck_phase():
    data = request.json
    room_id = data['room_id']
    
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    room = rooms[room_id]
    
    if room['status'] != 'waiting_for_projects':
        return jsonify({'error': 'Không thể bắt đầu ở trạng thái hiện tại'}), 400
    
    submitted_count = room['submitted_players']
    if submitted_count < 2:
        return jsonify({'error': f'Chưa đủ người chơi submit dự án (cần ít nhất 2, hiện có {submitted_count})'}), 400

    # Chuyển trạng thái
    room['status'] = 'choosing_deck'
    room['player_ready'] = [False] * room['num_players']   # reset để dùng cho submit deck
    room['logs'].append(f"Host đã force bắt đầu chọn Deck. {submitted_count} người chơi tham gia.")

    return jsonify({
        'ok': True,
        'message': f'Bắt đầu giai đoạn chọn Deck với {submitted_count} dự án.'
    })
@app.route('/api/submit_deck', methods=['POST'])
def submit_deck():
    data = request.json
    room_id = data['room_id']
    player_index = data['player_index']
    active_indices = data['active_indices']
    reaction_indices = data.get('reaction_indices', [])

    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    room = rooms[room_id]

    if room['status'] != 'choosing_deck':
        return jsonify({'error': 'Không phải lúc chọn deck'}), 400

    if len(active_indices) != 22:
        return jsonify({'error': 'Phải chọn đúng 22 active cards'}), 400

    proj = room['players'][player_index]
    proj['active_deck'] = [ACTIVE_CARDS_FULL[i] for i in active_indices]
    proj['reaction_hand'] = [REACTION_CARDS[i].copy() for i in reaction_indices]

    room['deck_ready'][player_index] = True

    # Tự động bắt đầu game nếu tất cả người đã submit deck
    if all(room['deck_ready'][i] for i in range(room['num_players']) if room['players'][i] is not None):
        room['max_phase'] = max(p['max_phase'] for p in room['players'] if p is not None)
        room['bot_alloc'] = [
            {'bot_id': bot['id'], 'perProject': [0] * room['num_players'], 'idle': bot['wealth']} 
            for bot in BOTS
        ]
        room['phase'] = 1
        room['status'] = 'playing'
        room['logs'].append("Tất cả người chơi đã chọn deck. Game chính thức bắt đầu!")

        for idx, p in enumerate(room['players']):
            if p and p.get('active_deck'):
                p['current_hand'] = random.sample(p['active_deck'], min(5, len(p['active_deck'])))
                p['energy_left'] = 3

    return jsonify({'ok': True})


@app.route('/api/host_state', methods=['GET'])
def host_state():
    room_id = request.args.get('room_id')
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    room = rooms[room_id]
    rankings = []
    for i, proj in enumerate(room['players']):
        if proj:
            ended = proj.get('current_phase', 0) >= proj['max_phase']
            if ended:
                metrics = calculate_metrics(proj)
                score = final_score(proj, proj['max_phase'], metrics)
                status = 'ended'
            else:
                metrics = calculate_metrics(proj)
                score = 0
                status = proj.get('status', 'active')
            rankings.append({
                'name': f"Player {i+1}",
                'funding': proj['funding_progress'],
                'hype': proj['hype'],
                'transparency': proj['transparency'],
                'score': score,
                'scale': proj.get('scale', ''),
                'status': status,
                'current_phase': proj.get('current_phase', 0),
                'max_phase': proj['max_phase']
            })
        else:
            rankings.append({'name': f"Player {i+1}", 'funding': 0, 'score': 0, 'status': 'not_joined'})
    all_ended = all(p is None or p.get('current_phase', 0) >= p['max_phase'] for p in room['players'])
    if room['status'] == 'playing' and (room['phase'] > room['max_phase'] or all_ended):
        room['game_ended'] = True
        room['status'] = 'ended'
    return jsonify({
        'status': room['status'],
        'phase': room['phase'],
        'max_phase': room['max_phase'],
        'players_joined': sum(1 for p in room['players'] if p is not None),
        'max_players': room['num_players'],
        'logs': room.get('logs', []),
        'rankings': rankings,
        'all_ready': all(room['player_ready']) if room['status'] == 'playing' else False,
        'game_ended': room.get('game_ended', False)
    })
 return jsonify({
        'status': room['status'],
        'phase': room['phase'],
        'max_phase': room['max_phase'],
        'players_joined': room['submitted_players'],   # quan trọng
        'max_players': room['num_players'],
        'logs': room.get('logs', [])[-40:],
        'rankings': rankings,
        'all_ready': all(room.get('deck_ready', [False]*room['num_players'])[i] for i in range(room['num_players']) if room['players'][i]),
        'can_start_deck': room['status'] == 'waiting_for_projects' and room['submitted_players'] >= 2,
        'submitted_count': room.get('submitted_players', 0)
    })

@app.route('/api/play_card', methods=['POST'])
def play_card():
    data = request.json
    room_id = data.get('room_id')
    player_index = data.get('player_index')
    card_index = data.get('card_index')

    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404

    room = rooms[room_id]
    if room['status'] != 'playing':
        return jsonify({'error': 'Game chưa ở trạng thái chơi'}), 400

    proj = room['players'][player_index] if player_index < len(room['players']) else None
    
    if not proj or proj.get('status') != 'active':
        return jsonify({'error': 'Dự án không hợp lệ hoặc đã kết thúc'}), 400

    hand = proj.get('current_hand', [])
    if not (0 <= card_index < len(hand)):
        return jsonify({'error': 'Lá bài không hợp lệ'}), 400

    card = hand[card_index]

    if proj.get('energy_left', 0) < card.get('cost', 0):
        return jsonify({'error': 'Không đủ Energy'}), 400

    # Lưu và trừ
    import copy
    room['pending_cards'][player_index] = copy.deepcopy(card)
    proj['energy_left'] -= card['cost']
    hand.pop(card_index)

    return jsonify({
        'ok': True,
        'message': f'✅ Đã chơi {card["name"]}'
    })

@app.route('/api/mulligan', methods=['POST'])
def mulligan():
    data = request.json
    room_id = data['room_id']
    player_index = data['player_index']
   if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    room = rooms[room_id]
   if room['status'] != 'playing':
        return jsonify({'error': 'Game chưa bắt đầu'}), 400
   proj = room['players'][player_index]
    if not proj or proj.get('status') != 'active':
        return jsonify({'error': 'Dự án không còn hoạt động'}), 400
   if room['mulligan_used'][player_index]:
        return jsonify({'error': 'Bạn đã dùng Mulligan trong phase này rồi'}), 400
    if proj.get('energy_left', 0) < 1:
        return jsonify({'error': 'Không đủ Energy để Mulligan'}), 400
   # Mulligan logic
    deck = proj['active_deck']
    proj['current_hand'] = random.sample(deck, min(5, len(deck)))
    proj['energy_left'] -= 1
    proj['transparency'] = max(0, proj['transparency'] - 2)
   for bid in proj['trust_scores']:
        proj['trust_scores'][bid] = max(0, proj['trust_scores'][bid] - 1)
   room['mulligan_used'][player_index] = True
   return jsonify({'ok': True, 'message': 'Mulligan thành công! Đã đổi 5 lá bài mới.'})

@app.route('/api/player_ready_phase', methods=['POST'])
def player_ready_phase():
    data = request.json
    room_id = data['room_id']
    player_index = data['player_index']
   if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    room = rooms[room_id]
   if room['status'] != 'playing':
        return jsonify({'error': 'Game chưa bắt đầu'}), 400
   proj = room['players'][player_index]
    if not proj or proj.get('status') != 'active':
        return jsonify({'error': 'Dự án không còn hoạt động'}), 400
   room['player_ready'][player_index] = True
    return jsonify({'ok': True})

@app.route('/api/use_reaction', methods=['POST'])
def use_reaction():
    data = request.json
    room_id = data['room_id']
    player_index = data['player_index']
    reaction_index = data['reaction_index']
   if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    room = rooms[room_id]
   if room['status'] != 'playing':
        return jsonify({'error': 'Not playing'}), 400
   proj = room['players'][player_index]
    if not proj:
        return jsonify({'error': 'Player not found'}), 400
   reaction_hand = proj.get('reaction_hand', [])
    if reaction_index >= len(reaction_hand):
        return jsonify({'error': 'Invalid reaction index'}), 400
   rc = reaction_hand[reaction_index]
    available_reactions = room['player_triggers'][player_index].get('available_reactions', [])
    available_ids = [r['id'] for r in available_reactions]
   if rc['id'] not in available_ids:
        return jsonify({'error': 'Reaction này hiện không thể kích hoạt'}), 400
   eff = rc.get('effect', {})
    cost_percent = rc.get('cost_percent', 0)
   # Áp dụng effects
    if 'transparency' in eff:
        proj['transparency'] = clamp(proj['transparency'] + eff['transparency'], 0, 100)
    if 'hype' in eff:
        proj['hype'] = clamp(proj['hype'] + eff['hype'], 0, 100)
    if 'runway' in eff:
        m = calculate_metrics(proj)
        proj['available_cash'] += eff['runway'] * m.get('monthly_burn', 0)
    if 'reg_risk' in eff and eff['reg_risk'] < 0:
        reduction = (abs(eff['reg_risk']) / 100.0) * proj['target_funding']
        proj['legal_cost_spent'] = max(0, proj['legal_cost_spent'] - reduction)
   if 'trust_all' in eff:
        for bid in proj['trust_scores']:
            proj['trust_scores'][bid] = clamp(proj['trust_scores'][bid] + eff['trust_all'], 0, 100)
    if 'whale_trust' in eff:
        for bot in BOTS:
            if bot['type'] == 'Whale':
                bid = bot['id']
                proj['trust_scores'][bid] = clamp(proj['trust_scores'].get(bid, 50) + eff['whale_trust'], 0, 100)
    if 'sell_pressure_reduce' in eff:
        proj['sell_pressure_reduce'] = eff.get('sell_pressure_reduce', 0.5)
   # Trừ chi phí reaction
    cost = (cost_percent / 100.0) * proj['target_funding']
    proj['available_cash'] = max(0, proj['available_cash'] - cost)
   # Xóa reaction đã dùng
    proj['reaction_hand'].pop(reaction_index)
    room['player_triggers'][player_index]['available_reactions'] = [
        r for r in available_reactions if r['id'] != rc['id']
    ]
   return jsonify({'ok': True, 'message': f'Đã kích hoạt reaction: {rc["name"]}'})

@app.route('/api/run_phase', methods=['POST'])
def run_phase():
    data = request.json
    room_id = data['room_id']
   if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    room = rooms[room_id]
   if room['status'] != 'playing':
        return jsonify({'error': 'Game not active'}), 400
   # Kiểm tra tất cả người chơi còn active đã ready
    active_players_ready = all(
        room['player_ready'][i] for i in range(room['num_players']) 
        if room['players'][i] and room['players'][i].get('status') == 'active'
    )
    if not active_players_ready:
        return jsonify({'error': 'Chưa phải tất cả người chơi đều Ready'}), 400
   phase = room['phase']
    players = room['players']
    logs = []
   # Reset reaction triggers
    for i in range(room['num_players']):
        room['player_triggers'][i] = {'available_reactions': []}
   # ===================== XỬ LÝ TỪNG DỰ ÁN =====================
    for idx, proj in enumerate(players):
        if not proj or proj.get('status') != 'active' or proj.get('current_phase', 0) >= proj.get('max_phase', 999):
            continue
       # Scenario
        scenario = random.choice(SCENARIOS)
        proj['last_scenario'] = scenario['name']
        logs.append(f"Dự án {idx+1}: {scenario['name']}")
       d = scenario['delta']
       if 'price' in d:
            proj['price'] *= (1 + d['price'])
        if 'cogs' in d:
            proj['material'] *= (1 + d['cogs'])
            proj['packaging'] *= (1 + d['cogs'])
            proj['labor'] *= (1 + d['cogs'])                    # ← Đổi từ shipping
        if 'hype' in d:
            proj['hype'] = clamp(proj['hype'] + d['hype'], 0, 100)
        if 'transparency' in d:
            proj['transparency'] = clamp(proj['transparency'] + d['transparency'], 0, 100)
        if 'trust_all' in d:
            for bid in proj['trust_scores']:
                proj['trust_scores'][bid] = clamp(proj['trust_scores'][bid] + d['trust_all'], 0, 100)
        if 'runway' in d:
            m = calculate_metrics(proj)
            proj['available_cash'] += d['runway'] * m.get('monthly_burn', 0)
        if 'legal_cost_percent' in d:
            cost = (d['legal_cost_percent'] / 100) * proj['target_funding']
            proj['legal_cost_spent'] += cost
            proj['available_cash'] -= cost
        if 'reg_risk' in d:
            proj['legal_cost_spent'] += (d['reg_risk'] / 100) * proj['target_funding']
       # Active Card Effect
        if idx in room['pending_cards']:
            card = room['pending_cards'].get(idx)
            if card:
                eff = card.get('effect', {})
                if 'hype' in eff:
                    proj['hype'] = clamp(proj['hype'] + eff['hype'], 0, 100)
                if 'transparency' in eff:
                    proj['transparency'] = clamp(proj['transparency'] + eff['transparency'], 0, 100)
                if 'price_percent' in eff:
                    proj['price'] *= (1 + eff['price_percent'] / 100)
                if 'cogs_percent' in eff:
                    proj['material'] *= (1 + eff['cogs_percent'] / 100)
                    proj['packaging'] *= (1 + eff['cogs_percent'] / 100)
                    proj['labor'] *= (1 + eff['cogs_percent'] / 100)        # ← Đổi từ shipping
                if 'funding_boost_percent' in eff:
                    boost = (eff['funding_boost_percent'] / 100) * proj['target_funding']
                    proj['total_invested'] += boost
                    proj['available_cash'] += boost
                    proj['funding_progress'] = min(1.0, proj['total_invested'] / proj['target_funding'])
                if 'cost_percent' in eff:
                    proj['available_cash'] -= (eff['cost_percent'] / 100) * proj['target_funding']
                if 'visibility' in eff:
                    proj['visibility'] = clamp(proj.get('visibility', 50) + eff['visibility'], 0, 100)
               logs.append(f" → Dự án {idx+1} chơi thẻ {card['name']}")
       # Reaction Trigger Detection
        triggers = []
        for rc in proj.get('reaction_hand', []):
            if rc['trigger'] == 'on_scenario_market_bad' and scenario['cat'] == 'Market':
                if any(k in scenario['name'].lower() for k in ['crisis', 'slow', 'khủng', 'xấu']):
                    triggers.append(rc)
            elif rc['trigger'] == 'on_whale_trust_low' and proj.get('whale_trust', 50) < 30:
                triggers.append(rc)
            elif rc['trigger'] == 'on_transparency_low' and proj['transparency'] < 30:
                triggers.append(rc)
            elif rc['trigger'] == 'on_reg_risk_high':
                reg = (proj['legal_cost_spent'] / proj['target_funding']) * 100 if proj['target_funding'] > 0 else 0
                if reg > 70:
                    triggers.append(rc)
            elif rc['trigger'] == 'on_hype_high' and proj['hype'] > 80:
                triggers.append(rc)
            elif rc['trigger'] == 'on_runway_low':
                m = calculate_metrics(proj)
                if m.get('runway', 999) < 3:
                    triggers.append(rc)
       if triggers:
            room['player_triggers'][idx]['available_reactions'] = triggers
            logs.append(f" → Dự án {idx+1} có {len(triggers)} reaction có thể kích hoạt")
       # Cập nhật phase
        metrics = calculate_metrics(proj)
        proj['funding_progress'] = metrics.get('funding_progress', 0)
        proj['current_phase'] += 1
       if proj['current_phase'] >= proj['max_phase']:
            proj['status'] = 'ended'
            logs.append(f" → Dự án {idx+1} đã kết thúc.")
       logs.append(f" → Funding sau phase: {proj['funding_progress']*100:.1f}%")
   # ===================== BOT INVESTMENT & WITHDRAW (giữ nguyên logic cũ của bạn) =====================
    # ... (phần bot bạn gửi trước đó giữ nguyên, chỉ thay labor nếu có)
   # Cleanup & Next Phase
    room['pending_cards'] = {}
    room['player_ready'] = [False] * room['num_players']
    room['logs'] = logs[-50:]  # Giữ log gần
   room['phase'] += 1
   # Phát bài mới cho phase tiếp theo
    for idx, proj in enumerate(players):
        if proj and proj.get('status') == 'active' and proj.get('current_phase', 0) < proj.get('max_phase', 999):
            proj['current_hand'] = random.sample(proj['active_deck'], min(5, len(proj['active_deck'])))
            proj['energy_left'] = 3
            room['mulligan_used'][idx] = False
   # Kiểm tra kết thúc game
    all_ended = all(p is None or p.get('current_phase', 0) >= p.get('max_phase', 999) for p in players)
    game_ended = (room['phase'] > room['max_phase']) or all_ended
   if game_ended:
        room['game_ended'] = True
        room['status'] = 'ended'
   return jsonify({
        'ended': game_ended,
        'phase': room['phase'] - 1,
        'logs': logs,
        'game_ended': game_ended
    })

@app.route('/api/card_lists', methods=['GET'])
def card_lists():
    """Trả về danh sách tất cả thẻ Active và Reaction cho người chơi chọn deck"""
    try:
        # Tạo bản copy để tránh vô tình sửa dữ liệu gốc
        active_cards = [card.copy() for card in ACTIVE_CARDS_FULL]
        reaction_cards = [card.copy() for card in REACTION_CARDS]
        
        return jsonify({
            'active': active_cards,
            'reaction': reaction_cards,
            'total_active': len(active_cards),
            'total_reaction': len(reaction_cards)
        })
        
    except Exception as e:
        return jsonify({'error': 'Không thể tải danh sách thẻ', 'details': str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    
    print(f"🚀 Server đang chạy tại http://0.0.0.0:{port}")
    print(f"📌 Mode: {'Debug' if app.debug else 'Production'}")
    
    app.run(
        host='0.0.0.0', 
        port=port, 
        debug=False,           # Nên để False khi deploy
        threaded=True          # Tốt hơn cho nhiều request đồng thời
 # Đặt ngoài các route
CARD_CACHE = None

@app.route('/api/card_lists', methods=['GET'])
def card_lists():
    global CARD_CACHE
    if CARD_CACHE is None:
        CARD_CACHE = {
            'active': [card.copy() for card in ACTIVE_CARDS_FULL],
            'reaction': [card.copy() for card in REACTION_CARDS],
            'total_active': len(ACTIVE_CARDS_FULL),
            'total_reaction': len(REACTION_CARDS)
        }
    return jsonify(CARD_CACHE)


