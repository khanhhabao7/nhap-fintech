# ===================================================================
# STARTUP GAME - TOÀN BỘ CODE GỘP TRONG MỘT FILE
# PHÂN CÔNG:
# - MINH: Dữ liệu cố định, Card Engine, Utils
# - PHÚC: Metrics, Game Controller (process_phase, reset_for_next_phase)
# - JIN: Attractiveness, Bot AI, Reaction Manager
# - KHANH: API Routing, Flask app, Rooms management
# - DƯƠNG: templates/host.html, templates/play.html (riêng)
# ===================================================================

from flask import Flask, render_template, request, jsonify
import random
import math
import uuid

app = Flask(__name__, template_folder='templates')
app.secret_key = 'startup-game-secret'

# ===================== MINH: DỮ LIỆU CỐ ĐỊNH =====================
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
ACTIVE_CARDS_FULL = [
    # Hot Pink cards (Attack)
    {"id":"A1","name":"Marketing Blitz","cost":2,"type":"hotpink","desc":"Tăng Hype 25, giảm Transparency 5","effect":{"hype":25,"transparency":-5}},
    {"id":"A2","name":"Viral Campaign","cost":3,"type":"hotpink","desc":"Tăng Hype 40, giảm Transparency 10","effect":{"hype":40,"transparency":-10}},
    {"id":"A3","name":"Flash Sale","cost":2,"type":"hotpink","desc":"Giảm giá 15%, tăng Hype 15","effect":{"price_percent":-15,"hype":15}},
    {"id":"A4","name":"Influencer Deal","cost":2,"type":"hotpink","desc":"Tăng Hype 20, Visibility 15","effect":{"hype":20,"visibility":15}},
    {"id":"A6","name":"FOMO Campaign","cost":2,"type":"hotpink","desc":"Tăng Hype 20, Funding 5%","effect":{"hype":20,"funding_boost_percent":5}},
    {"id":"A7","name":"Celebrity Endorsement","cost":2,"type":"hotpink","desc":"Tăng Hype 25, giảm Transparency 3","effect":{"hype":25,"transparency":-3}},
    {"id":"A9","name":"Limited Offer","cost":1,"type":"hotpink","desc":"Tăng Hype 10, Visibility 5","effect":{"hype":10,"visibility":5}},
    {"id":"A10","name":"Shill Army","cost":2,"type":"hotpink","desc":"Tăng Hype 30, giảm Transparency 15","effect":{"hype":30,"transparency":-15}},
    {"id":"A11","name":"Pre-sale Discount","cost":2,"type":"hotpink","desc":"Giảm giá 10%, tăng Funding 10%","effect":{"price_percent":-10,"funding_boost_percent":10}},
    {"id":"A12","name":"Media Blast","cost":2,"type":"hotpink","desc":"Tăng Hype 20, Visibility 10","effect":{"hype":20,"visibility":10}},
    {"id":"A13","name":"Meme Marketing","cost":1,"type":"hotpink","desc":"Tăng Hype 15, giảm Transparency 2","effect":{"hype":15,"transparency":-2}},
    {"id":"A14","name":"Aggressive Pricing","cost":2,"type":"hotpink","desc":"Giảm giá 20%, tăng Hype 10","effect":{"price_percent":-20,"hype":10}},
    
    # Baby Blue cards (Defense)
    {"id":"D1","name":"Cost Cutting","cost":1,"type":"babyblue","desc":"Giảm COGS 3%, tăng Transparency 5","effect":{"cogs_percent":-3,"transparency":5}},
    {"id":"D2","name":"Community Update","cost":1,"type":"babyblue","desc":"Tăng Hype 5, Transparency 3","effect":{"hype":5,"transparency":3}},
    {"id":"D3","name":"Third Party Audit","cost":2,"type":"babyblue","desc":"Tăng Transparency 15, giảm rủi ro","effect":{"transparency":15,"reg_risk":-10}},
    {"id":"D4","name":"Vesting Pledge","cost":1,"type":"babyblue","desc":"Tăng Transparency 10, Trust 5","effect":{"transparency":10,"trust_all":5}},
    {"id":"D5","name":"Emergency Fund","cost":2,"type":"babyblue","desc":"Tăng Runway 2 tháng","effect":{"runway":2}},
    {"id":"D6","name":"Open Book","cost":2,"type":"babyblue","desc":"Tăng Transparency 20","effect":{"transparency":20}},
    {"id":"D8","name":"Legal Shield","cost":2,"type":"babyblue","desc":"Giảm rủi ro pháp lý 15","effect":{"reg_risk":-15}},
    {"id":"D9","name":"Slow & Steady","cost":1,"type":"babyblue","desc":"Tăng Transparency 5, Hype 2","effect":{"transparency":5,"hype":2}},
    {"id":"D10","name":"Crisis Management","cost":2,"type":"babyblue","desc":"Giảm 50% delta tiêu cực","effect":{"halve_negative_delta":1}},
    {"id":"D11","name":"Supply Chain Fix","cost":2,"type":"babyblue","desc":"Giảm COGS 5%, tăng Transparency 5","effect":{"cogs_percent":-5,"transparency":5}},
    {"id":"D12","name":"Investor Call","cost":1,"type":"babyblue","desc":"Tăng Trust 10","effect":{"trust_all":10}},
    {"id":"D13","name":"Transparency Report","cost":2,"type":"babyblue","desc":"Tăng Transparency 15, giảm Hype 5","effect":{"transparency":15,"hype":-5}},
    
    # Lavender cards (Tokenomics)
    {"id":"T1","name":"Whale Discount","cost":3,"type":"lavender","desc":"Tăng Funding 15%, giảm trust Whale","effect":{"funding_boost_percent":15,"trust_whale":-10}},
    {"id":"T3","name":"Secondary Offering","cost":3,"type":"lavender","desc":"Tăng Funding 20%, giảm trust","effect":{"funding_boost_percent":20,"trust_all":-15}},
    {"id":"T4","name":"DAO Vote","cost":2,"type":"lavender","desc":"Tăng Transparency 5, Trust 5","effect":{"transparency":5,"trust_all":5}},
    {"id":"T6","name":"Treasury Diversify","cost":2,"type":"lavender","desc":"Giảm rủi ro 10, tăng Trust 10","effect":{"reg_risk":-10,"trust_all":10}},
    {"id":"T7","name":"Token Split","cost":2,"type":"lavender","desc":"Tăng Funding 5%, Hype 10","effect":{"funding_boost_percent":5,"hype":10}},
    {"id":"T8","name":"Governance Proposal","cost":1,"type":"lavender","desc":"Tăng Transparency 5, Trust 5","effect":{"transparency":5,"trust_all":5}},
    {"id":"T9","name":"Vesting Extension","cost":2,"type":"lavender","desc":"Tăng Trust 20, Transparency 10","effect":{"trust_all":20,"transparency":10}},
    {"id":"T11","name":"Strategic Partnership","cost":2,"type":"lavender","desc":"Tăng Trust 15, giảm rủi ro","effect":{"trust_all":15,"reg_risk":-5}},
    {"id":"T13","name":"Airdrop to Holders","cost":2,"type":"lavender","desc":"Tăng Trust 10, Hype 15","effect":{"trust_all":10,"hype":15}},
    {"id":"T14","name":"Equity Swap","cost":3,"type":"lavender","desc":"Tăng Funding 30%, giảm trust","effect":{"funding_boost_percent":30,"trust_all":-20}}
]

# ===================== MINH: CARD ENGINE – REACTION CARDS =====================
REACTION_CARDS = [
    {"id":"R1","name":"Lock-up Extension","trigger":"on_bot_withdraw","type":"lavender","desc":"Giảm bán tháo khi bot rút 50%","effect":{"sell_pressure_reduce":0.5}, "cost_percent":2},
    {"id":"R2","name":"Emergency PR","trigger":"on_scenario_market_bad","type":"lavender","desc":"Giảm 50% delta xấu","effect":{"halve_negative_delta":1}, "cost_percent":3},
    {"id":"R3","name":"Whale Whisperer","trigger":"on_whale_trust_low","type":"lavender","desc":"Tăng trust của Whale 10","effect":{"whale_trust":10}, "cost_percent":5},
    {"id":"R4","name":"Damage Control","trigger":"on_transparency_low","type":"lavender","desc":"Tăng Transparency 10, giảm Hype 5","effect":{"transparency":10,"hype":-5}, "cost_percent":2},
    {"id":"R5","name":"Liquidity Injection","trigger":"on_circuit_breaker","type":"lavender","desc":"Rút ngắn circuit breaker","effect":{"circuit_breaker_reduce":1}, "cost_percent":8},
    {"id":"R6","name":"Legal Emergency","trigger":"on_reg_risk_high","type":"lavender","desc":"Giảm rủi ro pháp lý 20","effect":{"reg_risk":-20}, "cost_percent":4},
    {"id":"R7","name":"Security Patch","trigger":"on_security_low","type":"lavender","desc":"Tăng Security 15","effect":{"security":15}, "cost_percent":3},
    {"id":"R8","name":"FOMO Suppression","trigger":"on_hype_high","type":"lavender","desc":"Giảm Hype 15, tăng Transparency 5","effect":{"hype":-15,"transparency":5}, "cost_percent":1},
    {"id":"R9","name":"Investor Assurance","trigger":"on_trust_any_bot_low","type":"lavender","desc":"Tăng trust cho bot đó 15","effect":{"trust_single":15}, "cost_percent":2},
    {"id":"R10","name":"Runway Boost","trigger":"on_runway_low","type":"lavender","desc":"Thêm 3 tháng runway","effect":{"runway":3}, "cost_percent":10}
]

# ==================== PHUC - CALCULATION ====================
def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def calculate_metrics(proj):
    total_fees = proj.get("fee_ecom", 0) + proj.get("fee_retail", 0) + proj.get("fee_direct", 0)
    ch_fees = total_fees / 100.0
    price_real = proj["price"] * (1 - ch_fees)
    cogs_unit = (proj["material"] + proj["packaging"] + proj.get("labor", 0)) * (1 + proj.get("defect_rate", 0) / 100.0)
    gm = (price_real - cogs_unit) / price_real if price_real > 0 else 0
    monthly_burn = proj["fixed_cost"] + proj["marketing_cost"] + (proj["loan"] * proj["interest_rate"] / 100 / 12)
    burn_rate = monthly_burn / proj["target_funding"] if proj["target_funding"] > 0 else 0
    growth = (proj["units_m6"] / proj["units_m1"]) - 1 if proj["units_m1"] > 0 else 0

    # Enhanced intrinsic components
    if gm > 0.2:
        gm_score = 20 + 10 * (1 - math.exp(-5 * (gm - 0.2) / 0.6))
    else:
        gm_score = max(0, 20 * (gm / 0.2))
    gm_score = clamp(gm_score, 0, 30)

    if burn_rate < 0.3:
        burn_score = 15 + 5 * (1 - math.exp(-4 * (0.3 - burn_rate) / 0.25))
    else:
        burn_score = max(0, 15 * (1 - (burn_rate - 0.3) / 0.7))
    burn_score = clamp(burn_score, 0, 20)

    if growth > 0:
        growth_score = 10 + 10 * (1 - math.exp(-3 * growth / 0.5))
    else:
        growth_score = max(0, 10 * (1 + growth / 0.5))
    growth_score = clamp(growth_score, 0, 20)

    revenue_year = proj["units_m6"] * 12 * price_real
    revenue_score = min(10, max(0, math.log10(max(1, revenue_year / 100000)) / 2 * 10))

    total_capital = proj["owner_equity"] + proj["loan"] + proj.get("total_invested", 0)
    annual_profit = (price_real - cogs_unit) * proj["units_m6"] * 12 - (monthly_burn * 12)
    if total_capital > 0 and annual_profit > 0:
        roe = annual_profit / total_capital
        efficiency_score = min(10, roe * 10)
    else:
        efficiency_score = 0
    efficiency_score = clamp(efficiency_score, 0, 10)

    if proj["owner_equity"] > 0:
        debt_ratio = proj["loan"] / proj["owner_equity"]
        if debt_ratio < 0.5:
            leverage_score = 5 + debt_ratio * 10
        elif debt_ratio <= 1.5:
            leverage_score = 10 - (debt_ratio - 0.5) * 5
        else:
            leverage_score = max(0, 5 - (debt_ratio - 1.5) * 3)
    else:
        leverage_score = 0
    leverage_score = clamp(leverage_score, 0, 10)

    intrinsic = gm_score + burn_score + growth_score + revenue_score + efficiency_score + leverage_score

    total_invested = proj.get("total_invested", 0)
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
    if mult < 1:
        val_score = 30 - (1-mult)/1*30
    elif mult <= 3:
        val_score = 80 + (mult-1)/2*20
    elif mult <= 5:
        val_score = 80 - (mult-3)/2*40
    else:
        val_score = max(0, 40 - (mult-5)/2*40)
    val_score = clamp(val_score, 0, 100)

    base_reg = 20 if proj.get("has_license", False) else 80
    if proj.get("legal_cost_spent", 0) >= 0.05 * proj["target_funding"]: base_reg += 20
    reg_risk = clamp(base_reg - proj["transparency"] / 10, 0, 100)
    avail_cash = proj.get("available_cash", proj["owner_equity"] + proj["loan"])
    runway = math.floor(avail_cash / monthly_burn) if monthly_burn > 0 else 999

    return {
        "intrinsic": intrinsic,
        "valuation_sanity": val_score,
        "roi_norm": roi_norm,
        "growth": growth,
        "monthly_burn": monthly_burn,
        "available_cash": avail_cash,
        "runway": runway,
        "funding_progress": proj.get("funding_progress", 0),
        "estimated_valuation": estimated_valuation,
        "raw_roi": raw_roi,
        "reg_risk": reg_risk
    }

def attractiveness(project, bot, metrics):
    raw = 0
    total_w = 0
    for key, w in bot["weights"].items():
        if key == "intrinsic":
            val = metrics["intrinsic"]
        elif key == "valuation":
            val = metrics["valuation_sanity"]
        elif key == "roi_norm":
            val = metrics["roi_norm"]
        elif key == "scalability":
            val = clamp(metrics["growth"] * 100, 0, 100)
        elif key == "transparency":
            val = project["transparency"]
        elif key == "hype":
            val = project["hype"]
        elif key == "visibility":
            val = project.get("visibility", 50)
        elif key == "funding_prog":
            val = metrics["funding_progress"] * 100
        else:
            continue
        sens = bot["hype_sens"] if key == "hype" else (bot["trans_sens"] if key == "transparency" else 1.0)
        raw += val * w * sens
        total_w += w
    if total_w == 0:
        return 0
    raw_A = (raw / total_w) * 100
    if metrics["valuation_sanity"] < 40:
        raw_A = max(0, raw_A - (40 - metrics["valuation_sanity"]) * 1.5)
    trust = project["trust_scores"].get(bot["id"], 50)
    noise = random.uniform(-5, 5) if bot["type"] != "Random" else random.uniform(-10, 10)
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
    raw_final = perf_phase * proj.get("scale_factor", 1.0) * (1 + proj["funding_progress"])
    return clamp(raw_final, 0, 100)

# ==================== JIN: AI BOT GENERATION ====================
random.seed(42)
BOTS = []
for i in range(1, 201):
    bot_type = random.choices(["FOMO", "Value Hunter", "Whale", "Random"], weights=[50, 30, 10, 10])[0]
    wealth_class = random.choices(["small", "medium", "large"], weights=[40, 40, 20])[0]
    wealth = {
        "small": random.randint(1000, 5000),
        "medium": random.randint(10000, 50000),
        "large": random.randint(50000, 200000)
    }[wealth_class]
    hype_sens = round(random.uniform(0.5, 2.5), 2)
    trans_sens = round(random.uniform(0.5, 1.2), 2)

    if bot_type == "FOMO":
        decay = round(random.uniform(0.05, 0.15), 2)
    elif bot_type == "Value Hunter":
        decay = round(random.uniform(0.2, 0.35), 2)
    elif bot_type == "Whale":
        decay = round(random.uniform(0.4, 0.6), 2)
    else:
        decay = round(random.uniform(0.15, 0.4), 2)

    if bot_type == "FOMO":
        weights = {
            "intrinsic": 0.1, "valuation": 0.1, "roi_norm": 0.1,
            "scalability": 0.05, "transparency": 0.05, "hype": 0.42,
            "visibility": 0.09, "funding_prog": 0.09
        }
    elif bot_type == "Value Hunter":
        weights = {
            "intrinsic": 0.43, "valuation": 0.2, "roi_norm": 0.15,
            "scalability": 0.03, "transparency": 0.14, "hype": 0.0,
            "visibility": 0.0, "funding_prog": 0.05
        }
    elif bot_type == "Whale":
        weights = {
            "intrinsic": 0.17, "valuation": 0.42, "roi_norm": 0.15,
            "scalability": 0.03, "transparency": 0.18, "hype": 0.0,
            "visibility": 0.0, "funding_prog": 0.05
        }
    else:
        weights = {
            "intrinsic": 0.1, "valuation": 0.1, "roi_norm": 0.1,
            "scalability": 0.05, "transparency": 0.05, "hype": 0.46,
            "visibility": 0.05, "funding_prog": 0.09
        }
    BOTS.append({
        "id": i, "type": bot_type, "wealth_class": wealth_class, "wealth": wealth,
        "hype_sens": hype_sens, "trans_sens": trans_sens, "memory_decay_rate": decay,
        "weights": weights
    })

def get_bots_for_phase(phase, total_bots=200):
    ratio = min(1.0, phase * 0.2)
    count = int(total_bots * ratio)
    return BOTS[:count]

def process_phase(room, phase, players, logs):
    active_bots = get_bots_for_phase(phase)
    logs.append(f"Phase {phase}: Có {len(active_bots)} bot hoạt động")
    bot_alloc = room['bot_alloc']
    A = {}

    for bot in active_bots:
        for idx, proj in enumerate(players):
            if not proj or proj.get('status') != 'active' or proj['funding_progress'] >= 1 or proj.get('current_phase', 0) >= proj['max_phase']:
                A[(bot['id'], idx)] = -1e9
            else:
                metrics = calculate_metrics(proj)   
                hist = room['bot_memory'][bot['id']]['attractiveness_history'][idx]
                current_attr = attractiveness(proj, bot, metrics)
                if hist:
                    weighted_avg = sum((i+1)*val for i, val in enumerate(hist)) / sum(range(1, len(hist)+1))
                    decay = bot['memory_decay_rate']
                    final_attr = (1 - decay) * current_attr + decay * weighted_avg
                else:
                    final_attr = current_attr
                hist.append(current_attr)
                if len(hist) > 5:
                    hist.pop(0)
                A[(bot['id'], idx)] = final_attr

    for bot in active_bots:
        best_idx = max(range(len(players)), key=lambda i: A.get((bot['id'], i), -1e9))
        alloc_entry = next(entry for entry in bot_alloc if entry['bot_id'] == bot['id'])
        for idx in range(len(players)):
            invested = alloc_entry['perProject'][idx]
            if invested == 0:
                continue
            if players[idx].get('status') != 'active' or players[idx].get('current_phase', 0) >= players[idx]['max_phase']:
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
            max_ratio = min(0.6, 0.2 + (phase - 1) * 0.05)
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

    for bot in active_bots:
        alloc_entry = next(entry for entry in bot_alloc if entry['bot_id'] == bot['id'])
        idle = alloc_entry['idle']
        if idle <= 0:
            continue
        candidates = [i for i, p in enumerate(players) if p and p['status'] == 'active' and p['funding_progress'] < 1 and p.get('current_phase', 0) < p['max_phase']]
        if not candidates:
            continue
        attrs = [A.get((bot['id'], i), -1e9) for i in candidates]
        min_a = min(attrs)
        shifted = [max(0, a - min_a + 0.01) for a in attrs]
        sum_exp = sum(math.exp(a / 20) for a in shifted)
        probs = [math.exp(a / 20) / sum_exp for a in shifted]
        remaining = idle
        for _ in range(5):
            if remaining <= 0:
                break
            for j, idx in enumerate(candidates):
                invest = remaining * probs[j]
                invested_by_bot = alloc_entry['perProject'][idx]
                max_per_bot = players[idx]['target_funding'] * (0.2 if phase == 1 else 0.25)
                cap = min(invest, max_per_bot - invested_by_bot)
                if cap > 0:
                    players[idx]['total_invested'] += cap
                    players[idx]['available_cash'] += cap
                    players[idx]['funding_progress'] = min(1.0, players[idx]['total_invested'] / players[idx]['target_funding'])
                    alloc_entry['perProject'][idx] += cap
                    remaining -= cap
                    logs.append(f"💸 Bot {bot['type']} đầu tư {cap:.0f} vào dự án {idx+1}")
        alloc_entry['idle'] = remaining

# ==================== KHANH: FLASK APP & ROOMS ====================
rooms = {}

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
        'status': 'waiting_for_projects',
        'bot_alloc': None,
        'logs': ["Phòng đã tạo. Chờ người chơi submit dự án..."],
        'player_ready': [False] * num_players,
        'deck_ready': [False] * num_players,
        'pending_cards': {},
        'phase_energy': [3] * num_players,
        'mulligan_used': [False] * num_players,
        'game_ended': False,
        'player_triggers': [{} for _ in range(num_players)],
        'bot_memory': {bot['id']: {'attractiveness_history': [[] for _ in range(num_players)]} for bot in BOTS},
        'submitted_players': 0
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
        'active_deck': None,
        'reaction_hand': None,
        'current_hand': [],
        'energy_left': 3,
    })

    room['players'][player_index] = project_data
    room['player_ready'][player_index] = True
    room['submitted_players'] += 1

    room['logs'].append(f"✅ Player {player_index + 1} đã submit dự án.")

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

    room['status'] = 'choosing_deck'
    room['player_ready'] = [False] * room['num_players']
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
    if not room_id or room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    room = rooms[room_id]
    rankings = []
    
    for i, proj in enumerate(room['players']):
        if proj:
            is_ended = proj.get('status') in ['ended', 'funded', 'bankrupt'] or proj.get('current_phase', 0) >= proj.get('max_phase', 5)
            if is_ended and proj.get('funding_progress', 0) >= 0.5:
                metrics = calculate_metrics(proj)
                score = final_score(proj, proj.get('max_phase', 5), metrics)
            elif is_ended:
                score = 0
            else:
                score = 0
            
            rankings.append({
                'name': f"Player {i+1}",
                'funding': proj.get('funding_progress', 0),
                'hype': proj.get('hype', 50),
                'transparency': proj.get('transparency', 50),
                'score': score,
                'scale': proj.get('scale', 'M'),
                'status': proj.get('status', 'active'),
                'current_phase': proj.get('current_phase', 0),
                'max_phase': proj.get('max_phase', 5)
            })
        else:
            rankings.append({'name': f"Player {i+1}", 'funding': 0, 'score': 0, 'status': 'not_joined'})
    
    return jsonify({
        'status': room['status'],
        'phase': room['phase'],
        'max_phase': room['max_phase'],
        'players_joined': room.get('submitted_players', 0),
        'max_players': room['num_players'],
        'logs': room.get('logs', [])[-40:],
        'rankings': rankings,
        'can_start_deck': room['status'] == 'waiting_for_projects' and room.get('submitted_players', 0) >= 2,
        'submitted_count': room.get('submitted_players', 0)
    })

@app.route('/api/player_state', methods=['GET'])
def player_state():
    room_id = request.args.get('room_id')
    player_index = request.args.get('player_index')
    
    if not room_id or player_index is None:
        return jsonify({'error': 'Missing room_id or player_index'}), 400
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    try:
        player_index = int(player_index)
    except ValueError:
        return jsonify({'error': 'Invalid player_index'}), 400
    
    room = rooms[room_id]
    if player_index < 0 or player_index >= len(room['players']) or room['players'][player_index] is None:
        return jsonify({'error': 'Player not found'}), 404
    
    proj = room['players'][player_index]
    metrics = calculate_metrics(proj)
    
    investors = []
    if room.get('bot_alloc'):
        for alloc in room['bot_alloc']:
            amount = alloc['perProject'][player_index] if player_index < len(alloc['perProject']) else 0
            if amount > 0:
                bot = next((b for b in BOTS if b['id'] == alloc['bot_id']), None)
                if bot:
                    investors.append({'type': bot['type'], 'amount': amount})
    
    is_ended = proj.get('status') in ['ended', 'funded', 'bankrupt'] or proj.get('current_phase', 0) >= proj.get('max_phase', 5)
    final_score_value = 0
    if is_ended and proj.get('funding_progress', 0) >= 0.5:
        final_score_value = final_score(proj, proj.get('max_phase', 5), metrics)
    elif proj.get('status') == 'bankrupt':
        final_score_value = -100
    
    triggers = room.get('player_triggers', [{}])[player_index] if player_index < len(room.get('player_triggers', [])) else {}
    
    return jsonify({
        'status': room.get('status', 'waiting'),
        'phase': room.get('phase', 0),
        'last_scenario': proj.get('last_scenario', 'Chưa có sự kiện'),
        'metrics': {
            'intrinsic': metrics.get('intrinsic', 0),
            'valuation_sanity': metrics.get('valuation_sanity', 0),
            'roi_norm': metrics.get('roi_norm', 0),
            'runway': metrics.get('runway', 0),
            'funding_progress': proj.get('funding_progress', 0)
        },
        'hype': proj.get('hype', 50),
        'transparency': proj.get('transparency', 50),
        'hand': proj.get('current_hand', []),
        'energy_left': proj.get('energy_left', 3),
        'mulligan_used': room.get('mulligan_used', [False])[player_index] if player_index < len(room.get('mulligan_used', [])) else False,
        'investors': investors,
        'funding_progress': proj.get('funding_progress', 0),
        'available_cash': metrics.get('available_cash', 0),
        'reaction_hand': proj.get('reaction_hand', []),
        'game_ended': room.get('game_ended', False),
        'ended': is_ended or proj.get('status') == 'bankrupt',
        'final_score': final_score_value,
        'triggers': triggers.get('available_reactions', [])
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
    if 'trust_whale' in eff:
        for bot in BOTS:
            if bot['type'] == 'Whale':
                bid = bot['id']
                proj['trust_scores'][bid] = clamp(proj['trust_scores'].get(bid, 50) + eff['trust_whale'], 0, 100)
    if 'sell_pressure_reduce' in eff:
        proj['sell_pressure_reduce'] = eff.get('sell_pressure_reduce', 0.5)
    
    cost = (cost_percent / 100.0) * proj['target_funding']
    proj['available_cash'] = max(0, proj['available_cash'] - cost)
    
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

    active_players_ready = all(
        room['player_ready'][i] 
        for i in range(room['num_players']) 
        if room['players'][i] and room['players'][i].get('status') == 'active'
    )
    
    if not active_players_ready:
        return jsonify({'error': 'Chưa phải tất cả người chơi đều Ready'}), 400

    phase = room['phase']
    players = room['players']
    logs = []

    for i in range(room['num_players']):
        room['player_triggers'][i] = {'available_reactions': []}

    for idx, proj in enumerate(players):
        if not proj or proj.get('status') != 'active' or proj.get('current_phase', 0) >= proj.get('max_phase', 999):
            continue

        scenario = random.choice(SCENARIOS)
        proj['last_scenario'] = scenario['name']
        logs.append(f"Dự án {idx+1}: {scenario['name']}")

        d = scenario['delta']

        if 'price' in d:
            proj['price'] *= (1 + d['price'])
        if 'cogs' in d:
            proj['material'] *= (1 + d['cogs'])
            proj['packaging'] *= (1 + d['cogs'])
            proj['labor'] = proj.get('labor', 0) * (1 + d['cogs'])

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

        if idx in room['pending_cards']:
            card = room['pending_cards'][idx]
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
                    proj['labor'] = proj.get('labor', 0) * (1 + eff['cogs_percent'] / 100)
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

        triggers = []
        for rc in proj.get('reaction_hand', []):
            if rc.get('trigger') == 'on_scenario_market_bad' and scenario['cat'] == 'Market':
                if any(k in scenario['name'].lower() for k in ['crisis', 'slow', 'khủng', 'xấu']):
                    triggers.append(rc)
            elif rc.get('trigger') == 'on_transparency_low' and proj['transparency'] < 30:
                triggers.append(rc)
            elif rc.get('trigger') == 'on_reg_risk_high':
                reg = (proj['legal_cost_spent'] / proj['target_funding']) * 100 if proj['target_funding'] > 0 else 0
                if reg > 70:
                    triggers.append(rc)
            elif rc.get('trigger') == 'on_hype_high' and proj['hype'] > 80:
                triggers.append(rc)
            elif rc.get('trigger') == 'on_runway_low':
                m = calculate_metrics(proj)
                if m.get('runway', 999) < 3:
                    triggers.append(rc)

        if triggers:
            room['player_triggers'][idx]['available_reactions'] = triggers
            logs.append(f" → Dự án {idx+1} có {len(triggers)} reaction có thể kích hoạt")

        metrics = calculate_metrics(proj)
        proj['funding_progress'] = metrics.get('funding_progress', 0)
        proj['current_phase'] += 1

        if proj['current_phase'] >= proj['max_phase']:
            proj['status'] = 'ended'
            logs.append(f" → Dự án {idx+1} đã kết thúc.")

    process_phase(room, phase, players, logs)

    room['pending_cards'] = {}
    room['player_ready'] = [False] * room['num_players']
    room['logs'] = logs[-50:]

    room['phase'] += 1

    for idx, proj in enumerate(players):
        if proj and proj.get('status') == 'active' and proj.get('current_phase', 0) < proj.get('max_phase', 999):
            proj['current_hand'] = random.sample(proj['active_deck'], min(5, len(proj['active_deck'])))
            proj['energy_left'] = 3
            room['mulligan_used'][idx] = False

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
    try:
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
    print(f"📌 Mode: Production")
    
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
