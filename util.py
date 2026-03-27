# utils.py

def get_action_plan(risks):
    """
    Transforms risk levels into a structured Standard Operating Procedure (SOP).
    """
    plan = []

    # 1. HEAT & HUMIDITY (Health Domain)
    if risks.get('heat_stress') == "Extreme Danger":
        plan.append({
            "Domain": "🏥 Health",
            "Severity": "🔴 Critical",
            "SOP": "Heatstroke Protocol: Suspend all outdoor activity. Activate campus cooling zones."
        })
    elif risks.get('heat') == "High":
        plan.append({
            "Domain": "🏥 Health",
            "Severity": "🟠 High",
            "SOP": "Hydration Alert: Mandatory water breaks every 30 mins for outdoor staff/students."
        })

    # 2. RAINFALL (Infrastructure Domain)
    if risks.get('flood') == "Critical":
        plan.append({
            "Domain": "🚗 Transport",
            "Severity": "🔴 Critical",
            "SOP": "Flash Flood Warning: Avoid low-lying parking areas. Check Varikoli bridge levels."
        })
    elif risks.get('flood') == "Warning":
        plan.append({
            "Domain": "🏠 Safety",
            "Severity": "🟡 Medium",
            "SOP": "Heavy Rain: Ensure all lab equipment near windows is secured and unplugged."
        })

    # 3. AIR QUALITY (Environmental Domain)
    if risks.get('air') == "Unhealthy":
        plan.append({
            "Domain": "🫁 Respiratory",
            "Severity": "🟠 High",
            "SOP": "Air Quality Alert: Wear N95 masks. Switch AC units to internal circulation mode."
        })

    # 4. DEFAULT CASE
    if not plan:
        plan.append({
            "Domain": "✅ System",
            "Severity": "🟢 Stable",
            "SOP": "Nominal Conditions: No specialized environmental protocols required."
        })

    return plan