# ===================================================================
# STARTUP GAME - TOÀN BỘ CODE GỘP TRONG MỘT FILE
# PHÂN CÔNG:
# - MINH: Dữ liệu cố định, Card Engine, Utils
# - PHÚC: Metrics, Game Controller (process_phase, reset_for_next_phase)
# - KHANH: Attractiveness, Bot AI, Reaction Manager
# - JIN: API Routing, Flask app, Rooms management
# - DƯƠNG: templates/host.html, templates/play.html (riêng)
# ===================================================================


from flask import Flask, render_template, request, jsonify
from werkzeug.exceptions import HTTPException
import random
import math
import uuid
import os

app = Flask(__name__, template_folder='templates')
app.secret_key = 'startup-game-secret'

# ===================== DỮ LIỆU CỐ ĐỊNH =====================
import random
TAG_ALIASES = {
    "demand": "demand_pressure",
    "price": "price_pressure",
    "cost": "cost_pressure",
    "runway": "runway_pressure",
    "funding": "funding_pressure",
    "transparency": "disclosure_pressure",
}

def normalize_tag(tag):
    return TAG_ALIASES.get(tag, tag)

def normalize_tags(tags):
    return sorted({normalize_tag(tag) for tag in tags})
SCENARIOS = [
    {"id": 1, "name": "Market Liquidity Improves and Capital Becomes Easier to Raise", "cat": "Market", "tags": ["market_opportunity", "capital_availability"], "delta": {"price": 0.04, "hype": 10, "funding_boost_percent": 3}},
    {"id": 2, "name": "Investor Risk Appetite Rises for High-Growth Startup Projects ", "cat": "Market", "tags": ["market_opportunity", "capital_availability"], "delta": {"price": 0.07, "hype": 18, "funding_boost_percent": 5}},
    {"id": 3, "name": "Interest Rates Increase and Startup Financing Costs Become More Expensive ", "cat": "Market", "tags": ["market_down", "cost", "funding", "runway"], "delta": {"price": -0.06, "hype": -12, "funding_boost_percent": -4, "runway": -1}},
    {"id": 4, "name": "Capital Shifts from Risky Startup Investments to Safer Assets", "cat": "Market", "tags": ["market_down", "investor_confidence", "funding"], "delta": {"price": -0.08, "hype": -18, "trust_all": -8, "funding_boost_percent": -5}},
    {"id": 5, "name": "Customer Spending Slows and Market Demand for New Products Weakens ", "cat": "Market", "tags": ["demand", "price", "marketing_eff"], "delta": {"price": -0.05, "hype": -10, "runway": -1}},
    {"id": 6, "name": "Funding Becomes Harder and Investors Slow Down New Deals", "cat": "Market", "tags": ["funding", "runway", "market_down", "investor_confidence"], "delta": {"price": -0.12, "hype": -25, "funding_boost_percent": -12, "trust_all": -10, "runway": -2}},
    {"id": 7, "name": "Operating Costs Exceed Budget and the Startup Runway Shrinks", "cat": "Internal", "tags": ["cost", "runway"], "delta": {"cogs": 0.05, "hype": -5, "trust_all": -5, "runway": -1}},
    {"id": 8, "name": "Product Complaints Increase and Customer Trust Drops", "cat": "Internal", "tags": ["product", "reputation"], "delta": {"hype": -10, "transparency": -8, "trust_all": -12, "runway": -1}},
    {"id": 9, "name": "Customer Data Privacy Incident Raises Security and Regulatory Risk", "cat": "Internal", "tags": ["security", "disclosure_pressure", "regulatory"], "delta": {"security": -25, "hype": -15, "transparency": -20, "trust_all": -18, "reg_risk": 15, "cost_percent": 3}},
    {"id": 10, "name": "Internal Budget Tracking Breaks Down and Runway Visibility Becomes Unclear", "cat": "Internal", "tags": ["cost", "runway", "disclosure_pressure", "investor_confidence", "execution"], "delta": {"hype": -6, "transparency": -12, "trust_all": -9, "whale_trust": -6, "funding_boost_percent": -5, "runway": -1}},
    {"id": 11, "name": "Strong Product-Market Fit Signal Attracts Customer and Investor Attention", "cat": "Internal", "tags": ["product_opportunity", "market_opportunity", "demand", "funding_readiness"], "delta": {"hype": 15, "trust_all": 8, "funding_boost_percent": 5}},
    {"id": 12, "name": "Unit Economics Improve and the Business Model Looks More Sustainable", "cat": "Internal", "tags": ["funding_readiness", "investor_confidence"], "delta": {"cogs": -0.04, "hype": 8, "trust_all": 8, "runway": 1, "funding_boost_percent": 4}},
    {"id": 13, "name": "Competitor Cuts Prices and Puts Pressure on Customer Demand", "cat": "External", "tags": ["competition", "price", "demand"], "delta": {"price": -0.05, "hype": -6}},
    {"id": 14, "name": "Competitor Launches a Better Product and Weakens Your Market Position", "cat": "External", "tags": ["competition", "product", "reputation"], "delta": {"price": -0.08, "hype": -15, "trust_all": -5}},
    {"id": 15, "name": "Strategic Partnership Opportunity Appears and Opens a New Growth Channel", "cat": "External", "tags": ["partnership", "market_opportunity", "funding_readiness", "investor_confidence"], "delta": {"price": 0.04, "visibility": 10, "hype": 12, "trust_all": 5, "funding_boost_percent": 4}},
    {"id": 16, "name": "Supplier Delivery Disruption Raises Cost and Weakens Product Availability", "cat": "External", "tags": ["supply", "cost", "runway"], "delta": {"cogs": 0.07, "hype": -8, "trust_all": -5, "runway": -1}},
    {"id": 17, "name": "Negative Media Rumor Spreads and Investor Confidence Falls", "cat": "External", "tags": ["reputation", "disclosure_pressure", "investor_confidence"], "delta": {"hype": -12, "transparency": -12, "trust_all": -15, "whale_trust": -10, "funding_boost_percent": -5}},
    {"id": 18, "name": "Platform Algorithm Reduces Campaign Reach and Marketing Efficiency Drops", "cat": "External", "tags": ["marketing_eff", "visibility", "demand"], "delta": {"visibility": -15, "hype": -10}},
    {"id": 19, "name": "Regulator Requests Additional Documents and Raises Compliance Pressure", "cat": "Regulatory", "tags": ["regulatory", "disclosure_pressure", "legal"], "delta": {"reg_risk": 15, "transparency": -10, "trust_all": -8, "cost_percent": 3}},
    {"id": 20, "name": "Regulatory Sandbox Approval Improves Trust and Funding Readiness", "cat": "Regulatory", "tags": ["regulatory_opportunity", "funding_readiness", "investor_confidence"], "delta": {"reg_risk": -25, "transparency": 15, "trust_all": 15, "hype": 10, "funding_boost_percent": 8}},
    {"id": 21, "name": "New Policy Supports Financial Innovation and Improves Investor Appetite", "cat": "Regulatory", "tags": ["regulatory_opportunity", "market_opportunity", "capital_availability"], "delta": {"reg_risk": -12, "transparency": 5, "trust_all": 5, "hype": 8, "funding_boost_percent": 5}},
    {"id": 22, "name": "New Fundraising Disclosure Rule Increases Compliance Burden", "cat": "Regulatory", "tags": ["regulatory", "disclosure_pressure", "funding_pressure", "compliance_pressure"], "delta": {"reg_risk": 18, "transparency": -12, "trust_all": -10, "funding_boost_percent": -6, "cost_percent": 4}},
    {"id": 23, "name": "Tax and Reporting Review Increases Legal Cost and Shortens Runway", "cat": "Regulatory", "tags": ["regulatory", "cost", "legal", "runway"], "delta": {"reg_risk": 10, "transparency": -5, "trust_all": -5, "cost_percent": 3, "runway": -1}},
    {"id": 24, "name": "Independent Compliance Certification Opportunity Strengthens Investor Trust", "cat": "Regulatory", "tags": ["compliance_opportunity", "regulatory_opportunity", "investor_confidence"], "delta": {"reg_risk": -10, "transparency": 12, "trust_all": 12, "whale_trust": 8, "funding_boost_percent": 4}}
]

SCENARIO_PRIMARY_GROUP = {
    1: "red",
    2: "purple",
    3: "purple",
    4: "purple",
    5: "red",
    6: "purple",

    7: "green",
    8: "green",
    9: "green",
    10: "green",
    11: "red",
    12: "purple",

    13: "red",
    14: "red",
    15: "purple",
    16: "green",
    17: "green",
    18: "red",

    19: "green",
    20: "purple",
    21: "purple",
    22: "green",
    23: "green",
    24: "green",
}

for scenario in SCENARIOS:
    scenario["primary_group"] = SCENARIO_PRIMARY_GROUP[scenario["id"]]
    scenario["tags"] = normalize_tags(scenario["tags"])
    
ACTIVE_CARDS_FULL = [
    {"id": "A1", "name": "Low-Budget Target Ads", "cost": 1, "type": "red", "desc": "Run a small paid ad test to increase demand and visibility.", "counters": ["demand", "marketing_eff", "visibility"], "effect": {"hype": 6, "visibility": 5, "cost_percent": 1}},
    {"id": "A2", "name": "Quick Social Media Posts", "cost": 1, "type": "red", "desc": "Post a short social content for short-term attention. Cheap, fast, but shallow.", "counters": ["market_opportunity", "visibility", "reputation"], "effect": {"hype": 7, "visibility": 7, "cost_percent": 1}},
    {"id": "A3", "name": "Customer Referral Loop", "cost": 1, "type": "red", "desc": "Turn existing users into a small organic growth loop.", "counters": ["demand", "product_opportunity"], "effect": {"hype": 6, "trust_all": 3}},
    {"id": "A4", "name": "One-Week Promo Offer", "cost": 1, "type": "red", "desc": "Use a short promotion to create urgency without changing the full pricing strategy.", "counters": ["demand", "price", "competition"], "effect": {"price": -0.05, "hype": 8, "visibility": 4}},
    {"id": "A5", "name": "Press Outreach Cycle", "cost": 2, "type": "red", "desc": "Pitch the startup story to gain public  attention.", "counters": ["visibility", "reputation", "market_opportunity"], "effect": {"hype": 12, "visibility": 14, "trust_all": 3, "cost_percent": 2}},
    {"id": "A6", "name": "Creator Partnership Campaign", "cost": 2, "type": "red", "desc": "Work with a creator or influencer to expand reach and awareness.", "counters": ["competition", "demand", "visibility"], "effect": {"hype": 14, "visibility": 15, "cost_percent": 3}},
    {"id": "A7", "name": "Conversion Funnel Refresh", "cost": 2, "type": "red", "desc": "Improve landing pages, messaging, and conversion flow to recover weak demand.", "counters": ["marketing_eff", "demand", "price"], "effect": {"hype": 8, "trust_all": 3, "cost_percent": 3}},
    {"id": "A8", "name": "Feature Launch Webinar", "cost": 2, "type": "red", "desc": "Demonstrate new product features publicly to build customer interest.", "counters": ["product", "competition", "product_opportunity"], "effect": {"hype": 15, "visibility": 8, "cost_percent": 3}},
    {"id": "A9", "name": "Multi-Channel Acquisition Sprint", "cost": 2, "type": "red", "desc": "Expand promotion across several channels when one channel performs poorly.", "counters": ["marketing_eff", "visibility", "demand"], "effect": {"visibility": 12, "hype": 8, "cost_percent": 3}},
    {"id": "A10", "name": "Customer Proof Campaign", "cost": 2, "type": "red", "desc": "Use customer success stories to convert credibility into demand.", "counters": ["reputation", "demand"], "effect": {"trust_all": 7, "hype": 7, "transparency": 3, "cost_percent": 2}},
    {"id": "A11", "name": "Full-Scale Brand Repositioning", "cost": 3, "type": "red", "desc": "Launch a large brand campaign to change market perception and defend against competitors.", "counters": ["competition", "demand", "market_opportunity", "reputation"], "effect": {"hype": 22, "visibility": 22, "trust_all": 5, "cost_percent": 6}},
    {"id": "A12", "name": "National Launch Rollout", "cost": 3, "type": "red", "desc": "Run a broad launch rollout to create national awareness and accelerate acquisition.", "counters": ["demand", "visibility", "product_opportunity", "market_opportunity"], "effect": {"hype": 24, "visibility": 24, "cost_percent": 7, "runway": -1}},
    {"id": "A13", "name": "Aggressive Pricing Strategy", "cost": 3, "type": "red", "desc": "Cut pricing aggressively to defend market share, with margin and trust trade-offs.", "counters": ["price", "competition", "demand"], "effect": {"price": -0.15, "hype": 16, "trust_all": -6, "runway": -1}},
    {"id": "A14", "name": "Hypergrowth Expansion Program", "cost": 3, "type": "red", "desc": "Spend aggressively to turn market opportunity into rapid growth and stronger traction.", "counters": ["market_opportunity", "capital_availability", "product_opportunity"], "effect": {"hype": 24, "funding_boost_percent": 8, "cost_percent": 6, "runway": -1}},
    {"id": "D1", "name": "Cutting cost", "cost": 1, "type": "green", "desc": "Cutting unnecessary expenses without disrupting daily operations.", "counters": ["cost", "runway"], "effect": {"cogs": -0.03}},
    {"id": "D2", "name": "Community Update", "cost": 1, "type": "green", "desc": "Publish a clear update to explain progress and reduce uncertainty.", "counters": ["reputation", "disclosure_pressure"], "effect": {"hype": 1, "transparency": 6, "trust_all": 4}},
    {"id": "D3", "name": "Complaint Response Desk", "cost": 1, "type": "green", "desc": "Quickly respond to complaints and reduce product frustration.", "counters": ["product", "reputation"], "effect": {"trust_all": 5, "transparency": 2}},
    {"id": "D4", "name": "Basic Compliance Checklist", "cost": 1, "type": "green", "desc": "Check basic regulatory items such as required documents, licenses, reporting records, tax files, and fundraising disclosures.", "counters": ["regulatory", "legal", "disclosure_pressure", "compliance_pressure"], "effect": {"reg_risk": -6, "transparency": 4, "trust_all": 2}},
    {"id": "D5", "name": "Founder AMA Session", "cost": 1, "type": "green", "desc": "Let founders answer questions directly to build confidence.", "counters": ["reputation"], "effect": {"trust_all": 6, "transparency": 5, "hype": 1}},
    {"id": "D6", "name": "Supplier Renegotiation", "cost": 2, "type": "green", "desc": "Negotiate with suppliers to reduce COGS and ease supply pressure.", "counters": ["cost", "supply", "runway"], "effect": {"cogs": -0.08, "runway": 1, "cost_percent": 1}},
    {"id": "D7", "name": "Quality Recovery Program", "cost": 2, "type": "green", "desc": "Improve quality control to reduce defects, complaints, and product frustration.", "counters": ["product", "reputation"], "effect": {"trust_all": 8, "transparency": 4, "cost_percent": 2}},
    {"id": "D8", "name": "Data Protection Review", "cost": 2, "type": "green", "desc": "Review data handling and patch security weaknesses before they become worse.", "counters": ["security", "regulatory"], "effect": {"security": 15, "transparency": 8, "trust_all": 5, "cost_percent": 3}},
    {"id": "D9", "name": "Regulatory Document Response Pack", "cost": 2, "type": "green", "desc": "Prepare legal, tax, and operating documents before regulators or investors ask.", "counters": ["regulatory", "legal", "disclosure_pressure"], "effect": {"reg_risk": -12, "transparency": 8, "trust_all": 4, "cost_percent": 2}},
    {"id": "D10", "name": "Reviewed Monthly Metrics Pack", "cost": 2, "type": "green", "desc": "Share reviewed monthly metrics to support investor due diligence.", "counters": ["investor_confidence", "disclosure_pressure"], "effect": {"transparency": 14, "trust_all": 8, "hype": -2, "cost_percent": 2}},
    {"id": "D11", "name": "Crisis Coordination Playbook", "cost": 2, "type": "green", "desc": "Coordinate a structured response to limit damage from a negative event.", "counters": ["market_down", "reputation", "supply", "cost"], "effect": {"transparency": 8, "trust_all": 6, "reg_risk": -4, "cost_percent": 3}},
    {"id": "D12", "name": "Governance and Reporting Recovery Program", "cost": 3, "type": "green", "desc": "Launch a full recovery program to improve internal controls, reporting quality, compliance readiness, and investor confidence after a serious trust or disclosure problem.", "counters": ["disclosure_pressure", "investor_confidence", "regulatory", "reputation", "execution", "compliance_opportunity"], "effect": {"transparency": 20, "trust_all": 14, "whale_trust": 9, "reg_risk": -10, "cost_percent": 5}},
    {"id": "D13", "name": "Emergency Cash Reserve", "cost": 3, "type": "green", "desc": "Reserve cash to survive a funding slowdown or runway crisis.", "counters": ["runway", "funding", "market_down"], "effect": {"runway": 3, "trust_all": 4, "funding_boost_percent": -3, "hype": -3, "cost_percent": 8}},
    {"id": "D14", "name": "Cybersecurity Incident Response", "cost": 3, "type": "green", "desc": "Launch a full response after a privacy or cybersecurity incident.", "counters": ["security", "regulatory"], "effect": {"security": 23, "transparency": 12, "trust_all": 10, "reg_risk": -8, "cost_percent": 5}},
    {"id": "C1", "name": "Use-of-Funds Note", "cost": 1, "type": "purple", "desc": "Explain how the startup will use raised capital across product, marketing, operations, and reserves.", "counters": ["funding", "disclosure_pressure", "investor_confidence"], "effect": {"transparency": 5, "trust_all": 4, "funding_boost_percent": 3}},
    {"id": "C2", "name": "Funding Gap Calculator", "cost": 1, "type": "purple", "desc": "Calculate how much extra capital the startup needs by comparing current cash and target funding requirement.", "counters": ["funding", "runway", "capital_availability", "investor_confidence"], "effect": {"funding_boost_percent": 4, "transparency": 4, "trust_all": 3}},
    {"id": "C3", "name": "Investor Risk Q&A Call", "cost": 1, "type": "purple", "desc": "Answer investor questions about revenue, costs, valuation, dilution, and business risks.", "counters": ["investor_confidence"], "effect": {"whale_trust": 7, "trust_all": 5, "transparency": 3}},
    {"id": "C4", "name": "Funding Milestone Plan", "cost": 1, "type": "purple", "desc": "Link the fundraising target to measurable milestones such as revenue, users, margin, or launch timeline.", "counters": ["funding", "capital_availability", "regulatory_opportunity"], "effect": {"funding_boost_percent": 5, "transparency": 3, "trust_all": 3}},
    {"id": "C5", "name": "Comparable Valuation Pack", "cost": 2, "type": "purple", "desc": "Prepare a valuation pack using comparable companies, revenue multiples, margin, and growth assumptions.", "counters": ["investor_confidence", "funding_readiness", "disclosure_pressure"], "effect": {"transparency": 7, "funding_boost_percent": 6, "cost_percent": 2}},
    {"id": "C6", "name": "Working Capital Plan", "cost": 2, "type": "purple", "desc": "Plan short-term cash needs for inventory, receivables, operating expenses, and emergency liquidity.", "counters": ["runway", "cost", "funding"], "effect": {"runway": 1, "trust_all": 5, "funding_boost_percent": 5, "cost_percent": 2}},
    {"id": "C7", "name": "Convertible Loan Proposal", "cost": 2, "type": "purple", "desc": "Raise capital through a loan that can later convert into equity, balancing cash needs and financing cost.", "counters": ["funding_pressure", "runway", "capital_availability"], "effect": {"funding_boost_percent": 12, "runway": 1, "trust_all": -2, "cost_percent": 3}},
    {"id": "C8", "name": "Founder Equity Commitment", "cost": 2, "type": "purple", "group": "purple", "group_name": "Capital & Governance", "desc": "Show that founders remain committed by linking founder equity to continued contribution and project progress.", "counters": ["investor_confidence"], "effect": {"trust_all": 13, "transparency": 6, "cost_percent": 2}},
    {"id": "C9", "name": "Runway Reforecast Plan", "cost": 2, "type": "purple", "desc": "Recalculate monthly burn, remaining runway, funding gap, and cost-saving options to show investors how the startup can survive under cash pressure.", "counters": ["runway", "cost", "funding", "investor_confidence"], "effect": {"transparency": 7, "funding_boost_percent": 7, "trust_all": 5, "runway": 1, "cost_percent": 2}},
    {"id": "C10", "name": "Strategic Channel Partnership", "cost": 2, "type": "purple", "desc": "Build a partnership that improves distribution, revenue visibility, and investor confidence.", "counters": ["partnership", "competition", "market_opportunity", "capital_availability"], "effect": {"trust_all": 10, "visibility": 6, "funding_boost_percent": 4, "cost_percent": 3}},
    {"id": "C11", "name": "Urgent Rescue Financing Round", "cost": 3, "type": "purple", "desc": "Negotiate an urgent financing round during a funding crisis.", "counters": ["funding_pressure", "market_down", "capital_availability", "investor_confidence"], "effect": {"funding_boost_percent": 23, "whale_trust": 12, "runway": 1, "trust_all": -10, "hype": -4, "cost_percent": 6}},
    {"id": "C12", "name": "Emergency Bridge Financing Round", "cost": 3, "type": "purple", "desc": "Raise short-term bridge financing to survive a funding gap, but accept higher cost and repayment pressure.", "counters": ["funding", "runway", "market_down", "capital_availability"], "effect": {"funding_boost_percent": 24, "runway": 2, "trust_all": -12, "hype": -5, "cost_percent": 6}},
    {"id": "C13", "name": "Investor Downside Protection Reserve", "cost": 3, "type": "purple", "desc": "Prepare a strong investor assurance package covering downside protection.", "counters": ["funding", "market_down", "investor_confidence"], "effect": {"trust_all": 18, "whale_trust": 10, "runway": -1, "cost_percent": 8}},
    {"id": "C14", "name": "Strategic Investment Partnership", "cost": 3, "type": "purple", "desc": "Prepare a strategic acquisition, merger, or major investment negotiation to solve funding and competitive pressure.", "counters": ["competition", "partnership", "funding", "capital_availability"], "effect": {"funding_boost_percent": 20, "trust_all": 15, "whale_trust": 8, "cost_percent": 6}},
]

for card in ACTIVE_CARDS_FULL:
    if card["id"].startswith("A"):
        card["group"] = "red"
        card["group_name"] = "Market Momentum"
    elif card["id"].startswith("D"):
        card["group"] = "green"
        card["group_name"] = "Resilience & Trust"
    elif card["id"].startswith("C"):
        card["group"] = "purple"
        card["group_name"] = "Capital & Governance"

for card in ACTIVE_CARDS_FULL:
    card["counters"] = normalize_tags(card["counters"])

def card_matches_scenario(card, scenario):
    scenario_tags = set(normalize_tags(scenario.get("tags", [])))
    card_counters = set(normalize_tags(card.get("counters", [])))
    return len(scenario_tags & card_counters) > 0


def draw_hand_with_cost_ladder(player_deck, scenario, hand_size=5):
    primary_group = scenario.get("primary_group")
    hand = []

    for cost in [1, 2, 3]:
        candidates = [
            card for card in player_deck
            if card.get("group") == primary_group
            and card.get("cost") == cost
            and card_matches_scenario(card, scenario)
            and card not in hand
        ]

        if not candidates:
            candidates = [
                card for card in player_deck
                if card.get("cost") == cost
                and card_matches_scenario(card, scenario)
                and card not in hand
            ]

        if candidates:
            hand.append(random.choice(candidates))

    remaining_pool = [card for card in player_deck if card not in hand]
    random.shuffle(remaining_pool)

    while len(hand) < hand_size and remaining_pool:
        hand.append(remaining_pool.pop())

    random.shuffle(hand)
    return hand

def draw_hand_no_duplicate_color_cost(deck, hand_size=5):
    """Chọn hand_size lá từ deck sao cho không có 2 lá cùng (group, cost).
       Nếu deck không đủ đa dạng, vẫn cố gắng tránh trùng lặp tối đa."""
    from collections import defaultdict
    import random

    # Nhóm các lá bài theo (group, cost)
    groups = defaultdict(list)
    for card in deck:
        groups[(card['group'], card['cost'])].append(card)

    unique_groups = list(groups.keys())
    hand = []

    if len(unique_groups) >= hand_size:
        # Đủ nhóm khác nhau: chọn hand_size nhóm ngẫu nhiên, mỗi nhóm lấy 1 lá
        selected_groups = random.sample(unique_groups, hand_size)
        hand = [random.choice(groups[g]) for g in selected_groups]
    else:
        # Không đủ nhóm: lấy mỗi nhóm một lá trước, sau đó bổ sung ngẫu nhiên
        for g in unique_groups:
            hand.append(random.choice(groups[g]))
        while len(hand) < hand_size:
            g = random.choice(unique_groups)
            hand.append(random.choice(groups[g]))
    random.shuffle(hand)
    return hand


MAX_REACTION_CARDS_PER_GAME = 3

REACTION_CARDS = [
    {"id": "R1", "name": "Emergency Investor Trust Recovery Update", "trigger": "on_trust_low", "condition": {"metric": "trust_all", "operator": "<", "value": 20}, "desc": "Send a clear recovery update when overall investor trust becomes dangerously low.", "cost_percent": 2, "effect": {"trust_all": 8, "transparency": 5, "hype": -2}},

    {"id": "R2", "name": "Emergency Disclosure Statement", "trigger": "on_transparency_low", "condition": {"metric": "transparency", "operator": "<", "value": 25}, "desc": "Publish a clear emergency statement when lack of information creates serious doubt.", "cost_percent": 3, "effect": {"transparency": 12, "trust_all": 6, "hype": -3}},
    
    {"id": "R3", "name": "Data Breach Emergency Fix", "trigger": "on_security_low", "condition": {"metric": "security", "operator": "<", "value": 20}, "desc": "Take urgent action to contain a data privacy or cybersecurity problem.", "cost_percent": 5, "effect": {"security": 20, "transparency": 8, "trust_all": 6, "reg_risk": -8}},

    {"id": "R4", "name": "Urgent Legal Support", "trigger": "on_reg_risk_high", "condition": {"metric": "reg_risk", "operator": ">", "value": 70}, "desc": "Bring in legal support when compliance or regulatory risk becomes too high.", "cost_percent": 4, "effect": {"reg_risk": -20, "transparency": 4}},

    {"id": "R5", "name": "Emergency Burn Reduction Plan", "trigger": "on_runway_warning", "condition": {"metric": "runway", "operator": "<=", "value": 2}, "desc": "Cut non-essential spending when the startup has only a short runway left before a cash crisis.", "cost_percent": 2, "effect": {"runway": 1, "cogs": -0.03, "hype": -3, "trust_all": -2}},
    
    {"id": "R6", "name": "Emergency Visibility Recovery Sprint", "trigger": "on_visibility_collapse", "condition": {"metric": "visibility", "operator": "<", "value": 25}, "desc": "Run an urgent visibility recovery sprint when the startup loses market reach.", "cost_percent": 4, "effect": {"visibility": 16, "hype": 6, "trust_all": 3, "cost_percent": 3}},

    {"id": "R7", "name": "Product Quality Recall", "trigger": "on_customer_trust_low", "condition": {"metric": "trust_all", "operator": "<", "value": 10}, "desc": "Recall or fix poor-quality products before customer trust is damaged further.", "cost_percent": 5, "effect": {"trust_all": 8, "transparency": 5, "hype": -3}},
    
    {"id": "R8", "name": "Emergency Cost Freeze", "trigger": "on_cogs_rise", "condition": {"metric": "cogs", "operator": ">", "value": 0.6}, "desc": "Freeze non-essential spending when production or operating costs rise sharply.", "cost_percent": 1, "effect": {"cogs": -0.04, "runway": 1, "hype": -3}},

    {"id": "R9", "name": "Emergency Bridge Cash", "trigger": "on_near_bankruptcy", "condition": {"metric": "runway", "operator": "<=", "value": 1}, "desc": "Secure short-term emergency cash to prevent immediate bankruptcy, but accept weaker investor confidence.", "cost_percent": 3, "effect": {"runway": 2, "funding_boost_percent": 5, "trust_all": -6}},

    {"id": "R10", "name": "Investor Withdrawal Defense", "trigger": "on_bot_withdraw", "condition": {"event": "bot_withdraw"}, "desc": "Reassure investors when withdrawal pressure starts and reduce the risk of panic selling.", "cost_percent": 3, "effect": {"sell_pressure_reduce": 0.5, "trust_all": 8, "whale_trust": 5, "runway": 1}},
]
from collections import Counter

def validate_master_data():
    errors = []

    if len(SCENARIOS) != 24:
        errors.append(f"SCENARIOS must have 24 items, found {len(SCENARIOS)}")

    if len(ACTIVE_CARDS_FULL) != 42:
        errors.append(f"ACTIVE_CARDS_FULL must have 42 cards, found {len(ACTIVE_CARDS_FULL)}")

    if len(REACTION_CARDS) != 10:
        errors.append(f"REACTION_CARDS must have 10 cards, found {len(REACTION_CARDS)}")

    active_ids = [card["id"] for card in ACTIVE_CARDS_FULL]
    if len(active_ids) != len(set(active_ids)):
        errors.append("Duplicate active card IDs found")

    for card in ACTIVE_CARDS_FULL:
        for key in ["id", "name", "cost", "type", "group", "group_name", "desc", "counters", "effect"]:
            if key not in card:
                errors.append(f"{card.get('id')} missing key: {key}")

    group_count = Counter(card.get("group") for card in ACTIVE_CARDS_FULL)
    if dict(group_count) != {"red": 14, "green": 14, "purple": 14}:
        errors.append(f"Wrong group count: {dict(group_count)}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "group_count": dict(group_count),
    }

# ==================== CÁC HÀM HỖ TRỢ ====================
def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def get_scale_factor(scale):
    return {"S": 0.8, "M": 1.0, "L": 1.2}.get(scale, 1.0)

def calculate_metrics(proj):
    # Đảm bảo các key cần thiết có giá trị mặc định
    proj.setdefault('fee_ecom', 0)
    proj.setdefault('fee_retail', 0)
    proj.setdefault('fee_direct', 0)
    proj.setdefault('material', 0)
    proj.setdefault('packaging', 0)
    proj.setdefault('labor', 0)
    proj.setdefault('defect_rate', 0)
    proj.setdefault('fixed_cost', 0)
    proj.setdefault('marketing_cost', 0)
    proj.setdefault('loan', 0)
    proj.setdefault('interest_rate', 0)
    proj.setdefault('target_funding', 1)   # tránh chia 0
    proj.setdefault('units_m1', 1)
    proj.setdefault('units_m6', 1)
    proj.setdefault('owner_equity', 0)
    proj.setdefault('price', 1)
    proj.setdefault('has_license', False)
    proj.setdefault('legal_cost_spent', 0)
    proj.setdefault('transparency', 50)
    proj.setdefault('available_cash', 0)
    proj.setdefault('security', 50)
    proj.setdefault('reg_risk', 0)
    proj.setdefault('hype', 50)
    proj.setdefault('visibility', 50)
    proj.setdefault('total_invested', 0)

    total_fees = proj.get("fee_ecom", 0) + proj.get("fee_retail", 0) + proj.get("fee_direct", 0)
    ch_fees = total_fees / 100.0
    price_real = proj["price"] * (1 - ch_fees)
    cogs_unit = (proj["material"] + proj["packaging"] + proj.get("labor", 0)) * (1 + proj.get("defect_rate", 0) / 100.0)
    gm = (price_real - cogs_unit) / price_real if price_real > 0 else 0
    monthly_burn = proj["fixed_cost"] + proj["marketing_cost"] + (proj["loan"] * proj["interest_rate"] / 100 / 12)
    burn_rate = monthly_burn / proj["target_funding"] if proj["target_funding"] > 0 else 0
    growth = (proj["units_m6"] / proj["units_m1"]) - 1 if proj["units_m1"] > 0 else 0

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

    avg_monthly_units = (proj["units_m1"] + proj["units_m6"]) / 2
    revenue_year = avg_monthly_units * 12 * price_real
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
    
    # Penalty: security càng thấp càng mất điểm (tối đa -10), reg_risk càng cao càng mất điểm (tối đa -10)
    security_penalty = max(0, (50 - proj.get('security', 50)) / 5)   # mỗi 5 điểm dưới 50 trừ 1
    reg_risk_penalty = proj.get('reg_risk', 0) / 10                  # mỗi 10% reg_risk trừ 1
    intrinsic = max(0, intrinsic - security_penalty - reg_risk_penalty)

    total_invested = proj.get("total_invested", 0)
    ps_ratio = 3.0
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

# ==================== KHANH: AI BOT GENERATION ====================
random.seed(42)
BOTS = []
for i in range(1, 201):
    bot_type = random.choices(["FOMO", "Value Hunter", "Whale", "Random"], weights=[50, 30, 10, 10])[0]
    wealth_class = random.choices(["small", "medium", "large"], weights=[40, 40, 20])[0]
    wealth = {
        "small": random.randint(50, 200),
        "medium": random.randint(500, 2000),
        "large": random.randint(2000, 8000)
    }[wealth_class]
    hype_sens = round(random.uniform(0.2, 1.0), 2) if bot_type != "FOMO" else round(random.uniform(0.8, 1.5), 2)
    trans_sens = round(random.uniform(0.8, 2.0), 2)

    if bot_type == "FOMO":
        decay = round(random.uniform(0.02, 0.08), 2)
    elif bot_type == "Value Hunter":
        decay = round(random.uniform(0.1, 0.2), 2)
    elif bot_type == "Whale":
        decay = round(random.uniform(0.2, 0.4), 2)
    else:
        decay = round(random.uniform(0.1, 0.3), 2)

    if bot_type == "FOMO":
        weights = {
            "intrinsic": 0.1, "valuation": 0.1, "roi_norm": 0.1,
            "scalability": 0.05, "transparency": 0.05, "hype": 0.42,
            "visibility": 0.09, "funding_prog": 0.09,
            "security": 0.05, "reg_risk": 0.05          # thêm security & reg_risk
        }
    elif bot_type == "Value Hunter":
        weights = {
            "intrinsic": 0.43, "valuation": 0.2, "roi_norm": 0.15,
            "scalability": 0.03, "transparency": 0.14, "hype": 0.0,
            "visibility": 0.0, "funding_prog": 0.05,
            "security": 0.10, "reg_risk": 0.10          # thêm security & reg_risk
        }
    elif bot_type == "Whale":
        weights = {
            "intrinsic": 0.17, "valuation": 0.42, "roi_norm": 0.15,
            "scalability": 0.03, "transparency": 0.18, "hype": 0.0,
            "visibility": 0.0, "funding_prog": 0.05,
            "security": 0.10, "reg_risk": 0.10          # thêm security & reg_risk
        }
    else:  # Random
        weights = {
            "intrinsic": 0.1, "valuation": 0.1, "roi_norm": 0.1,
            "scalability": 0.05, "transparency": 0.05, "hype": 0.46,
            "visibility": 0.05, "funding_prog": 0.09,
            "security": 0.05, "reg_risk": 0.05          # thêm security & reg_risk
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
        elif key == "security":
            val = project.get('security', 50)
        elif key == "reg_risk":
            val = 100 - project.get('reg_risk', 0)  # đảo ngược: reg_risk thấp → điểm cao
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
    if proj["funding_progress"] < 0:
        return 0

    funding_score = proj["funding_progress"] * 40

    complete_phase = proj.get("funding_complete_phase")
    max_phase = proj.get("max_phase", 5)
    if complete_phase is not None and max_phase > 1:
        speed_score = 20 * (1 - (complete_phase - 1) / (max_phase - 1))
    else:
        speed_score = 0
    speed_score = max(0, min(20, speed_score))

    roi_score = min(20, (metrics["roi_norm"] / 100) * 20)
    trans_score = max(0, min(20, (proj["transparency"] / 100) * 20))

    raw = funding_score + speed_score + roi_score + trans_score
    raw = max(0, min(100, raw))

    scale_map = {"S": 0.8, "M": 0.9, "L": 1.0}
    scale_factor = scale_map.get(proj.get("scale", "M"), 0.9)
    funding_bonus = (1 + proj["funding_progress"]) / 2

    final = raw * scale_factor * funding_bonus
    return min(100, max(0, final))

def get_bot_memory(room, bot_id, player_count):
    """Return stable bot memory even after JSON turns numeric keys into strings."""
    room.setdefault('bot_memory', {})
    str_key = str(bot_id)
    int_key = bot_id

    memory = room['bot_memory'].get(str_key)
    if memory is None and int_key in room['bot_memory']:
        memory = room['bot_memory'].pop(int_key)
        room['bot_memory'][str_key] = memory
    if memory is None:
        memory = {'attractiveness_history': [[] for _ in range(player_count)]}
        room['bot_memory'][str_key] = memory

    history = memory.setdefault('attractiveness_history', [])
    while len(history) < player_count:
        history.append([])
    if len(history) > player_count:
        del history[player_count:]
    return memory

def ensure_room_lists(room):
    num_players = int(room.get('num_players') or len(room.get('players', [])) or 4)
    room['num_players'] = num_players

    list_defaults = {
        'players': lambda: None,
        'player_ready': lambda: False,
        'deck_ready': lambda: False,
        'mulligan_used': lambda: False,
        'phase_energy': lambda: 3,
        'player_triggers': lambda: {},
    }

    for key, default_factory in list_defaults.items():
        value = room.get(key)
        if not isinstance(value, list):
            value = []
        while len(value) < num_players:
            value.append(default_factory())
        if len(value) > num_players:
            del value[num_players:]
        room[key] = value

    room.setdefault('pending_cards', {})
    room.setdefault('logs', [])
    room.setdefault('phase_details', [])
    if 'submitted_players' not in room:
        room['submitted_players'] = sum(1 for player in room['players'] if player is not None)

def ensure_bot_alloc(room):
    num_players = int(room.get('num_players') or len(room.get('players', [])) or 4)
    bot_alloc = room.get('bot_alloc')
    if not isinstance(bot_alloc, list):
        room['bot_alloc'] = [
            {'bot_id': bot['id'], 'perProject': [0] * num_players, 'idle': bot['wealth']}
            for bot in BOTS
        ]
        return

    by_id = {entry.get('bot_id'): entry for entry in bot_alloc if isinstance(entry, dict)}
    normalized = []
    for bot in BOTS:
        entry = by_id.get(bot['id'])
        if not entry:
            entry = {'bot_id': bot['id'], 'perProject': [0] * num_players, 'idle': bot['wealth']}
        per_project = entry.get('perProject')
        if not isinstance(per_project, list):
            per_project = []
        while len(per_project) < num_players:
            per_project.append(0)
        if len(per_project) > num_players:
            del per_project[num_players:]
        entry['perProject'] = per_project
        entry['idle'] = entry.get('idle', bot['wealth'])
        normalized.append(entry)
    room['bot_alloc'] = normalized

def aggregate_bot_actions(bot_actions):
    grouped = {}
    for action in bot_actions or []:
        key = (
            action.get('bot_type', 'Unknown'),
            action.get('action', 'unknown'),
            action.get('player_index', -1),
        )
        grouped[key] = grouped.get(key, 0) + action.get('amount', 0)

    return [
        {
            'bot_type': bot_type,
            'action': action,
            'player_index': player_index,
            'amount': amount,
        }
        for (bot_type, action, player_index), amount in sorted(grouped.items())
    ]

def process_phase(room, phase, players, logs, bot_actions=None):
    if bot_actions is None:
        bot_actions = []
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
                bot_memory = get_bot_memory(room, bot['id'], len(players))
                hist = bot_memory['attractiveness_history'][idx]
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
            if players[idx].get('status') in ['ended', 'funded']:
                continue
            if players[idx].get('status') != 'active' or players[idx].get('current_phase', 0) >= players[idx]['max_phase']:
                if invested > 0:
                    withdraw_amount = min(invested, players[idx]['available_cash'], players[idx]['total_invested'])
                    if withdraw_amount > 0:
                        players[idx]['available_cash'] -= withdraw_amount
                        players[idx]['total_invested'] -= withdraw_amount
                        players[idx]['funding_progress'] = max(0, players[idx]['total_invested'] / players[idx]['target_funding'])
                        alloc_entry['idle'] += withdraw_amount
                        alloc_entry['perProject'][idx] = 0
                        bot_actions.append({'bot_type': bot['type'], 'action': 'withdraw', 'player_index': idx, 'amount': withdraw_amount})
                        logs.append(f"Bot {bot['type']} rút toàn bộ {withdraw_amount:.0f} từ dự án {idx+1} (kết thúc)")
                continue
            diff = A.get((bot['id'], best_idx), -1e9) - A.get((bot['id'], idx), -1e9)
            if diff > 25:
                withdraw_ratio = 0.5
            elif diff > 15:
                withdraw_ratio = 0.25
            elif diff > 5:
                withdraw_ratio = 0.0   # không rút
            else:
                withdraw_ratio = 0.0
            
            # Nếu dự án gần đạt mục tiêu (>80%), giảm động lực rút
            if players[idx].get('funding_progress', 0) > 0.8:
                withdraw_ratio *= 0.3
            
            max_ratio = min(0.6, 0.2 + (phase - 1) * 0.05)
            desired = invested * withdraw_ratio
            max_withdraw = invested * max_ratio
            actual = min(desired, max_withdraw)
            if actual > 0:
                # Giới hạn actual không vượt quá total_invested và available_cash
                actual = min(actual, players[idx]['total_invested'], players[idx]['available_cash'])
                if actual > 0:
                    players[idx]['available_cash'] -= actual
                    players[idx]['total_invested'] -= actual
                    players[idx]['funding_progress'] = max(0, players[idx]['total_invested'] / players[idx]['target_funding'])
                    alloc_entry['perProject'][idx] -= actual
                    alloc_entry['idle'] += actual
                    bot_actions.append({'bot_type': bot['type'], 'action': 'withdraw', 'player_index': idx, 'amount': actual})
                    logs.append(f"Bot {bot['type']} rút {actual:.0f} từ dự án {idx+1}")
                # Nếu actual = 0 thì không làm gì (không đủ tiền để rút)
                else:
                    players[idx]['status'] = 'bankrupt'
                    players[idx]['funding_progress'] = 0
                    players[idx]['total_invested'] = 0
                    logs.append(f"Dự án {idx+1} PHÁ SẢN!")

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
        
        # Thêm diversity penalty: dự án càng gần target thì càng bị phạt
        for j, idx in enumerate(candidates):
            already_invested = alloc_entry['perProject'][idx]
            saturation = already_invested / players[idx]['target_funding']   # 0..1
            diversity_penalty = saturation * 30
            shifted[j] = max(0, shifted[j] - diversity_penalty)
        
        sum_exp = sum(math.exp(a / 35) for a in shifted)   # đổi từ /20 thành /35
        probs = [math.exp(a / 35) / sum_exp for a in shifted]
        
        remaining = idle
        for _ in range(5):
            if remaining <= 0: break
            for j, idx in enumerate(candidates):
                invest = remaining * probs[j]
                invested_by_bot = alloc_entry['perProject'][idx]
                # giảm max_per_bot: 0.15 (phase 1) / 0.2 (các phase sau)
                max_per_bot = players[idx]['target_funding'] * (0.15 if phase == 1 else 0.2)
                cap = min(invest, max_per_bot - invested_by_bot)
                if cap > 0:
                    players[idx]['total_invested'] += cap
                    players[idx]['available_cash'] += cap
                    players[idx]['funding_progress'] = min(1.0, players[idx]['total_invested'] / players[idx]['target_funding'])
                    alloc_entry['perProject'][idx] += cap
                    remaining -= cap
                    bot_actions.append({'bot_type': bot['type'], 'action': 'invest', 'player_index': idx, 'amount': cap})
                    logs.append(f"Bot {bot['type']} đầu tư {cap:.0f} vào dự án {idx+1}")
                    if players[idx]['funding_progress'] >= 1.0 and players[idx].get('funding_complete_phase') is None:
                        players[idx]['funding_complete_phase'] = phase
        alloc_entry['idle'] = remaining

# ==================== FLASK APP & ROOMS ====================
import sqlite3
import json
from flask import g

class SqliteRoomManager:
    def __init__(self, db_path='game_state.db'):
        self.db_path = db_path
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('CREATE TABLE IF NOT EXISTS rooms (id TEXT PRIMARY KEY, data TEXT)')
    
    def _get_cache(self):
        if not hasattr(g, 'rooms_cache'):
            g.rooms_cache = {}
        return g.rooms_cache

    def __getitem__(self, key):
        cache = self._get_cache()
        if key in cache:
            return cache[key]
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT data FROM rooms WHERE id = ?', (key,))
            row = cursor.fetchone()
            if row:
                room = json.loads(row[0])
                cache[key] = room
                return room
            raise KeyError(key)

    def __setitem__(self, key, value):
        cache = self._get_cache()
        cache[key] = value

    def __contains__(self, key):
        try:
            self[key]
            return True
        except KeyError:
            return False

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def values(self):
        with sqlite3.connect(self.db_path, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT data FROM rooms')
            return [json.loads(row[0]) for row in cursor.fetchall()]

rooms = SqliteRoomManager()

@app.teardown_request
def save_rooms(exception=None):
    if hasattr(g, 'rooms_cache'):
        with sqlite3.connect(rooms.db_path, timeout=10) as conn:
            for key, room in g.rooms_cache.items():
                conn.execute('INSERT OR REPLACE INTO rooms (id, data) VALUES (?, ?)', (key, json.dumps(room)))

def try_start_game(room):
    ensure_room_lists(room)
    """Khởi tạo game khi tất cả người chơi đã chọn deck"""
    if room['status'] != 'choosing_deck':
        return False

    # Kiểm tra tất cả người chơi (đã submit project) đều đã chọn deck
    for i, p in enumerate(room['players']):
        if p is not None and not room['deck_ready'][i]:
            return False

    if not any(p is not None for p in room['players']):
        return False

    try:
        # Tính max_phase từ các dự án
        max_phase = max((p.get('max_phase', 5) for p in room['players'] if p is not None), default=5)
        room['max_phase'] = max_phase

        # Khởi tạo bot allocation
        room['bot_alloc'] = [
            {'bot_id': bot['id'], 'perProject': [0] * room['num_players'], 'idle': bot['wealth']}
            for bot in BOTS
        ]

        room['phase'] = 1
        room['status'] = 'playing'
        room['player_ready'] = [False] * room['num_players']
        room['logs'].append("🎮 Tất cả người chơi đã chọn deck. Game chính thức bắt đầu!")

        # Phát bài ban đầu cho người chơi active và chọn sự kiện khởi đầu
        for idx, p in enumerate(room['players']):
            if p and p.get('active_deck') and len(p['active_deck']) > 0:
                p['current_hand'] = draw_hand_no_duplicate_color_cost(p['active_deck'], 5)
                p['energy_left'] = 3
                scenario = random.choice(SCENARIOS)
                p['last_scenario'] = scenario['name']
                room['logs'].append(f"  → Player {idx+1} đã được chia {len(p['current_hand'])} lá bài. Sự kiện: {scenario['name']}")
            elif p:
                room['logs'].append(f"⚠️ Player {idx+1} không có deck hợp lệ, bỏ qua.")
        return True
    except Exception as e:
        room['logs'].append(f"❌ Lỗi khi bắt đầu game: {str(e)}")
        return False

@app.route('/')
def index():
    return render_template('host.html')

@app.route('/play/<room_id>/<int:player_index>')
def play_page(room_id, player_index):
    if room_id not in rooms:
        return "Phòng không tồn tại", 404
    room = rooms[room_id]
    ensure_room_lists(room)
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
        'bot_memory': {str(bot['id']): {'attractiveness_history': [[] for _ in range(num_players)]} for bot in BOTS},
        'submitted_players': 0,
        'name': None,
        'phase_details': []
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
    ensure_room_lists(room)

    if player_index >= len(room['players']):
        return jsonify({'error': 'Player index không hợp lệ'}), 400

    if room['players'][player_index] is not None:
        return jsonify({'error': 'Bạn đã submit dự án rồi'}), 400

    # Lưu tên phòng nếu chưa có
    if room.get('name') is None and 'project_name' in project_data:
        room['name'] = project_data['project_name']

    # Thêm max_phase dựa trên scale
    scale = project_data.get('scale', 'M')
    max_phase_map = {'S': 5, 'M': 7, 'L': 9}
    project_data['max_phase'] = max_phase_map.get(scale, 7)

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
        'security': 50,                     
        'reg_risk': 0,                      
        'active_deck': [],
        'reaction_hand': [],
        'current_hand': [],
        'energy_left': 3,
        'funding_complete_phase': None,
    })
    
    project_data['scale'] = scale   # lưu scale vào project
    
    room['players'][player_index] = project_data
    room['player_ready'][player_index] = True
    room['submitted_players'] += 1

    room['logs'].append(f"✅ Player {player_index + 1} đã submit dự án (scale {scale}, max_phase {project_data['max_phase']}).")

    # Tự động chuyển sang choosing_deck nếu đủ số lượng người chơi (>=2)
    if room['status'] == 'waiting_for_projects' and room['submitted_players'] >= 2:
        room['status'] = 'choosing_deck'
        room['logs'].append(f"🎮 Đã có {room['submitted_players']} người chơi. Bắt đầu giai đoạn chọn Deck!")

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
    ensure_room_lists(room)
    
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
    try:
        data = request.json
        room_id = data.get('room_id')
        player_index = data.get('player_index')
        active_indices = data.get('active_indices')
        reaction_indices = data.get('reaction_indices', [])

        # Validate input
        if not room_id or player_index is None:
            return jsonify({'error': 'Missing room_id or player_index'}), 400

        room = rooms.get(room_id)
        if not room:
            return jsonify({'error': 'Room not found'}), 404
        ensure_room_lists(room)

        if room['status'] not in ['waiting_for_projects', 'choosing_deck']:
            return jsonify({'error': 'Không phải lúc chọn deck (status: ' + room['status'] + ')'}), 400

        # Kiểm tra player tồn tại
        if player_index < 0 or player_index >= len(room['players']):
            return jsonify({'error': 'Player index out of range'}), 400

        proj = room['players'][player_index]
        if proj is None:
            return jsonify({'error': 'Player chưa submit dự án'}), 400

        if not isinstance(active_indices, list) or len(active_indices) != 22:
            return jsonify({'error': 'Phải chọn đúng 22 active cards'}), 400

        # Kiểm tra các index có hợp lệ không
        total_active = len(ACTIVE_CARDS_FULL)
        total_reaction = len(REACTION_CARDS)

        for idx in active_indices:
            if not isinstance(idx, int) or idx < 0 or idx >= total_active:
                return jsonify({'error': f'Active card index {idx} không hợp lệ (0..{total_active-1})'}), 400

        for idx in reaction_indices:
            if not isinstance(idx, int) or idx < 0 or idx >= total_reaction:
                return jsonify({'error': f'Reaction card index {idx} không hợp lệ (0..{total_reaction-1})'}), 400

        # Gán deck
        try:
            proj['active_deck'] = [ACTIVE_CARDS_FULL[i] for i in active_indices]
            proj['reaction_hand'] = [REACTION_CARDS[i].copy() for i in reaction_indices]
        except IndexError as e:
            room['logs'].append(f"❌ Lỗi IndexError khi gán deck cho Player {player_index+1}: {str(e)}")
            return jsonify({'error': f'Lỗi card index: {str(e)}'}), 400

        # Đánh dấu đã sẵn sàng
        room['deck_ready'][player_index] = True
        room['logs'].append(f"✅ Player {player_index + 1} đã chọn deck ({len(active_indices)} active, {len(reaction_indices)} reaction).")

        # Không tự động bắt đầu game, host sẽ nhấn RUN PHASE
        return jsonify({'ok': True, 'game_started': False})

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print("=== LỖI SUBMIT DECK ===")
        print(error_trace)
        if 'room_id' in locals() and room_id in rooms:
            rooms[room_id]['logs'].append(f"❌ Lỗi submit deck của Player {player_index+1}: {str(e)}")
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

@app.route('/api/auto_select_deck', methods=['POST'])
def auto_select_deck():
    """Tự động chọn deck ngẫu nhiên cho người chơi (chỉ tạo, không tự submit)"""
    data = request.json
    room_id = data['room_id']
    player_index = data['player_index']

    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    room = rooms[room_id]
    ensure_room_lists(room)

    if room['status'] not in ['waiting_for_projects', 'choosing_deck']:
        return jsonify({'error': 'Không thể chọn deck lúc này'}), 400

    proj = room['players'][player_index]
    if proj is None:
        return jsonify({'error': 'Player not found'}), 404

    # Chọn random 22 active cards từ ACTIVE_CARDS_FULL
    total_active = len(ACTIVE_CARDS_FULL)
    active_indices = random.sample(range(total_active), 22)
    
    # Chọn random 0-3 reaction cards
    total_reaction = len(REACTION_CARDS)
    num_reactions = random.randint(0, 3)
    reaction_indices = random.sample(range(total_reaction), num_reactions) if num_reactions > 0 else []

    # Chỉ lưu vào project, không tự động đánh dấu deck_ready
    proj['active_deck'] = [ACTIVE_CARDS_FULL[i] for i in active_indices]
    proj['reaction_hand'] = [REACTION_CARDS[i].copy() for i in reaction_indices]

    room['logs'].append(f"🤖 Player {player_index + 1} đã auto-chọn deck ngẫu nhiên (chưa submit).")

    return jsonify({
        'ok': True,
        'active_indices': active_indices,
        'reaction_indices': reaction_indices,
        'message': f'Đã tạo {len(active_indices)} active cards và {len(reaction_indices)} reaction cards ngẫu nhiên. Bạn có thể chỉnh sửa trước khi submit.'
    })



@app.route('/api/host_state', methods=['GET'])
def host_state():
    room_id = request.args.get('room_id')
    if not room_id or room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    room = rooms[room_id]
    ensure_room_lists(room)
    rankings = []
    
    for i, proj in enumerate(room['players']):
        if proj:
            is_ended = proj.get('status') in ['ended', 'funded', 'bankrupt'] or proj.get('current_phase', 0) >= proj.get('max_phase', 5)
            if is_ended:
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
                'security': proj.get('security', 50),
                'reg_risk': proj.get('reg_risk', 0),
                'score': score,
                'scale': proj.get('scale', 'M'),
                'status': proj.get('status', 'active'),
                'current_phase': proj.get('current_phase', 0),
                'max_phase': proj.get('max_phase', 5),
                'deck_ready': room.get('deck_ready', [False])[i] if i < len(room.get('deck_ready', [])) else False
            })
        else:
            rankings.append({'name': f"Player {i+1}", 'funding': 0, 'score': 0, 'status': 'not_joined', 'deck_ready': False})
    
    return jsonify({
        'status': room['status'],
        'phase': room['phase'],
        'max_phase': room['max_phase'],
        'players_joined': room.get('submitted_players', 0),
        'max_players': room['num_players'],
        'logs': room.get('logs', [])[-40:],
        'rankings': rankings,
        'can_start_deck': room['status'] == 'waiting_for_projects' and room.get('submitted_players', 0) >= 2,
        'submitted_count': room.get('submitted_players', 0),
        'game_started': room['status'] == 'playing'
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
    ensure_room_lists(room)
    if player_index < 0 or player_index >= len(room['players']) or room['players'][player_index] is None:
        return jsonify({
            'joined': False,
            'status': room.get('status', 'waiting'),
            'choosing_deck': room['status'] == 'choosing_deck',
            'game_started': room['status'] == 'playing',
            'game_ended': room.get('game_ended', False)
        }), 200
    
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
    
    if proj.get('status') == 'bankrupt':
        final_score_value = -100
    elif is_ended:
        # Tính điểm cho MỌI dự án đã kết thúc (kể cả funding < 50%)
        final_score_value = final_score(proj, proj.get('max_phase', 5), metrics)
    
    triggers = room.get('player_triggers', [{}])[player_index] if player_index < len(room.get('player_triggers', [])) else {}
    
    return jsonify({
        'status': room.get('status', 'waiting'),
        'phase': room.get('phase', 0),
        'max_phase': proj.get('max_phase', 7),
        'last_scenario': proj.get('last_scenario', 'Chưa có sự kiện'),
        'metrics': {
            'intrinsic': metrics.get('intrinsic', 0),
            'valuation_sanity': metrics.get('valuation_sanity', 0),
            'roi_norm': metrics.get('roi_norm', 0),
            'runway': metrics.get('runway', 0),
            'funding_progress': proj.get('funding_progress', 0)
        },
        'ready': room.get('player_ready', [False])[player_index] if player_index < len(room.get('player_ready', [])) else False,
        'choosing_deck': room['status'] == 'choosing_deck' or (room['status'] == 'waiting_for_projects' and proj is not None),
        'game_started': room['status'] == 'playing',
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
        'triggers': triggers.get('available_reactions', []),
        'deck_ready': room.get('deck_ready', [False])[player_index] if player_index < len(room.get('deck_ready', [])) else False,
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
    ensure_room_lists(room)
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
    room.setdefault('pending_cards', {})[str(player_index)] = copy.deepcopy(card)
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
    ensure_room_lists(room)
    
    # ===== TRƯỜNG HỢP: GAME ĐANG Ở GIAI ĐOẠN CHỌN DECK =====
    if room['status'] == 'choosing_deck':
        # 1. Kiểm tra đã có đủ số người chơi theo num_players chưa?
        if room.get('submitted_players', 0) < room['num_players']:
            return jsonify({
                'error': f'Chưa đủ người chơi: cần {room["num_players"]} người, mới có {room["submitted_players"]}. Vui lòng chờ thêm người tham gia.'
            }), 400

        # 2. Kiểm tra tất cả người chơi đã submit deck chưa?
        not_ready = []
        for i in range(room['num_players']):
            # Vì đã đủ người nên players[i] chắc chắn không None
            if not room['deck_ready'][i]:
                not_ready.append(i + 1)   # số thứ tự player (1-based)

        if not_ready:
            return jsonify({
                'error': f'Các player {not_ready} chưa submit deck. Vui lòng chờ họ hoàn tất.'
            }), 400

        # 3. Đủ điều kiện -> khởi tạo game
        success = try_start_game(room)
        if not success:
            return jsonify({'error': 'Không thể khởi tạo game. Kiểm tra deck của từng người chơi.'}), 400

        room['player_ready'] = [False] * room['num_players']
        room['logs'].append("🚀 Game đã được khởi tạo. Các người chơi cần nhấn READY cho Phase 1, sau đó host nhấn RUN PHASE lần nữa.")
        return jsonify({
            'game_started': True,
            'phase': room['phase'],
            'message': 'Game started. Please wait for players to ready and click RUN PHASE again.'
        })


    # ===== 2. CHỈ CHO PHÉP CHẠY KHI GAME Ở TRẠNG THÁI PLAYING =====
    if room['status'] != 'playing':
        return jsonify({'error': 'Game not active'}), 400

    ensure_bot_alloc(room)

    phase = room['phase']
    players = room['players']
    logs = []

    # ===== 3. KIỂM TRA TẤT CẢ ACTIVE PLAYER ĐÃ READY =====
    active_indices = []
    for i, p in enumerate(players):
        if p and p.get('status') == 'active' and p.get('current_phase', 0) < p.get('max_phase', 999):
            active_indices.append(i)
    not_ready = [i for i in active_indices if not room['player_ready'][i]]
    if not_ready:
        return jsonify({'error': f'Players {[i+1 for i in not_ready]} chưa ready'}), 400

    logs.append(f"🚀 BẮT ĐẦU PHASE {phase}")

    # Reset triggers
    for i in range(room['num_players']):
        room['player_triggers'][i] = {'available_reactions': []}

    # Xử lý scenario và thẻ đã chơi
    for idx, proj in enumerate(players):
        if not proj or proj.get('status') != 'active' or proj.get('current_phase', 0) >= proj.get('max_phase', 999):
            continue

        # Lấy sự kiện đã được gán cho phase này
        scenario_name = proj.get('last_scenario')
        scenario = next((s for s in SCENARIOS if s['name'] == scenario_name), None)
        if not scenario:
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
        
        # ========== CÁC DELTA MỚI ==========
        if 'funding_boost_percent' in d:
            boost = (d['funding_boost_percent'] / 100) * proj['target_funding']
            new_total = proj['total_invested'] + boost
            if new_total < 0:
                boost = -proj['total_invested']   # chỉ giảm đến 0
            proj['total_invested'] += boost
            proj['available_cash'] += boost
            proj['funding_progress'] = min(1.0, max(0, proj['total_invested'] / proj['target_funding']))
            logs.append(f" → Dự án {idx+1}: funding_boost {d.get('funding_boost_percent',0)}%, total_invested={proj['total_invested']:.0f}, progress={proj['funding_progress']:.2f}")
        
        if 'security' in d:
            proj['security'] = clamp(proj.get('security', 50) + d['security'], 0, 100)
        
        if 'visibility' in d:
            proj['visibility'] = clamp(proj.get('visibility', 50) + d['visibility'], 0, 100)
        
        if 'whale_trust' in d:
            for bot in BOTS:
                if bot['type'] == 'Whale':
                    bid = bot['id']
                    proj['trust_scores'][bid] = clamp(proj['trust_scores'].get(bid, 50) + d['whale_trust'], 0, 100)
        
        if 'cost_percent' in d:
            cost = (d['cost_percent'] / 100) * proj['target_funding']
            proj['available_cash'] -= cost
        
        # Sửa lại xử lý reg_risk (lưu thành biến riêng, không dùng legal_cost_spent)
        if 'reg_risk' in d:
            proj['reg_risk'] = clamp(proj.get('reg_risk', 0) + d['reg_risk'], 0, 100)
            # (Tuỳ chọn) Nếu muốn reg_risk vẫn ảnh hưởng đến chi phí pháp lý:
            # cost = (abs(d['reg_risk']) / 100) * proj['target_funding']
            # proj['legal_cost_spent'] += cost

        # Áp dụng thẻ đã chơi (pending_cards)
        pending_key = str(idx)
        pending_cards = room.get('pending_cards', {})
        if pending_key in pending_cards or idx in pending_cards:
            card = pending_cards.get(pending_key, pending_cards.get(idx))
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
                    new_total = proj['total_invested'] + boost
                    if new_total < 0:
                        boost = -proj['total_invested']
                    proj['total_invested'] += boost
                    proj['available_cash'] += boost
                    proj['funding_progress'] = min(1.0, max(0, proj['total_invested'] / proj['target_funding']))
                if 'cost_percent' in eff:
                    proj['available_cash'] -= (eff['cost_percent'] / 100) * proj['target_funding']
                if 'visibility' in eff:
                    proj['visibility'] = clamp(proj.get('visibility', 50) + eff['visibility'], 0, 100)
                logs.append(f" → Dự án {idx+1} chơi thẻ {card['name']}")

        # Kích hoạt reaction (chỉ hiển thị, không tự động dùng)
        triggers = []
        metrics = calculate_metrics(proj)  # tính metrics để dùng nhiều lần
        
        for rc in proj.get('reaction_hand', []):
            trigger = rc.get('trigger')
            
            # 1. on_scenario_market_bad (giữ cũ)
            if trigger == 'on_scenario_market_bad' and scenario['cat'] == 'Market':
                if any(k in scenario['name'].lower() for k in ['crisis', 'slow', 'khủng', 'xấu']):
                    triggers.append(rc)
            
            # 2. on_transparency_low (giữ cũ, ngưỡng 25 theo card mới)
            elif trigger == 'on_transparency_low' and proj['transparency'] < 25:
                triggers.append(rc)
            
            # 3. on_reg_risk_high (giữ cũ)
            elif trigger == 'on_reg_risk_high':
                reg = (proj['legal_cost_spent'] / proj['target_funding']) * 100 if proj['target_funding'] > 0 else 0
                if reg > 70:
                    triggers.append(rc)
            
            # 4. on_hype_high (giữ cũ)
            elif trigger == 'on_hype_high' and proj['hype'] > 80:
                triggers.append(rc)
            
            # 5. on_runway_warning (mới) - runway <= 2
            elif trigger == 'on_runway_warning' and metrics.get('runway', 999) <= 2:
                triggers.append(rc)
            
            # 6. on_near_bankruptcy (mới) - runway <= 1
            elif trigger == 'on_near_bankruptcy' and metrics.get('runway', 999) <= 1:
                triggers.append(rc)
            
            # 7. on_trust_low (mới) - trust_all < 20
            elif trigger == 'on_trust_low' and proj['trust_scores'] and (sum(proj['trust_scores'].values()) / len(proj['trust_scores'])) < 20:
                triggers.append(rc)
            
            # 8. on_customer_trust_low (mới) - trust_all < 10
            elif trigger == 'on_customer_trust_low' and proj['trust_scores'] and (sum(proj['trust_scores'].values()) / len(proj['trust_scores'])) < 10:
                triggers.append(rc)
            
            # 9. on_visibility_collapse (mới) - visibility < 25
            elif trigger == 'on_visibility_collapse' and proj.get('visibility', 50) < 25:
                triggers.append(rc)
            
            # 10. on_cogs_rise (mới) - cogs > 0.6 (lấy từ material hoặc labor tổng hợp, tạm dùng material)
            elif trigger == 'on_cogs_rise' and proj.get('material', 0) > 0.6:
                triggers.append(rc)
            
            # 11. on_security_low (mới) - security < 20
            elif trigger == 'on_security_low' and proj.get('security', 50) < 20:
                triggers.append(rc)
            
            # 12. on_bot_withdraw (giữ cũ)
            elif trigger == 'on_bot_withdraw':
                # Bot withdraw event được xử lý riêng ở process_phase, ở đây ta có thể bỏ qua hoặc giữ logic cũ
                # Tuy nhiên trong code cũ không có event bot_withdraw ở đây, nên giữ nguyên nếu muốn
                # Để an toàn, ta vẫn thêm điều kiện false vì event này không xảy ra trong vòng lặp này
                pass
        
        if triggers:
            room['player_triggers'][idx]['available_reactions'] = triggers
            logs.append(f" → Dự án {idx+1} có {len(triggers)} reaction có thể kích hoạt")

    # Snapshot starting cash for each player before bot processing
    starting_cash = {}
    for idx, proj in enumerate(players):
        if proj:
            starting_cash[idx] = proj.get('available_cash', 0)

    # Xử lý bot đầu tư/rút vốn
    bot_actions = []
    process_phase(room, phase, players, logs, bot_actions)

    # Chỉ kết thúc dự án sau khi phase hiện tại đã chạy đủ scenario/card/bot.
    for idx, proj in enumerate(players):
        if proj and proj.get('status') == 'active' and idx in active_indices:
            proj['current_phase'] = proj.get('current_phase', 0) + 1
            if proj['current_phase'] >= proj.get('max_phase', 999):
                proj['status'] = 'ended'
                logs.append(f" → Dự án {idx+1} đã kết thúc sau phase {phase}.")

    # Dọn dẹp sau phase
    room['pending_cards'] = {}
    room['player_ready'] = [False] * room['num_players']
    room['logs'] = logs[-50:]

    # Tăng phase và chia bài mới, đồng thời chọn sự kiện cho phase tiếp theo
    room['phase'] += 1
    for idx, proj in enumerate(players):
        if proj and proj.get('status') == 'active' and proj.get('current_phase', 0) < proj.get('max_phase', 999):
            proj['current_hand'] = draw_hand_no_duplicate_color_cost(proj['active_deck'], 5)
            proj['energy_left'] = 3
            room['mulligan_used'][idx] = False
            next_scenario = random.choice(SCENARIOS)
            proj['last_scenario'] = next_scenario['name']

    # Kiểm tra game kết thúc
    all_ended = all(
        p is None
        or p.get('status') in ['ended', 'funded', 'bankrupt']
        or p.get('current_phase', 0) >= p.get('max_phase', 999)
        for p in players
    )
    game_ended = (room['phase'] > room['max_phase']) or all_ended
    if game_ended:
        room['game_ended'] = True
        room['status'] = 'ended'

    # Lưu phase details with bot actions and cash flow
    phase_detail = {
        'phase': phase,
        'date': str(uuid.uuid4())[:8],
        'event': f"End of Phase {phase}",
        'bot_actions': aggregate_bot_actions(bot_actions),
        'players': []
    }
    for idx, proj in enumerate(players):
        if proj:
            ending_cash = proj.get('available_cash', 0)
            start = starting_cash.get(idx, 0)
            phase_detail['players'].append({
                'name': f'Player {idx+1}',
                'status': proj.get('status', 'active'),
                'funding': proj.get('funding_progress', 0),
                'available_cash': ending_cash,
                'cash_flow': ending_cash - start
            })
    room.setdefault('phase_details', []).append(phase_detail)

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

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Backend đang chạy'})

@app.route('/api/rooms', methods=['POST'])
def api_create_room():
    data = request.json
    room_name = data.get('name', 'Startup Game')
    max_players = data.get('maxPlayers', 4)
    
    room_id = str(uuid.uuid4())[:8]
    base_url = request.host_url.rstrip('/')
    
    rooms[room_id] = {
        'num_players': max_players,
        'players': [None] * max_players,
        'phase': 0,
        'max_phase': 0,
        'status': 'waiting_for_projects',
        'bot_alloc': None,
        'logs': ["Phòng đã tạo. Chờ người chơi submit dự án..."],
        'player_ready': [False] * max_players,
        'deck_ready': [False] * max_players,
        'pending_cards': {},
        'phase_energy': [3] * max_players,
        'mulligan_used': [False] * max_players,
        'game_ended': False,
        'player_triggers': [{} for _ in range(max_players)],
        'bot_memory': {str(bot['id']): {'attractiveness_history': [[] for _ in range(max_players)]} for bot in BOTS},
        'submitted_players': 0,
        'name': room_name,
        'phase_details': []
    }
    
    join_links = []
    for i in range(max_players):
        join_links.append({
            'playerIndex': i,
            'playerName': f'Player {i+1}',
            'realLink': f"{base_url}/play/{room_id}/{i}"
        })
    
    return jsonify({
        'id': room_id,
        'name': room_name,
        'maxPlayers': max_players,
        'joinLinks': join_links
    })

@app.route('/api/rooms/<room_id>', methods=['GET'])
def api_get_room(room_id):
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    room = rooms[room_id]
    ensure_room_lists(room)

    
    
    players_list = []
    for i, proj in enumerate(room.get('players', [])):
        if proj:
            # Tính metrics và score thực tế
            metrics = calculate_metrics(proj)
            # Nếu dự án đã kết thúc hoặc đạt max phase
            if proj.get('status') in ['ended', 'funded', 'bankrupt'] or proj.get('current_phase', 0) >= proj.get('max_phase', 5):
                score = final_score(proj, proj.get('max_phase', 5), metrics)
            else:
                # Score tạm thời dựa trên số phase đã qua (nếu có)
                current_phase = proj.get('current_phase', 0)
                score = final_score(proj, current_phase, metrics) if current_phase > 0 else 0
            players_list.append({
                'id': i,
                'name': f'Player {i+1}',
                'status': proj.get('status', 'active'),
                'funding': proj.get('funding_progress', 0),
                'hype': proj.get('hype', 50),
                'transparency': proj.get('transparency', 50),
                'score': score,
                'scale': proj.get('scale', 'M'),
                'current_phase': proj.get('current_phase', 0),
                'max_phase': proj.get('max_phase', 5),
                'deck_ready': room.get('deck_ready', [False])[i] if i < len(room.get('deck_ready', [])) else False,
                'ready': room.get('player_ready', [False])[i] if i < len(room.get('player_ready', [])) else False  
            })
        else:
            players_list.append({
                'id': i,
                'name': f'Player {i+1}',
                'status': 'not_joined',
                'funding': 0,
                'hype': 50,
                'transparency': 50,
                'score': 0,
                'scale': 'M',
                'current_phase': 0,
                'max_phase': 5,
                'deck_ready': False,
                'ready': False
            })
    
    base_url = request.host_url.rstrip('/')
    join_links = []
    for i in range(room.get('num_players', 4)):
        join_links.append({
            'playerIndex': i,
            'playerName': f'Player {i+1}',
            'realLink': f"{base_url}/play/{room_id}/{i}"
        })
    
    joined_players = len([p for p in room.get('players', []) if p is not None])
    
    raw_phase = room.get('phase', 0)
    max_phase = room.get('max_phase', 0)
    display_phase = min(raw_phase, max_phase) if max_phase > 0 else raw_phase
    phase_progress = min(100, (display_phase / max_phase) * 100) if max_phase > 0 else 0
    phase_details = []
    for detail in room.get('phase_details', []):
        if isinstance(detail, dict):
            compact_detail = detail.copy()
            compact_detail['bot_actions'] = aggregate_bot_actions(detail.get('bot_actions', []))
            phase_details.append(compact_detail)

    return jsonify({
        'name': room.get('name', 'Game Room'),
        'maxPlayers': room.get('num_players', 4),
        'joinedPlayers': joined_players,
        'currentPhase': display_phase,
        'maxPhase': room.get('max_phase', 7),
        'ended': room.get('game_ended', False),
        'players': players_list,
        'logs': room.get('logs', []),
        'phaseDetails': phase_details,
        'joinLinks': join_links,
        'can_start_deck': room['status'] == 'waiting_for_projects' and room.get('submitted_players', 0) >= 2,
        'status': room['status'],
        'game_started': room['status'] == 'playing',
        'phase_progress': phase_progress   # thêm dòng này
    })

@app.route('/api/rooms/<room_id>/next-phase', methods=['POST'])
def api_next_phase(room_id):
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    room = rooms[room_id]
    
    if room.get('players') and any(p for p in room['players'] if p):
        phase_details = {
            'phase': room.get('phase', 0),
            'date': str(uuid.uuid4())[:8],
            'event': f"End of Phase {room.get('phase', 0)}",
            'players': []
        }
        for i, p in enumerate(room['players']):
            if p:
                phase_details['players'].append({
                    'name': f'Player {i+1}',
                    'status': p.get('status', 'active'),
                    'funding': p.get('funding_progress', 0),
                    'available_cash': p.get('available_cash', 0),
                    'cash_flow': 0
                })
        
        if 'phase_details' not in room:
            room['phase_details'] = []
        room['phase_details'].append(phase_details)
    
    room['phase'] = room.get('phase', 0) + 1
    room['player_ready'] = [False] * room.get('num_players', 4)
    
    return jsonify({'success': True, 'phase': room.get('phase', 0)})

@app.route('/api/rooms/<room_id>/random-event', methods=['POST'])
def api_random_event(room_id):
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    room = rooms[room_id]
    scenario = random.choice(SCENARIOS)
    
    if 'logs' not in room:
        room['logs'] = []
    room['logs'].append(f"🎲 Sự kiện ngẫu nhiên: {scenario['name']}")
    
    for proj in room.get('players', []):
        if proj and proj.get('status') == 'active':
            d = scenario['delta']
            if 'hype' in d:
                proj['hype'] = clamp(proj.get('hype', 50) + d['hype'], 0, 100)
            if 'transparency' in d:
                proj['transparency'] = clamp(proj.get('transparency', 50) + d['transparency'], 0, 100)
    
    return jsonify({'success': True, 'event': scenario['name']})

@app.route('/api/rooms/<room_id>/reset-phase', methods=['POST'])
def api_reset_phase(room_id):
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    room = rooms[room_id]
    
    if room.get('phase', 0) > 0:
        room['phase'] = max(0, room['phase'] - 1)
    
    room['logs'] = room.get('logs', []) + [f"🔄 Phase đã được reset về {room['phase']}"]
    
    return jsonify({'success': True, 'phase': room.get('phase', 0)})

@app.route('/api/rooms/<room_id>/end', methods=['POST'])
def api_end_game(room_id):
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    room = rooms[room_id]
    room['game_ended'] = True
    room['status'] = 'ended'
    room['logs'].append("🏁 Game đã kết thúc bởi host!")
    
    return jsonify({'success': True})

@app.route('/api/rooms/<room_id>/reset', methods=['POST'])
def api_reset_game(room_id):
    if room_id not in rooms:
        return jsonify({'error': 'Room not found'}), 404
    
    room = rooms[room_id]
    
    room['phase'] = 0
    room['game_ended'] = False
    room['status'] = 'waiting_for_projects'
    room['players'] = [None] * room.get('num_players', 4)
    room['submitted_players'] = 0
    room['player_ready'] = [False] * room.get('num_players', 4)
    room['deck_ready'] = [False] * room.get('num_players', 4)
    room['pending_cards'] = {}
    room['mulligan_used'] = [False] * room.get('num_players', 4)
    room['player_triggers'] = [{} for _ in range(room.get('num_players', 4))]
    room['logs'] = ["🔄 Game đã được reset. Chờ người chơi submit dự án..."]
    room['phase_details'] = []
    
    room['bot_memory'] = {
        str(bot['id']): {'attractiveness_history': [[] for _ in range(room.get('num_players', 4))]}
        for bot in BOTS
    }
    
    return jsonify({'success': True})

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return jsonify({'error': e.description}), e.code

    import traceback
    error_trace = traceback.format_exc()
    print("=== UNHANDLED EXCEPTION ===")
    print(error_trace)
    return jsonify({'error': f'Internal Server Error: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)





