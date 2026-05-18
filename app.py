from flask import Flask, render_template, request, jsonify
import random
import math
import uuid

app = Flask(__name__, template_folder='templates')
app.secret_key = 'startup-game-secret'

# ===================== MINH: CONTENT & SCENARIO DESIGN =====================
# Các sự kiện (scenario) thuộc 4 loại: Market, Internal, External, Regulatory
SCENARIOS = [
    # Market (6)
    {"id":1,"name":"Market Liquidity Improves","cat":"Market","delta":{"price":0.03,"cogs":0,"hype":10,"sentiment":8,"transparency":0,"reg_risk":0}},
    {"id":2,"name":"Investor Risk Appetite Rises","cat":"Market","delta":{"price":0.08,"cogs":-0.02,"hype":22,"sentiment":15,"transparency":0,"reg_risk":0}},
    {"id":3,"name":"Capital Moves to Safer Assets","cat":"Market","delta":{"price":-0.05,"cogs":0.02,"hype":-12,"sentiment":-8,"transparency":0,"reg_risk":0}},
    {"id":4,"name":"Interest Rates Increase","cat":"Market","delta":{"price":-0.08,"cogs":0.04,"hype":-18,"sentiment":-15,"transparency":-3,"reg_risk":3}},
    {"id":5,"name":"Startup Funding Market Slows Down","cat":"Market","delta":{"price":-0.15,"cogs":0.05,"hype":-30,"sentiment":-25,"transparency":-8,"reg_risk":8}},
    {"id":6,"name":"Capital Market Liquidity Crisis","cat":"Market","delta":{"price":-0.25,"cogs":0.1,"hype":-40,"sentiment":-35,"transparency":-15,"reg_risk":15}},
    # Internal (6)
    {"id":7,"name":"Operating Costs Exceed the Budget","cat":"Internal","delta":{"cogs":0.05,"hype":-5,"transparency":-5,"trust_all":-5,"runway":-1}},
    {"id":8,"name":"Product Quality Issues Appear","cat":"Internal","delta":{"cogs":0.1,"hype":-10,"transparency":-10,"trust_all":-10,"runway":-2}},
    {"id":9,"name":"Data leak","cat":"Internal","delta":{"cogs":0,"hype":-15,"transparency":-20,"trust_all":-15,"runway":0}},
    {"id":10,"name":"Key Team Member Leaves","cat":"Internal","delta":{"cogs":0.03,"hype":-10,"transparency":-5,"trust_all":-5,"runway":0}},
    {"id":11,"name":"Important Business Milestone Achieved","cat":"Internal","delta":{"cogs":-0.05,"hype":15,"transparency":10,"trust_all":10,"runway":0}},
    {"id":12,"name":"Internal Control Improves","cat":"Internal","delta":{"cogs":0,"hype":5,"transparency":15,"trust_all":10,"runway":0}},
    # External (6)
    {"id":13,"name":"Competitor Cuts Prices","cat":"External","delta":{"price":-0.05,"marketing_eff":-0.1,"hype":-5,"transparency":0}},
    {"id":14,"name":"Competitor Launches a Better Product","cat":"External","delta":{"price":-0.1,"marketing_eff":-0.2,"hype":-15,"transparency":-5}},
    {"id":15,"name":"Strategic Partnership Announced","cat":"External","delta":{"price":0.05,"marketing_eff":0.15,"hype":15,"transparency":5}},
    {"id":16,"name":"Intellectual Property Dispute","cat":"External","delta":{"price":-0.08,"marketing_eff":-0.15,"hype":-20,"transparency":-10}},
    {"id":17,"name":"Industry Recognition Received","cat":"External","delta":{"price":0.1,"marketing_eff":0.1,"hype":10,"transparency":5}},
    {"id":18,"name":"Rumor of Interest from a Major Investor","cat":"External","delta":{"price":0.15,"marketing_eff":0.05,"hype":25,"transparency":-5}},
    # Regulatory (6)
    {"id":19,"name":"Regulator Requests Additional Documents","cat":"Regulatory","delta":{"reg_risk":25,"transparency":-10,"trust_all":-10,"legal_cost_percent":5}},
    {"id":20,"name":"The company is approved for regulatory Sandbox testing","cat":"Regulatory","delta":{"reg_risk":-30,"transparency":15,"trust_all":15,"legal_cost_percent":-3}},
    {"id":21,"name":"New Policy Supports Financial Innovation","cat":"Regulatory","delta":{"reg_risk":-15,"transparency":5,"trust_all":5,"legal_cost_percent":0}},
    {"id":22,"name":"New Regulation Tightens Fundraising Rules","cat":"Regulatory","delta":{"reg_risk":25,"transparency":-10,"trust_all":-10,"legal_cost_percent":5}},
    {"id":23,"name":"Tax and Reporting Review","cat":"Regulatory","delta":{"reg_risk":10,"transparency":-5,"trust_all":-5,"legal_cost_percent":2}},
    {"id":24,"name":"Independent Compliance Certification","cat":"Regulatory","delta":{"reg_risk":-10,"transparency":10,"trust_all":10,"legal_cost_percent":-2}},
]

# ===================== MINH: CARD ENGINE – ACTIVE CARDS =====================
# Đã loại bỏ tokenomic effects
ACTIVE_CARDS_FULL = [
    {"id":"A1","name":"Marketing Blitz","cost":2,"type":"red","desc":"Run a large campaign to quickly attract attention.","effect":{"hype":25,"transparency":-5,"cost_percent":3}},
    {"id":"A2","name":"Social Media Campaign","cost":3,"type":"red","desc":"Use social media to create strong public interest.","effect":{"hype":40,"transparency":-10,"cost_percent":5}},
    {"id":"A3","name":"Flash Sale","cost":2,"type":"red","desc":"Offer a short-term discount to increase demand.","effect":{"price_percent":-15,"hype":15}},
    {"id":"A4","name":"Influencer Deal","cost":2,"type":"red","desc":"Use an influencer to increase hype and visibility.","effect":{"hype":20,"visibility":15,"cost_percent":2}},
    {"id":"A5","name":"Free Trial Campaign","cost":3,"type":"red","desc":"Let customers try the product before paying.","effect":{"hype":30,"utility":5,"cost_percent":4}},
    {"id":"A6","name":"Investor Buzz Campaign","cost":2,"type":"red","desc":"Create fundraising momentum among investors.","effect":{"hype":20,"funding_boost_percent":5}},
    {"id":"A7","name":"Celebrity Endorsement","cost":2,"type":"red","desc":"Use a famous person to boost public attention.","effect":{"hype":25,"transparency":-3,"cost_percent":4}},
    {"id":"A8","name":"Customer Loyalty Program","cost":3,"type":"red","desc":"Reward repeat customers to keep them engaged.","effect":{"hype":15,"utility":10,"transparency":5}},
    {"id":"A9","name":"Limited Offer","cost":1,"type":"red","desc":"Create urgency with a short-time offer.","effect":{"hype":10,"visibility":5}},
    {"id":"A10","name":"Aggressive Promotion","cost":2,"type":"red","desc":"Push bold promotion to gain fast attention.","effect":{"hype":30,"transparency":-15,"cost_percent":2}},
    {"id":"A11","name":"Pre-sale Discount","cost":2,"type":"red","desc":"Use early discounts to bring in quick cash.","effect":{"price_percent":-10,"funding_boost_percent":10}},
    {"id":"A12","name":"Media Coverage Push","cost":2,"type":"red","desc":"Get media attention for the project.","effect":{"hype":20,"visibility":10,"cost_percent":1}},
    {"id":"A13","name":"Community Engagement Campaign","cost":1,"type":"red","desc":"Keep the community active and interested.","effect":{"hype":15,"transparency":-2}},
    {"id":"A14","name":"Aggressive Pricing Strategy","cost":2,"type":"red","desc":"Lower prices to attract more customers.","effect":{"price_percent":-20,"hype":10}},
    {"id":"D1","name":"Cost Cutting","cost":1,"type":"green","desc":"Reduce unnecessary operating costs.","effect":{"cogs_percent":-3,"transparency":5}},
    {"id":"D2","name":"Community Update","cost":1,"type":"green","desc":"Update investors and customers on progress.","effect":{"hype":5,"transparency":3}},
    {"id":"D3","name":"Third Party Audit","cost":2,"type":"green","desc":"Use an independent review to build credibility.","effect":{"transparency":15,"reg_risk":-10,"cost_percent":5}},
    {"id":"D4","name":"Founder Commitment Pledge","cost":1,"type":"green","desc":"Show that founders are committed long term.","effect":{"transparency":10,"trust_all":5}},
    {"id":"D5","name":"Emergency Fund","cost":2,"type":"green","desc":"Set aside reserve cash for unexpected problems.","effect":{"runway":2,"cost_percent":5}},
    {"id":"D6","name":"Open Financial Report","cost":2,"type":"green","desc":"Share clearer financial information.","effect":{"transparency":20,"cost_percent":2}},
    {"id":"D7","name":"Security Review Program","cost":1,"type":"green","desc":"Check system and data security risks.","effect":{"security":10,"transparency":5}},
    {"id":"D8","name":"Legal Readiness Check","cost":2,"type":"green","desc":"Review legal and compliance documents.","effect":{"reg_risk":-15,"cost_percent":3}},
    {"id":"D9","name":"Slow & Steady","cost":1,"type":"green","desc":"Choose controlled and realistic growth.","effect":{"transparency":5,"hype":2}},
    {"id":"D10","name":"Crisis Management","cost":2,"type":"green","desc":"Reduce damage from a negative event.","effect":{"halve_negative_delta":1,"cost_percent":3}},
    {"id":"D11","name":"Supply Chain Fix","cost":2,"type":"green","desc":"Fix supplier or delivery cost problems.","effect":{"cogs_percent":-5,"transparency":5}},
    {"id":"D12","name":"Investor Call","cost":1,"type":"green","desc":"Answer investor concerns directly.","effect":{"trust_all":10,"cost_percent":1}},
    {"id":"D13","name":"Transparency Report","cost":2,"type":"green","desc":"Explain performance, risks, and issues clearly.","effect":{"transparency":15,"hype":-5}},
    {"id":"D14","name":"Dual Approval Control","cost":1,"type":"green","desc":"Require two approvals for sensitive actions.","effect":{"security":15,"transparency":5}},
    {"id":"T1","name":"Strategic Investor Discount","cost":3,"type":"purple","desc":"Offer better terms to close a major investment.","effect":{"funding_boost_percent":15,"trust_all":-8,"whale_trust":5,"cost_percent":2}},
    {"id":"T2","name":"Investor Protection Reserve","cost":2,"type":"purple","desc":"Set aside funds to reassure investors.","effect":{"funding_boost_percent":-10,"trust_all":15,"utility":10,"cost_percent":10}},
    {"id":"T3","name":"Secondary Offering","cost":3,"type":"purple","desc":"Raise more capital from new investors.","effect":{"funding_boost_percent":20,"trust_all":-15}},
    {"id":"T4","name":"Stakeholder Governance Vote","cost":2,"type":"purple","desc":"Let stakeholders join an important decision.","effect":{"transparency":5,"trust_all":5}},
    {"id":"T5","name":"Customer Retention Program","cost":2,"type":"purple","desc":"Encourage customers to keep using the product.","effect":{"utility":15,"velocity":-0.2}},
    {"id":"T6","name":"Treasury Diversify","cost":2,"type":"purple","desc":"Reduce financial dependence on one source.","effect":{"reg_risk":-10,"trust_all":10}},
    {"id":"T7","name":"Small Share Split","cost":2,"type":"purple","desc":"Allow smaller investors to participate.","effect":{"funding_boost_percent":5,"hype":10}},
    {"id":"T8","name":"Governance Proposal","cost":1,"type":"purple","desc":"Clarify how major decisions are made.","effect":{"transparency":5,"trust_all":5}},
    {"id":"T9","name":"Founder Lock-In Agreement","cost":2,"type":"purple","desc":"Keep founders committed for longer.","effect":{"trust_all":20,"transparency":10,"cost_percent":2}},
    {"id":"T10","name":"Customer Incentive Program","cost":3,"type":"purple","desc":"Encourage customers to use the service more.","effect":{"utility":20,"velocity":-0.3,"cost_percent":5}},
    {"id":"T11","name":"Strategic Partnership","cost":2,"type":"purple","desc":"Work with a credible partner to reduce risk.","effect":{"trust_all":15,"reg_risk":-5,"cost_percent":3}},
    {"id":"T12","name":"Product Value Upgrade","cost":2,"type":"purple","desc":"Improve the product’s practical value.","effect":{"utility":15,"hype":10,"cost_percent":2}},
    {"id":"T13","name":"Loyalty Reward Program","cost":2,"type":"purple","desc":"Reward existing customers or supporters.","effect":{"trust_all":10,"hype":15,"cost_percent":4}},
    {"id":"T14","name":"Equity Swap","cost":3,"type":"purple","desc":"Trade ownership value for quick funding.","effect":{"funding_boost_percent":30,"trust_all":-20}},
]

# ===================== MINH: CARD ENGINE – REACTION CARDS =====================
REACTION_CARDS = [
    {"id":"R1","name":"Lock-up Extension","trigger":"on_bot_withdraw","condition":{"event":"bot_withdraw"},"desc":"Slow withdrawals when investors start leaving.","cost_percent":2,"effect":{"sell_pressure_reduce":0.5}},
    {"id":"R2","name":"Emergency PR","trigger":"on_scenario_market_bad","condition":{"event":"market_bad"},"desc":"Respond quickly to bad market news.","cost_percent":3,"effect":{"halve_negative_delta":1}},
    {"id":"R3","name":"Major Investor Briefing","trigger":"on_whale_trust_low","condition":{"metric":"whale_trust","operator":"<","value":30},"desc":"Rebuild confidence with major investors.","cost_percent":5,"effect":{"whale_trust":10}},
    {"id":"R4","name":"Damage Control","trigger":"on_transparency_low","condition":{"metric":"transparency","operator":"<","value":30},"desc":"Explain problems and restore transparency.","cost_percent":2,"effect":{"transparency":10,"hype":-5}},
    {"id":"R5","name":"Liquidity Support Plan","trigger":"on_circuit_breaker","condition":{"metric":"circuit_breaker_active","operator":"==","value":True},"desc":"Reduce the impact of a liquidity freeze.","cost_percent":8,"effect":{"circuit_breaker_reduce":1}},
    {"id":"R6","name":"Legal Emergency","trigger":"on_reg_risk_high","condition":{"metric":"reg_risk","operator":">","value":70},"desc":"Handle urgent legal or compliance risk.","cost_percent":4,"effect":{"reg_risk":-20}},
    {"id":"R7","name":"Security Patch","trigger":"on_security_low","condition":{"metric":"security","operator":"<","value":30},"desc":"Fix urgent security weaknesses.","cost_percent":3,"effect":{"security":15}},
    {"id":"R8","name":"Expectation Management","trigger":"on_hype_high","condition":{"metric":"hype","operator":">","value":80},"desc":"Control unrealistic public expectations.","cost_percent":1,"effect":{"hype":-15,"transparency":5}},
    {"id":"R9","name":"Investor Assurance","trigger":"on_trust_low","condition":{"metric":"min_bot_trust","operator":"<","value":20},"desc":"Reassure worried investors.","cost_percent":2,"effect":{"trust_all":5}},
    {"id":"R10","name":"Runway Boost","trigger":"on_runway_low","condition":{"metric":"runway","operator":"<","value":3},"desc":"Extend survival time during cash pressure.","cost_percent":10,"effect":{"runway":3}},
]

def get_condition_value(project, metric):
    if metric == "runway":
        return calculate_metrics(project)["runway"]

    if metric == "min_bot_trust":
        return min(project.get("trust_scores", {0: 50}).values())

    if metric == "whale_trust":
        whale_scores = [
            project["trust_scores"].get(bot["id"], 50)
            for bot in BOTS
            if bot["type"] == "Whale"
        ]
        return sum(whale_scores) / len(whale_scores) if whale_scores else 50

    return project.get(metric)


def check_condition(project, condition):
    if not condition:
        return True

    if "event" in condition:
        return condition["event"] in project.get("active_events", [])

    metric = condition.get("metric")
    operator = condition.get("operator")
    target = condition.get("value")

    current_value = get_condition_value(project, metric)

    if current_value is None:
        return False

    if operator == "<":
        return current_value < target
    if operator == ">":
        return current_value > target
    if operator == "<=":
        return current_value <= target
    if operator == ">=":
        return current_value >= target
    if operator == "==":
        return current_value == target

    return False


def get_available_reactions(project):
    available = []

    for card in project.get("reaction_hand", []):
        if check_condition(project, card.get("condition")):
            available.append(card)

    return available
# ===================== JIN: AI BOT GENERATION =====================
random.seed(42)
BOTS = []
for i in range(1, 201):
    bot_type = random.choices(["FOMO","Value Hunter","Whale","Random"], weights=[50,30,10,10])[0]
    wealth_class = random.choices(["small","medium","large"], weights=[40,40,20])[0]
    wealth = {"small":random.randint(10000,50000), "medium":random.randint(100000,500000), "large":random.randint(500000,2000000)}[wealth_class]
    hype_sens = round(random.uniform(1.5, 2.5), 2)   # tăng độ nhạy hype
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

# ===================== PHÚC: METRICS & SCORE SYSTEM =====================
def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def calculate_metrics(proj):
    # Tính toán các chỉ số cốt lõi: gross margin, burn rate, growth, intrinsic
    ch_fees = (proj["fee_ecom"] + proj["fee_retail"] + proj["fee_direct"]) / 100.0
    price_real = proj["price"] * (1 - ch_fees)
    cogs_unit = proj["material"] + proj["packaging"] + proj["shipping"] + proj["defect_rate"]*(proj["material"]+proj["packaging"]+proj["shipping"])
    gm = (price_real - cogs_unit)/price_real if price_real>0 else 0
    monthly_burn = proj["fixed_cost"] + proj["marketing_cost"] + (proj["loan"] * proj["interest_rate"]/100 /12)
    burn_rate = monthly_burn / proj["target_funding"]
    growth = (proj["units_m6"]/proj["units_m1"]) - 1 if proj["units_m1"]>0 else 0
    unit_econ = clamp(20 + 20*(1 - math.exp(-5*(gm-0.2)/0.6)), 20, 40) if gm>0.2 else 20
    burn_score = clamp(10 + 20*(1 - math.exp(-4*(0.3-burn_rate)/0.25)), 10, 30) if burn_rate<0.3 else 10
    scal_score = clamp(10 + 20*(1 - math.exp(-3*growth/0.5)), 10, 30) if growth>0 else 10
    intrinsic = unit_econ + burn_score + scal_score

    # ROI động dựa trên doanh thu và P/S ratio
    total_invested = proj.get("total_invested", 0)
    revenue_year = proj["units_m6"] * 12 * price_real
    ps_ratio = 5.0
    hype = proj.get("hype", 50)
    if hype > 70:
        ps_ratio += 2
    elif hype < 30:
        ps_ratio -= 1
    if growth > 0.5:
        ps_ratio += 1.5
    elif growth < -0.2:
        ps_ratio -= 1
    ps_ratio = max(1.5, min(15, ps_ratio))
    estimated_valuation = revenue_year * ps_ratio
    if total_invested > 0:
        raw_roi = ((estimated_valuation - total_invested) / total_invested) * 100
        raw_roi = max(0, raw_roi)
    else:
        raw_roi = 0
    roi_norm = min(100, 20 * math.log10(raw_roi + 1))

    # Valuation sanity (dùng estimated_valuation)
    mult = estimated_valuation / revenue_year if revenue_year > 0 else 1000
    if mult < 1:
        val_score = 30 - (1-mult)/1*30
    elif mult <= 3:
        val_score = 80 + (mult-1)/2*20
    elif mult <= 5:
        val_score = 80 - (mult-3)/2*40
    else:
        val_score = max(0, 40 - (mult-5)/2*40)
    val_score = clamp(val_score, 0, 100)

    # Bỏ tokenomic, chỉ giữ reg_risk
    base_reg = 20 if proj.get("has_license", False) else 80
    if proj.get("legal_cost_spent", 0) >= 0.05 * proj["target_funding"]:
        base_reg += 20
    reg_risk = clamp(base_reg - proj["transparency"] / 10, 0, 100)

    avail_cash = proj.get("available_cash", proj["owner_equity"] + proj["loan"])
    runway = math.floor(avail_cash / monthly_burn) if monthly_burn > 0 else 999
    liquidity = 100  # tạm thời set 100, không dùng tokenomic

    return {
        "intrinsic": intrinsic,
        "valuation_sanity": val_score,
        "roi_norm": roi_norm,
        "growth": growth,
        "monthly_burn": monthly_burn,
        "available_cash": avail_cash,
        "runway": runway,
        "liquidity": liquidity,
        "funding_progress": proj.get("funding_progress", 0),
        "estimated_valuation": estimated_valuation,
        "raw_roi": raw_roi
    }

# ===================== JIN: ATTRACTIVENESS & MEMORY DECAY =====================
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
    if total_w==0: return 0
    raw_A = (raw/total_w)*100
    if metrics["valuation_sanity"] < 40:
        raw_A = max(0, raw_A - (40-metrics["valuation_sanity"])*1.5)
    trust = project["trust_scores"].get(bot["id"], 50)
    noise = random.uniform(-5,5) if bot["type"]!="Random" else random.uniform(-10,10)
    return raw_A * (trust/100) + noise

# ===================== PHÚC: FINAL SCORE (CÓ THỂ ĐIỀU CHỈNH) =====================
def final_score(proj, phases_used, metrics):
    if proj["funding_progress"] < 0.5:
        return 0
    funding_score = proj["funding_progress"] * 30
    speed_score = (100 - phases_used) * 0.2
    roi_score = min(30, max(0, (metrics["roi_norm"]/100)*30))
    trans_score = (proj["transparency"]/100)*20
    raw = funding_score + speed_score + roi_score + trans_score
    perf_phase = raw / phases_used if phases_used>0 else 0
    return perf_phase * proj.get("scale_factor", 1.0) * (1 + proj["funding_progress"])

# ===================== JIN: BOT PHASE MANAGEMENT =====================
def get_bots_for_phase(phase, total_bots=200):
    ratio = min(1.0, phase * 0.2)
    count = int(total_bots * ratio)
    return BOTS[:count]

# ===================== PHÚC: GAME CORE & FLOW SYSTEM =====================
# Quản lý phòng và trạng thái game
rooms = {}

# ===================== KHANH: API & ROUTING =====================
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
        return "Slot này đã có người chơi", 400
    return render_template('play.html', room_id=room_id, player_index=player_index, max_players=room['num_players'])

@app.route('/api/create_room', methods=['POST'])
def create_room():
    data = request.json
    num_players = data.get('num_players', 4)
    if not isinstance(num_players, int) or num_players < 2 or num_players > 10:
        return jsonify({'error': 'Số người chơi phải từ 2 đến 10'}), 400
    room_id = str(uuid.uuid4())[:8]
    base_url = request.host_url.rstrip('/')
    join_links = [f"{base_url}/play/{room_id}/{i}" for i in range(num_players)]
    rooms[room_id] = {
        'num_players': num_players,
        'players': [None] * num_players,
        'phase': 0,
        'max_phase': 0,
        'status': 'waiting',
        'bot_alloc': None,
        'logs': [],
        'player_ready': [False] * num_players,
        'pending_cards': {},
        'phase_energy': [3] * num_players,
        'mulligan_used': [False] * num_players,
        'reaction_hand': [None] * num_players,
        'game_ended': False,
        'player_triggers': [{} for _ in range(num_players)],
        'bot_memory': {bot['id']: {'attractiveness_history': [[] for _ in range(num_players)]} for bot in BOTS}
    }
    return jsonify({'room_id': room_id, 'join_links': join_links})

@app.route('/api/submit_project', methods=['POST'])
def submit_project():
    data = request.json
    room_id = data['room_id']
    player_index = data['player_index']
    project_data = data['project']
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    room = rooms[room_id]
    if player_index >= len(room['players']) or room['players'][player_index] is not None:
        return jsonify({'error': 'Slot taken'}), 400
    # Khởi tạo project (bỏ tokenomic)
    project_data['trust_scores'] = {bot['id']: 50 for bot in BOTS}
    project_data['status'] = 'active'
    project_data['funding_progress'] = 0
    project_data['total_invested'] = 0
    project_data['available_cash'] = project_data['owner_equity'] + project_data['loan']
    project_data['legal_cost_spent'] = 0
    project_data['current_phase'] = 0
    project_data['max_phase'] = project_data.get('max_phase', 5)
    project_data['hype'] = project_data.get('hype', 50)
    project_data['transparency'] = project_data.get('transparency', 50)
    project_data['visibility'] = project_data.get('visibility', 50)
    room['players'][player_index] = project_data
    room['player_ready'][player_index] = True
    if all(p is not None for p in room['players']):
        room['status'] = 'choosing_deck'
        room['player_ready'] = [False] * room['num_players']
    return jsonify({'ok': True})

@app.route('/api/submit_deck', methods=['POST'])
def submit_deck():
    data = request.json
    room_id = data['room_id']
    player_index = data['player_index']
    active_indices = data['active_indices']
    reaction_indices = data['reaction_indices']
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    room = rooms[room_id]
    if len(active_indices) != 22:
        return jsonify({'error': 'Phải chọn đúng 22 active cards'}), 400
    if len(reaction_indices) > 3:
        return jsonify({'error': 'Tối đa 3 reaction cards'}), 400
    proj = room['players'][player_index]
    proj['active_deck'] = [ACTIVE_CARDS_FULL[i] for i in active_indices]
    proj['reaction_hand'] = [REACTION_CARDS[i].copy() for i in reaction_indices]
    room['player_ready'][player_index] = True
    if all(room['player_ready']):
        max_phase = max(p['max_phase'] for p in room['players'])
        room['max_phase'] = max_phase
        bot_alloc = [{'bot_id': bot['id'], 'perProject': [0] * room['num_players'], 'idle': bot['wealth']} for bot in BOTS]
        room['bot_alloc'] = bot_alloc
        room['phase'] = 1
        room['status'] = 'playing'
        room['player_ready'] = [False] * room['num_players']
        room['pending_cards'] = {}
        room['phase_energy'] = [3] * room['num_players']
        room['mulligan_used'] = [False] * room['num_players']
        for idx, proj in enumerate(room['players']):
            if proj:
                deck = proj['active_deck']
                proj['current_hand'] = random.sample(deck, min(5, len(deck)))
                proj['energy_left'] = 3
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
                proj_status = 'ended'
            else:
                metrics = calculate_metrics(proj)
                score = 0
                proj_status = proj.get('status', 'active')
            rankings.append({
                'name': f"Player {i+1}",
                'funding': proj['funding_progress'],
                'hype': proj['hype'],
                'transparency': proj['transparency'],
                'score': score,
                'scale': proj.get('scale', 1),
                'status': proj_status,
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
        'all_ready': all(room['player_ready']) if room['status']=='playing' else False,
        'game_ended': room.get('game_ended', False)
    })

@app.route('/api/player_state', methods=['GET'])
def player_state():
    room_id = request.args.get('room_id')
    player_index = int(request.args.get('player_index', -1))
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    room = rooms[room_id]
    if player_index < 0 or player_index >= len(room['players']) or room['players'][player_index] is None:
        return jsonify({'error': 'Player not found'}), 404
    proj = room['players'][player_index]
    metrics = calculate_metrics(proj)
    investors = []
    if room['bot_alloc']:
        for alloc in room['bot_alloc']:
            amount = alloc['perProject'][player_index]
            if amount > 0:
                bot = next((b for b in BOTS if b['id'] == alloc['bot_id']), None)
                if bot:
                    investors.append({'type': bot['type'], 'amount': amount})
    ended = proj.get('current_phase', 0) >= proj['max_phase']
    final_score_value = 0
    if ended:
        final_score_value = final_score(proj, proj['max_phase'], metrics)
    triggers = room['player_triggers'][player_index] if player_index < len(room['player_triggers']) else {}
    return jsonify({
        'status': room['status'],
        'phase': room['phase'],
        'last_scenario': proj.get('last_scenario', 'Chưa có sự kiện'),
        'metrics': metrics,
        'hype': proj['hype'],
        'transparency': proj['transparency'],
        'hand': proj.get('current_hand', []),
        'energy_left': proj.get('energy_left', 3),
        'mulligan_used': room['mulligan_used'][player_index],
        'investors': investors,
        'funding_progress': proj['funding_progress'],
        'available_cash': metrics['available_cash'],
        'reaction_hand': proj.get('reaction_hand', []),
        'game_ended': room.get('game_ended', False),
        'ended': ended,
        'final_score': final_score_value,
        'triggers': triggers.get('available_reactions', [])
    })

@app.route('/api/play_card', methods=['POST'])
def play_card():
    data = request.json
    room_id = data['room_id']
    player_index = data['player_index']
    card_index = data['card_index']
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    room = rooms[room_id]
    if room['status'] != 'playing':
        return jsonify({'error': 'Game not in playing'}), 400
    proj = room['players'][player_index]
    if card_index >= len(proj['current_hand']):
        return jsonify({'error': 'Invalid card'}), 400
    card = proj['current_hand'][card_index]
    cost = card['cost']
    if proj['energy_left'] < cost:
        return jsonify({'error': 'Not enough energy'}), 400
    room['pending_cards'][player_index] = card
    proj['energy_left'] -= cost
    proj['current_hand'].pop(card_index)
    return jsonify({'ok': True})

@app.route('/api/mulligan', methods=['POST'])
def mulligan():
    data = request.json
    room_id = data['room_id']
    player_index = data['player_index']
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    room = rooms[room_id]
    if room['status'] != 'playing':
        return jsonify({'error': 'Not in game'}), 400
    proj = room['players'][player_index]
    if room['mulligan_used'][player_index]:
        return jsonify({'error': 'Already used'}), 400
    if proj['energy_left'] < 1:
        return jsonify({'error': 'Not enough energy'}), 400
    deck = proj['active_deck']
    proj['current_hand'] = random.sample(deck, min(3, len(deck)))
    proj['energy_left'] -= 1
    proj['transparency'] = max(0, proj['transparency'] - 2)
    for bid in proj['trust_scores']:
        proj['trust_scores'][bid] = max(0, proj['trust_scores'][bid] - 1)
    room['mulligan_used'][player_index] = True
    return jsonify({'ok': True})

@app.route('/api/player_ready_phase', methods=['POST'])
def player_ready_phase():
    data = request.json
    room_id = data['room_id']
    player_index = data['player_index']
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    room = rooms[room_id]
    if room['status'] != 'playing':
        return jsonify({'error': 'Not playing'}), 400
    room['player_ready'][player_index] = True
    return jsonify({'ok': True})

# ===================== JIN: REACTION ENGINE =====================
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
    if reaction_index >= len(proj.get('reaction_hand', [])):
        return jsonify({'error': 'Invalid reaction'}), 400
    rc = proj['reaction_hand'][reaction_index]
    available_ids = [r['id'] for r in room['player_triggers'][player_index].get('available_reactions', [])]
    if rc['id'] not in available_ids:
        return jsonify({'error': 'Reaction not available now'}), 400
    eff = rc['effect']
    # Áp dụng các effect
    if 'transparency' in eff:
        proj['transparency'] = clamp(proj['transparency'] + eff['transparency'], 0, 100)
    if 'hype' in eff:
        proj['hype'] = clamp(proj['hype'] + eff['hype'], 0, 100)
    if 'runway' in eff:
        m = calculate_metrics(proj)
        proj['available_cash'] += eff['runway'] * m['monthly_burn']
    if 'reg_risk' in eff:
        proj['legal_cost_spent'] -= (eff['reg_risk']/100) * proj['target_funding'] if eff['reg_risk'] < 0 else 0
    if 'trust_all' in eff:
        for bid in proj['trust_scores']:
            proj['trust_scores'][bid] = clamp(proj['trust_scores'][bid] + eff['trust_all'], 0, 100)
    if 'whale_trust' in eff:
        for bot in BOTS:
            if bot['type'] == 'Whale':
                proj['trust_scores'][bot['id']] = clamp(proj['trust_scores'].get(bot['id'], 50) + eff['whale_trust'], 0, 100)
    if 'trust_single' in eff:
        min_bid = min(proj['trust_scores'], key=proj['trust_scores'].get)
        proj['trust_scores'][min_bid] = clamp(proj['trust_scores'][min_bid] + eff['trust_single'], 0, 100)
    if 'sell_pressure_reduce' in eff:
        proj['sell_pressure_reduce'] = eff['sell_pressure_reduce']
    # Trừ chi phí
    proj['available_cash'] -= (rc['cost_percent']/100) * proj['target_funding']
    proj['reaction_hand'].pop(reaction_index)
    room['player_triggers'][player_index]['available_reactions'] = [
        r for r in room['player_triggers'][player_index]['available_reactions'] if r['id'] != rc['id']
    ]
    return jsonify({'ok': True})

# ===================== PHÚC: GAME CORE – RUN PHASE (FLOW) =====================
@app.route('/api/run_phase', methods=['POST'])
def run_phase():
    data = request.json
    room_id = data['room_id']
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    room = rooms[room_id]
    if room['status'] != 'playing':
        return jsonify({'error': 'Game not active'}), 400
    if not all(room['player_ready']):
        return jsonify({'error': 'Not all players ready'}), 400
    
    phase = room['phase']
    players = room['players']
    logs = []
    # Reset triggers
    for i in range(room['num_players']):
        room['player_triggers'][i] = {'available_reactions': []}
    
    # ===================== MINH: XỬ LÝ SCENARIO & ACTIVE CARDS =====================
    for idx, proj in enumerate(players):
        if not proj or proj.get('current_phase', 0) >= proj['max_phase']:
            continue
        # Chọn scenario ngẫu nhiên
        scenario = random.choice(SCENARIOS)
        proj['last_scenario'] = scenario['name']
        logs.append(f"Dự án {idx+1}: {scenario['name']}")
        d = scenario['delta']
        if 'price' in d:
            proj['price'] *= (1 + d['price'])
        if 'cogs' in d:
            proj['material'] *= (1 + d['cogs'])
            proj['packaging'] *= (1 + d['cogs'])
            proj['shipping'] *= (1 + d['cogs'])
        if 'hype' in d:
            proj['hype'] = clamp(proj['hype'] + d['hype'], 0, 100)
        if 'transparency' in d:
            proj['transparency'] = clamp(proj['transparency'] + d['transparency'], 0, 100)
        if 'trust_all' in d:
            for bid in proj['trust_scores']:
                proj['trust_scores'][bid] = clamp(proj['trust_scores'][bid] + d['trust_all'], 0, 100)
        if 'runway' in d:
            metrics_before = calculate_metrics(proj)
            proj['available_cash'] += d['runway'] * metrics_before['monthly_burn']
        if 'legal_cost_percent' in d:
            cost = (d['legal_cost_percent']/100) * proj['target_funding']
            proj['legal_cost_spent'] += cost
            proj['available_cash'] -= cost
        if 'reg_risk' in d:
            proj['legal_cost_spent'] += (d['reg_risk']/100) * proj['target_funding']
        
        # Áp dụng thẻ active
        if idx in room['pending_cards']:
            card = room['pending_cards'][idx]
            if card:
                eff = card['effect']
                if 'hype' in eff:
                    proj['hype'] = clamp(proj['hype'] + eff['hype'], 0, 100)
                if 'transparency' in eff:
                    proj['transparency'] = clamp(proj['transparency'] + eff['transparency'], 0, 100)
                if 'price_percent' in eff:
                    proj['price'] *= (1 + eff['price_percent']/100)
                if 'cogs_percent' in eff:
                    proj['material'] *= (1 + eff['cogs_percent']/100)
                    proj['packaging'] *= (1 + eff['cogs_percent']/100)
                    proj['shipping'] *= (1 + eff['cogs_percent']/100)
                if 'funding_boost_percent' in eff:
                    boost = (eff['funding_boost_percent']/100) * proj['target_funding']
                    proj['total_invested'] += boost
                    proj['available_cash'] += boost
                    proj['funding_progress'] = min(1.0, proj['total_invested']/proj['target_funding'])
                if 'cost_percent' in eff:
                    proj['available_cash'] -= (eff['cost_percent']/100) * proj['target_funding']
                if 'visibility' in eff:
                    proj['visibility'] = clamp(proj.get('visibility', 50) + eff['visibility'], 0, 100)
                logs.append(f"  → Dự án {idx+1} chơi thẻ {card['name']}")
        # ===================== MINH: XÁC ĐỊNH REACTION TRIGGERS =====================
        triggers = []
        for rc in proj.get('reaction_hand', []):
            trigger = rc['trigger']
            if trigger == 'on_scenario_market_bad' and scenario['cat'] == 'Market' and any(k in scenario['name'] for k in ['xấu','Khủng hoảng']):
                triggers.append(rc)
            elif trigger == 'on_whale_trust<30':
                whale_trust = [proj['trust_scores'].get(bot['id'], 50) for bot in BOTS if bot['type']=='Whale']
                if whale_trust and sum(whale_trust)/len(whale_trust) < 30:
                    triggers.append(rc)
            elif trigger == 'on_transparency<30' and proj['transparency'] < 30:
                triggers.append(rc)
            elif trigger == 'on_reg_risk>70':
                reg = (proj['legal_cost_spent'] / proj['target_funding']) * 100 if proj['target_funding']>0 else 0
                if reg > 70:
                    triggers.append(rc)
            elif trigger == 'on_hype>80' and proj['hype'] > 80:
                triggers.append(rc)
            elif trigger == 'on_trust_any_bot<20':
                if any(t < 20 for t in proj['trust_scores'].values()):
                    triggers.append(rc)
            elif trigger == 'on_runway<3':
                m = calculate_metrics(proj)
                if m['runway'] < 3:
                    triggers.append(rc)
        if triggers:
            room['player_triggers'][idx]['available_reactions'] = triggers
            logs.append(f"  → Dự án {idx+1} có {len(triggers)} reaction có thể kích hoạt")
        
        # Cập nhật tiến độ
        metrics = calculate_metrics(proj)
        proj['funding_progress'] = metrics['funding_progress']
        proj['current_phase'] += 1
        if proj['current_phase'] >= proj['max_phase']:
            proj['status'] = 'ended'
            logs.append(f"  → Dự án {idx+1} kết thúc (đã qua {proj['max_phase']} phases).")
        logs.append(f"  → Funding sau phase: {proj['funding_progress']*100:.1f}%")
    
    # ===================== JIN: AI BOT XỬ LÝ ĐẦU TƯ VÀ RÚT VỐN =====================
    active_bots = get_bots_for_phase(phase)
    logs.append(f"Phase {phase}: Có {len(active_bots)} bot hoạt động")
    bot_alloc = room['bot_alloc']
    A = {}
    for bot in active_bots:
        for idx, proj in enumerate(players):
            if not proj or proj.get('status') != 'active' or proj['funding_progress'] >= 1 or proj.get('current_phase',0) >= proj['max_phase']:
                A[(bot['id'], idx)] = -1e9
            else:
                metrics = calculate_metrics(proj)
                hist = room['bot_memory'][bot['id']]['attractiveness_history'][idx]
                current_attr = attractiveness(proj, bot, metrics)
                if hist:
                    weighted_avg = sum((i+1)*val for i, val in enumerate(hist)) / sum(range(1, len(hist)+1))
                    decay = bot['memory_decay_rate']
                    final_attr = (1-decay)*current_attr + decay*weighted_avg
                else:
                    final_attr = current_attr
                hist.append(current_attr)
                if len(hist) > 5:
                    hist.pop(0)
                A[(bot['id'], idx)] = final_attr
    
    # Rút vốn
    for bot in active_bots:
        best_idx = max(range(len(players)), key=lambda i: A.get((bot['id'], i), -1e9))
        alloc_entry = next(entry for entry in bot_alloc if entry['bot_id'] == bot['id'])
        for idx in range(len(players)):
            invested = alloc_entry['perProject'][idx]
            if invested == 0:
                continue
            if players[idx].get('status') != 'active' or players[idx].get('current_phase',0) >= players[idx]['max_phase']:
                if invested > 0:
                    players[idx]['available_cash'] -= invested
                    alloc_entry['idle'] += invested
                    alloc_entry['perProject'][idx] = 0
                    logs.append(f"🐋 Bot {bot['type']} rút toàn bộ {invested:.0f} từ dự án {idx+1} (kết thúc)")
                continue
            diff = A.get((bot['id'], best_idx), -1e9) - A.get((bot['id'], idx), -1e9)
            if diff > 15:
                withdraw_ratio = 1.0
            elif diff > 5:
                withdraw_ratio = 0.3
            else:
                withdraw_ratio = 0.0
            max_ratio = min(0.6, 0.2 + (phase-1)*0.05)
            desired = invested * withdraw_ratio
            max_withdraw = invested * max_ratio
            actual = min(desired, max_withdraw)
            if actual > 0:
                if actual <= players[idx]['available_cash']:
                    players[idx]['available_cash'] -= actual
                    alloc_entry['perProject'][idx] -= actual
                    alloc_entry['idle'] += actual
                    logs.append(f"🐋 Bot {bot['type']} rút {actual:.0f} từ dự án {idx+1}")
                else:
                    players[idx]['status'] = 'bankrupt'
                    players[idx]['funding_progress'] = 0
                    logs.append(f"💀 Dự án {idx+1} PHÁ SẢN!")
    
    # Đầu tư softmax
    for bot in active_bots:
        alloc_entry = next(entry for entry in bot_alloc if entry['bot_id'] == bot['id'])
        idle = alloc_entry['idle']
        if idle <= 0:
            continue
        candidates = [i for i,p in enumerate(players) if p and p['status']=='active' and p['funding_progress']<1 and p.get('current_phase',0) < p['max_phase']]
        if not candidates:
            continue
        attrs = [A.get((bot['id'], i), -1e9) for i in candidates]
        min_a = min(attrs)
        shifted = [max(0, a - min_a + 0.01) for a in attrs]
        sum_exp = sum(math.exp(a/20) for a in shifted)
        probs = [math.exp(a/20)/sum_exp for a in shifted]
        remaining = idle
        for _ in range(5):
            if remaining <= 0:
                break
            for j, idx in enumerate(candidates):
                invest = remaining * probs[j]
                cap = min(invest, players[idx]['target_funding']*0.25 - players[idx]['total_invested'])
                if phase == 1:
                    cap = min(cap, players[idx]['target_funding']*0.2 - players[idx]['total_invested'])
                if cap > 0:
                    players[idx]['total_invested'] += cap
                    players[idx]['available_cash'] += cap
                    players[idx]['funding_progress'] = min(1.0, players[idx]['total_invested']/players[idx]['target_funding'])
                    alloc_entry['perProject'][idx] += cap
                    remaining -= cap
                    logs.append(f"💸 Bot {bot['type']} đầu tư {cap:.0f} vào dự án {idx+1}")
        alloc_entry['idle'] = remaining
    
    # Dọn dẹp sau phase
    room['pending_cards'] = {}
    room['player_ready'] = [False] * room['num_players']
    room['phase'] += 1
    room['logs'] = logs
    
    all_ended = all(p is None or p.get('current_phase',0) >= p['max_phase'] for p in players)
    game_ended = (room['phase'] > room['max_phase']) or all_ended
    if game_ended:
        room['game_ended'] = True
        room['status'] = 'ended'
    else:
        for idx, proj in enumerate(players):
            if proj and proj['status'] == 'active' and proj['funding_progress'] < 1 and proj.get('current_phase',0) < proj['max_phase']:
                deck = proj['active_deck']
                proj['current_hand'] = random.sample(deck, min(5, len(deck)))
                proj['energy_left'] = 3
                room['mulligan_used'][idx] = False
    return jsonify({
        'ended': game_ended,
        'phase': room['phase'],
        'logs': logs,
        'game_ended': game_ended
    })

# ===================== MINH: CARD LISTS API =====================
@app.route('/api/card_lists', methods=['GET'])
def card_lists():
    return jsonify({
        'active': ACTIVE_CARDS_FULL,
        'reaction': REACTION_CARDS
    })

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

