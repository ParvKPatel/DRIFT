import csv
import random
import uuid

# Fixed random seed for reproducibility
random.seed(42)

TOTAL_RECORDS = 4000

# 15-20% ambiguous
# ~70% routine/low-risk
# ~20% high-risk
# ~10% critical SIF

CATEGORIES = [
    "Working at Height", "Energy Isolation / LOTO", "Confined Space", "Hot Work", 
    "Lifting Operations", "Dropped Objects", "Vehicle Movement", "Excavation", 
    "Chemical Exposure", "Hydrocarbon Leaks", "Gas Releases", "Fire", 
    "Process Upsets", "Overpressure", "Electrical Hazards", "Simultaneous Operations", 
    "Housekeeping", "PPE observations", "Minor maintenance issues", "Routine inspections"
]

ROUTINE_TEMPLATES = [
    "During routine {cat} inspection, noticed minor debris which was cleared immediately.",
    "Worker observed not wearing full PPE during {cat} in the safe zone. Reminded and complied.",
    "Minor oil weepage noticed on valve body during {cat}. Cleaned and tightened.",
    "Walkway obstructed by empty pallets near {cat} area. Removed by housekeeping.",
    "Routine {cat} completed without any safety incidents.",
    "Handrail paint was peeling near the {cat} sector. Maintenance request submitted.",
    "Fire extinguisher tag missing in the {cat} zone. Replaced by safety officer.",
    "Slight trip hazard identified at {cat} location due to uneven grating. Marked with high-viz tape.",
    "Contractor reminded to use three points of contact on stairs near {cat} unit.",
    "Completed daily {cat} checks. All parameters normal."
]

HIGH_RISK_TEMPLATES = [
    "While performing {cat}, a heavy wrench slipped and struck the scaffolding tube near the worker's head. Near miss.",
    "Hydraulic hose burst during {cat}, spraying fluid across the deck. Operator was wearing face shield, no injury.",
    "During {cat}, LEL alarms triggered at 10%. Work stopped and area ventilated.",
    "Crane slewed unexpectedly during {cat}, load swung over the pedestrian walkway. Exclusion zone was active, no personnel exposed.",
    "Contractor found entering restricted {cat} area without a valid permit. Escorted out and work stopped.",
    "Scaffold tag was red but workers were seen preparing for {cat} on it. Intervened before access.",
    "Small localized smoldering fire observed during {cat} hot work. Extinguished immediately with local fire watch.",
    "Worker bypassed machine guard during {cat} to clear a jam. Equipment was still energized. Intervened and applied LOTO."
]

CRITICAL_TEMPLATES = [
    "Catastrophic failure of lifting gear during {cat}. 5-ton load dropped 10 meters, striking the deck less than 2 meters from the rigging crew.",
    "Worker fell 5 meters during {cat} because harness lanyard snapped. Rushed to medical bay with suspected fractures.",
    "Major hydrocarbon gas release during {cat}. Cloud drifted towards hot work area. Emergency shutdown activated immediately.",
    "Arc flash occurred during {cat} in the main switchgear room. Technician suffered severe electrical burns to face and hands.",
    "Trench collapsed during {cat} excavation. Worker was partially buried up to the waist. Rescue team deployed.",
    "Vehicle struck a pedestrian crossing the yard during {cat}. Severe trauma sustained, medevac initiated."
]

AMBIGUOUS_TEMPLATES = [
    "Received report of incident during {cat}. Could not verify details.",
    "Loud bang heard near {cat} unit, but no damage found and no one saw anything.",
    "Someone said the pressure was high during {cat}. Need to investigate further.",
    "Worker reported feeling unwell after {cat}. Might be related, might be food poisoning.",
    "Found some fluid on the deck near {cat}. Not sure if water or oil.",
    "The gauge looked weird during {cat}. We left it alone.",
    "Contractor dropped something during {cat}. Didn't see what it was."
]

MESSY_ADDITIONS = [
    " It was raining heavily at the time.",
    " The contractor was late to the shift.",
    " Lunch had just finished.",
    " The supervisor was not present.",
    " Radio comms were a bit staticky.",
    " We had a safety meeting about this just yesterday.",
    " The shift was almost over.",
    " I didn't have my glasses on but I saw it happen.",
    " (Note: Please fix the AC in the control room it is too hot)."
]

def generate_report(report_idx: int) -> dict:
    # Determine risk tier based on weighted probability
    # Ambiguous: 25%
    # Routine: 25%
    # High: 25%
    # Critical: 25%
    rand = random.random()
    cat = random.choice(CATEGORIES)
    
    if rand < 0.25:
        narrative = random.choice(AMBIGUOUS_TEMPLATES).format(cat=cat)
    elif rand < 0.50:
        narrative = random.choice(ROUTINE_TEMPLATES).format(cat=cat)
    elif rand < 0.75:
        narrative = random.choice(HIGH_RISK_TEMPLATES).format(cat=cat)
    else:
        narrative = random.choice(CRITICAL_TEMPLATES).format(cat=cat)
    
    # 20% chance to add messy context
    if random.random() < 0.20:
        narrative += random.choice(MESSY_ADDITIONS)
        
    # 10% chance to have a typo
    if random.random() < 0.10:
        narrative = narrative.replace("the ", "teh ").replace("was ", "ws ")
        
    # Generate unique OIL-style ID
    report_id = f"OIL-{2026}-{(report_idx+1):05d}"
    
    site_names = ['Offshore Platform Alpha', 'Refinery Unit B', 'Terminal Operations', 'Pipeline Sector 4', 'Maintenance Yard', 'Drilling Rig Delta']
    
    return {
        "report_id": report_id,
        "site": random.choice(site_names),
        "narrative": narrative
    }

def main():
    print("Generating OIL Stress Test Dataset...")
    reports = [generate_report(i) for i in range(TOTAL_RECORDS)]
    
    filename = "/Users/parvpatel/SIH MVP/oil_sample_dataset.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["report_id", "site", "narrative"])
        writer.writeheader()
        writer.writerows(reports)
        
    print(f"Successfully generated {TOTAL_RECORDS} records to {filename}")

if __name__ == "__main__":
    main()
