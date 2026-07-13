#!/usr/bin/env python3
"""
Create sample PDF files for MoD Semantic Search demo

This script generates simple PDF files based on the manifest data.
The PDFs contain text content that matches the descriptions and purposes
outlined in the manifest.
"""

import os
import sys
from pathlib import Path

# Check if reportlab is available
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def create_text_file_fallback(filepath, title, content):
    """Create a simple text file if reportlab is not available"""
    with open(filepath, 'w') as f:
        f.write(f"{title}\n")
        f.write("=" * len(title) + "\n\n")
        f.write(content)
    print(f"  ✓ Created text file: {filepath}")


def create_pdf(filepath, title, content):
    """Create a PDF file with the given title and content"""
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()

    # Define custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='darkblue',
        spaceAfter=30,
        alignment=TA_CENTER
    )

    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=12
    )

    # Build document
    story = []

    # Add title
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.3 * inch))

    # Add content paragraphs
    paragraphs = content.split('\n\n')
    for para in paragraphs:
        if para.strip():
            story.append(Paragraph(para.strip(), body_style))
            story.append(Spacer(1, 0.1 * inch))

    # Build PDF
    doc.build(story)
    print(f"  ✓ Created PDF: {filepath}")


# PDF Content definitions
PDF_CONTENTS = {
    "challenger2_technical.pdf": {
        "title": "Challenger 2 Main Battle Tank Technical Overview",
        "content": """
UNCLASSIFIED

1. INTRODUCTION

The Challenger 2 is the British Army's main battle tank, representing a significant advancement in armored vehicle technology. This technical overview provides essential information on the vehicle's specifications, systems, and operational capabilities.

2. GENERAL SPECIFICATIONS

Weight: 62.5 tonnes (combat loaded)
Length: 8.3m (hull), 11.55m (gun forward)
Width: 3.5m
Height: 2.49m
Crew: 4 (commander, gunner, loader, driver)
Maximum speed: 59 km/h (road), 40 km/h (cross-country)
Range: 550 km (road)
Engine: Perkins CV12 diesel, 1200 hp

3. ARMAMENT

Main gun: 120mm L30A1 rifled gun
Secondary armament: 7.62mm L94A1 chain gun, 7.62mm L37A2 machine gun
Ammunition capacity: 50 rounds (main gun), 4,000 rounds (chain gun)

The 120mm rifled gun provides exceptional accuracy at long ranges and can fire APFSDS, HESH, and smoke rounds.

4. ARMOR PROTECTION

The Challenger 2 features Chobham armor, providing excellent protection against kinetic energy and chemical energy threats. Additional explosive reactive armor (ERA) can be fitted for enhanced protection in high-threat environments.

5. FIRE CONTROL SYSTEM

Advanced digital fire control system with:
- Thermal imaging sights
- Laser rangefinder
- Ballistic computer
- Stabilized gun and sight systems
- Hunter-killer capability

6. MOBILITY

The vehicle's Hydrogas suspension system provides excellent cross-country mobility while maintaining gun stability. The powerpack can be removed and replaced in under 90 minutes for maintenance.

7. OPERATIONAL NOTES

The Challenger 2 has proven its effectiveness in various operational environments, from desert to urban terrain. Regular maintenance is essential to maintain peak operational readiness.

8. MAINTENANCE REQUIREMENTS

Daily: Visual inspections, fluid level checks, communication system tests
Weekly: Detailed mechanical inspections, track tension checks, weapon system verification
Monthly: Comprehensive system diagnostics, major component inspections

For detailed maintenance procedures, refer to the technical maintenance manual.

UNCLASSIFIED
"""
    },

    "as90_maintenance.pdf": {
        "title": "AS90 Self-Propelled Artillery Maintenance Guide",
        "content": """
UNCLASSIFIED

AS90 BRAVEHEART SELF-PROPELLED ARTILLERY
FIELD MAINTENANCE GUIDE

1. SYSTEM OVERVIEW

The AS90 is a 155mm self-propelled artillery system designed to provide mobile fire support. This guide covers essential field maintenance procedures to ensure operational readiness.

2. DAILY MAINTENANCE PROCEDURES

2.1 External Inspection
- Inspect tracks for damage, wear, and proper tension
- Check road wheels and return rollers for damage
- Examine hull and turret for cracks or structural damage
- Verify all external equipment is properly secured
- Inspect hydraulic systems for leaks

2.2 Weapon System Check
- Visually inspect the 155mm howitzer barrel for obstructions
- Check recoil system for proper operation
- Verify breach mechanism operates smoothly
- Inspect firing mechanisms and safety systems
- Test elevation and traverse systems

2.3 Fluid Levels
- Engine oil: Check dipstick, maintain between min/max marks
- Coolant: Verify proper level in expansion tank
- Hydraulic fluid: Check all reservoir levels
- Fuel: Document fuel state

3. WEEKLY MAINTENANCE

3.1 Mechanical Systems
- Perform detailed track inspection and adjustment
- Lubricate all grease points per technical manual
- Test all electrical systems including communications
- Verify fire control computer functionality
- Inspect ammunition handling system

3.2 Safety Systems
- Test fire suppression system
- Verify NBC protection system operation
- Check emergency escape hatches
- Test intercom and radio communications

4. FIRING SYSTEM MAINTENANCE

4.1 After Firing Procedures
- Cool barrel according to firing schedule
- Clean breach and firing mechanism
- Inspect recoil system for leaks or damage
- Document rounds fired in maintenance log
- Inspect spent shell ejection system

4.2 Barrel Maintenance
- Maximum barrel life: approximately 2500 rounds
- Document all rounds fired
- Perform bore inspection at specified intervals
- Monitor accuracy indicators

5. COMMON FAULTS AND REMEDIES

5.1 Hydraulic System Issues
- Symptom: Slow traverse or elevation
- Possible cause: Low hydraulic fluid or air in system
- Remedy: Check fluid levels, bleed system if required

5.2 Firing Circuit Faults
- Symptom: Misfire or failure to fire
- Possible cause: Electrical fault, damaged firing pin
- Remedy: Check electrical continuity, inspect firing mechanism

6. MAINTENANCE SCHEDULE

Daily: Visual inspections, fluid checks, system tests
Weekly: Detailed inspections, lubrication, communications check
Monthly: Comprehensive diagnostics, barrel inspection
Quarterly: Major component servicing, detailed accuracy testing

7. SAFETY PRECAUTIONS

- Always implement proper lockout/tagout procedures
- Ensure ammunition is properly secured when not in use
- Follow all safety protocols when working on hydraulic systems
- Use proper personal protective equipment
- Never perform maintenance on hot weapons systems

8. DOCUMENTATION

All maintenance activities must be properly documented in the vehicle maintenance log. Report all deficiencies through proper channels immediately.

For technical specifications and detailed repair procedures, consult the AS90 technical manual series.

UNCLASSIFIED
"""
    },

    "vehicle_recognition.pdf": {
        "title": "Armored Vehicle Recognition Training Manual",
        "content": """
UNCLASSIFIED

ARMORED VEHICLE RECOGNITION TRAINING MANUAL

1. PURPOSE

This training manual provides essential information for identifying friendly and potential threat armored vehicles. Accurate vehicle recognition is critical for force protection and mission success.

2. RECOGNITION METHODOLOGY

When identifying an armored vehicle, use the STARM method:
- Silhouette: Overall shape and profile
- Turret: Shape, size, and position
- Armament: Weapon systems visible
- Running gear: Track and wheel configuration
- Miscellaneous: Unique features, stowage patterns, antennas

3. BRITISH ARMY VEHICLES

3.1 CHALLENGER 2 MAIN BATTLE TANK
Profile: Low, angular turret with distinctive sloped armor
Main armament: Long 120mm rifled gun barrel
Running gear: Six road wheels with Hydrogas suspension
Key features: Thermal sleeve on gun barrel, distinctive turret shape
Weight class: Heavy (62+ tonnes)

3.2 WARRIOR INFANTRY FIGHTING VEHICLE
Profile: Boxy hull with two-man turret
Main armament: 30mm RARDEN cannon
Running gear: Five road wheels per side
Key features: Rear troop compartment, distinctive angular turret
Purpose: Infantry transport and fire support

3.3 AS90 SELF-PROPELLED ARTILLERY
Profile: Large boxy turret on tracked chassis
Main armament: 155mm howitzer with long barrel
Running gear: Six road wheels
Key features: Large turret with distinctive shape, no secondary armament visible
Purpose: Mobile artillery fire support

3.4 FV432 ARMORED PERSONNEL CARRIER
Profile: Simple box-shaped hull, no turret
Armament: Usually unarmed or single machine gun
Running gear: Five road wheels
Key features: Rear access ramp, very boxy appearance
Purpose: Personnel and equipment transport

4. ALLIED VEHICLES (NATO)

4.1 M1 ABRAMS (United States)
Profile: Rounded turret, smooth lines
Main armament: 120mm smoothbore gun
Running gear: Seven road wheels with advanced suspension
Key features: Turbine engine (distinctive sound), blow-out panels on turret

4.2 LEOPARD 2 (Germany)
Profile: Wedge-shaped turret with sharp angles
Main armament: 120mm smoothbore gun
Running gear: Seven road wheels
Key features: Distinctive slab-sided turret armor, commander's sight on turret roof

5. RECOGNITION TRAINING EXERCISES

5.1 Flash Card Drills
Use profile silhouettes to practice rapid recognition. Focus on distinctive features that are visible at various ranges and angles.

5.2 Timed Recognition Tests
Practice identifying vehicles under time pressure to simulate combat conditions. Aim for 3-second identification of common vehicles.

5.3 Range and Angle Variations
Study vehicles from multiple angles (front, side, rear, three-quarter) and at various ranges to account for battlefield conditions.

6. BATTLEFIELD CONSIDERATIONS

6.1 Range Identification
Long range (1000m+): Rely on overall silhouette and distinctive features
Medium range (500-1000m): Turret shape and armament become clear
Close range (<500m): All details visible including markings and stowage

6.2 Degraded Visibility
In poor visibility conditions (fog, dust, smoke), focus on overall shape and distinctive features like turret profile and gun length.

6.3 Camouflage and Concealment
Be aware that camouflage nets, additional armor, and field modifications can alter a vehicle's appearance. Focus on unchangeable features like overall size and running gear.

7. REPORTING PROCEDURES

When reporting enemy vehicle contacts, use standard format:
- Vehicle type
- Number of vehicles
- Grid location
- Direction of travel
- Activity (static, moving, engaging)

Example: "Contact report: Three enemy tanks, type unknown, grid 456789, moving north, currently static."

8. ASSESSMENT

Soldiers must demonstrate 90% accuracy in vehicle recognition tests before being certified. Regular refresher training is required to maintain proficiency.

UNCLASSIFIED
"""
    },

    "120mm_gun_system.pdf": {
        "title": "120mm Smoothbore Gun System Technical Data",
        "content": """
UNCLASSIFIED

120mm SMOOTHBORE GUN SYSTEM
TECHNICAL DATA SHEET

1. SYSTEM DESCRIPTION

The 120mm smoothbore gun system is a high-velocity tank gun used in modern main battle tanks. This document provides technical specifications and operational information.

2. GENERAL SPECIFICATIONS

Caliber: 120mm
Barrel length: 44 calibers (5.28 meters)
Rifling: Smoothbore (no rifling)
Maximum effective range: 4,000 meters (direct fire)
Rate of fire: 6-8 rounds per minute (sustained)
Muzzle velocity: 1,650-1,750 m/s (APFSDS rounds)

3. AMMUNITION TYPES

3.1 APFSDS (Armor-Piercing Fin-Stabilized Discarding Sabot)
- Purpose: Anti-tank, kinetic energy penetrator
- Penetration: Classified, effective against all known armor
- Muzzle velocity: 1,650-1,750 m/s
- Effective range: 4,000+ meters

The APFSDS round consists of a dense penetrator rod (typically depleted uranium or tungsten) surrounded by a sabot that falls away after leaving the barrel. The fin-stabilized penetrator achieves accuracy through aerodynamic stability rather than spin.

3.2 HEAT (High-Explosive Anti-Tank)
- Purpose: Anti-tank, shaped charge
- Penetration: 600-800mm RHA equivalent
- Muzzle velocity: 1,140 m/s
- Effective range: 3,000 meters

HEAT rounds use a shaped charge to form a high-velocity jet capable of penetrating armor. Effectiveness is independent of range but can be degraded by reactive armor.

3.3 HE (High-Explosive)
- Purpose: Anti-personnel, light vehicles, structures
- Explosive content: 5-7 kg
- Muzzle velocity: 900-1,000 m/s
- Effective range: 8,000 meters

Multi-purpose HE rounds are effective against soft targets and can be used with airburst or point-detonation fuzes.

3.4 SMOKE/ILLUMINATION
- Purpose: Screening, illumination
- Effective range: Varies by type
- Deployment: Smoke provides instant concealment; illumination provides battlefield lighting

4. FIRE CONTROL INTEGRATION

The 120mm gun system integrates with advanced fire control systems including:
- Laser rangefinder for precise distance measurement
- Ballistic computer for firing solution calculation
- Thermal sights for day/night engagement
- Automatic target tracking
- Wind sensor and atmospheric correction

5. ACCURACY SPECIFICATIONS

The system achieves first-round hit probability of:
- 90% at 2,000 meters (stationary target, stationary tank)
- 80% at 2,000 meters (moving target, stationary tank)
- 70% at 2,000 meters (moving target, moving tank)

Accuracy depends on proper boresighting, crew training, and environmental conditions.

6. BARREL MAINTENANCE

6.1 Service Life
Expected barrel life: 500-800 effective full charges
Factors affecting life: Ammunition type, firing rate, maintenance quality

6.2 Maintenance Procedures
After firing: Visual inspection for damage or obstructions
Daily: Clean if fired, inspect bore
Weekly: Detailed inspection, measure wear if heavily used
As needed: Bore measurement at prescribed intervals

6.3 Replacement Criteria
Replace barrel when:
- Accuracy degradation exceeds specifications
- Bore wear measurements exceed limits
- Damage or cracks detected
- Effective full charge count reached

7. SAFETY CONSIDERATIONS

7.1 Personnel Safety
- Maintain proper standoff distances during firing
- Ensure all personnel clear of recoil path
- Use proper hearing and eye protection
- Follow ammunition handling procedures

7.2 Equipment Safety
- Do not exceed maximum rate of fire (barrel heating)
- Allow proper cooling between firing sessions
- Inspect recoil system regularly
- Ensure proper ammunition storage

8. TROUBLESHOOTING

8.1 Misfire Procedures
- Wait 30 seconds minimum
- Announce misfire to all crew
- Follow established misfire procedures
- Do not open breach prematurely

8.2 Common Malfunctions
- Failure to extract: Check extractor for damage
- Failure to load: Inspect ammunition handling system
- Accuracy issues: Verify boresight, check barrel wear

9. AMMUNITION STORAGE

- Store in cool, dry environment
- Maintain proper separation by type
- Inspect regularly for damage
- Follow transport safety procedures
- Maximum storage temperature: 52°C

10. TRAINING REQUIREMENTS

Crew must demonstrate proficiency in:
- Safe ammunition handling
- Loading procedures
- Emergency procedures
- Accuracy standards
- Maintenance procedures

For detailed technical specifications and repair procedures, consult the weapon system technical manual.

UNCLASSIFIED
"""
    },

    "field_operations_report.pdf": {
        "title": "Field Operations Report - Desert Training Exercise",
        "content": """
UNCLASSIFIED

FIELD OPERATIONS REPORT
DESERT TRAINING EXERCISE - OPERATION SAND VIPER

DATE: 18 April 2024
LOCATION: Desert Training Area
UNIT: Armored Battle Group
CLASSIFICATION: UNCLASSIFIED

1. EXECUTIVE SUMMARY

This report documents observations and lessons learned from a five-day desert training exercise designed to prepare armored units for operations in arid environments.

2. EXERCISE OVERVIEW

2.1 Objectives
- Test armored vehicle performance in desert conditions
- Validate maintenance procedures for sandy environments
- Practice combined arms coordination
- Assess logistics and supply chain effectiveness

2.2 Participating Units
- 2x Tank Squadrons (Challenger 2)
- 1x Mechanized Infantry Company (Warrior IFVs)
- 1x Artillery Battery (AS90)
- Combat support and logistics elements

2.3 Duration
Five days of continuous operations with day and night maneuvers

3. OPERATIONAL ACTIVITIES

3.1 Movement to Contact
Tank and infantry units successfully executed movement to contact drills across varied desert terrain. Average speed: 25 km/h across open desert, reducing to 15 km/h in areas with significant obstacles.

Key observations:
- Navigation systems performed well in featureless terrain
- Dust signature management critical for concealment
- Formation spacing must be increased due to visibility issues

3.2 Live Fire Exercises
All units conducted live fire exercises with main weapon systems and supporting arms.

Results:
- Tank gunnery: 87% first-round hit rate at 2,000m
- Artillery fire missions: 94% within 50m of target
- Infantry weapons qualification: 89% pass rate

3.3 Night Operations
Night maneuvers tested thermal imaging and navigation capabilities.

Observations:
- Thermal sights highly effective in desert environment
- Temperature differential aids target detection
- Improved training on thermal signature management recommended

4. MAINTENANCE AND LOGISTICS

4.1 Vehicle Maintenance
Daily maintenance time increased by approximately 40% due to dust and sand ingress.

Key challenges:
- Air filter changes required every 4-6 hours of operation
- Track tension adjustments needed more frequently
- Cooling system fouling required additional monitoring

4.2 Supply Chain
Logistics units successfully maintained supply flow despite harsh conditions.

Fuel consumption: 15% higher than baseline due to terrain
Water consumption: 8 liters per person per day
Ammunition expenditure: Within planned parameters

5. LESSONS LEARNED

5.1 Equipment Performance
Positive:
- Main battle tanks performed reliably in high temperatures
- Fire control systems maintained accuracy
- Communications equipment functioned effectively

Challenges:
- Increased maintenance burden requires additional time allocation
- Dust filtration systems need frequent servicing
- Some auxiliary equipment experienced heat-related issues

5.2 Tactics and Procedures
Positive:
- Combined arms coordination effective
- Artillery support responsive and accurate
- Command and control maintained throughout

Improvements needed:
- Increased spacing between vehicles to reduce dust interference
- Enhanced concealment training for desert environment
- Better thermal signature management techniques

5.3 Personnel Performance
Positive:
- High morale despite challenging conditions
- Good adaptation to desert living conditions
- Strong teamwork and unit cohesion

Challenges:
- Heat casualty prevention requires constant attention
- Sleep cycles disrupted by extreme temperature variations
- Additional acclimatization time beneficial

6. ENVIRONMENTAL FACTORS

Temperature range: 15°C (night) to 45°C (day)
Wind: Light to moderate, creating dust storms on two occasions
Terrain: Mixed hard pan and soft sand, minimal vegetation

7. TRAINING VALUE ASSESSMENT

The exercise successfully validated unit readiness for desert operations. Key skills developed:
- Desert navigation and orientation
- Vehicle maintenance in harsh conditions
- Tactical movement across varied terrain
- Combined arms integration
- Logistics sustainment

8. RECOMMENDATIONS

8.1 Equipment
- Pre-deployment desert modification kits for all vehicles
- Additional air filter stocks for extended operations
- Enhanced crew cooling systems for hot climate operations

8.2 Training
- Increase pre-deployment desert environment familiarization
- Additional thermal signature management training
- Extended maintenance training for sand/dust conditions

8.3 Procedures
- Revise vehicle spacing doctrine for desert operations
- Update logistics planning factors for fuel consumption
- Enhance heat casualty prevention protocols

9. CONCLUSION

The desert training exercise successfully tested unit capabilities and identified areas for improvement. All participating units demonstrated professionalism and adaptability. The experience gained will significantly enhance operational readiness for future desert deployments.

PREPARED BY: Exercise Control Team
DATE: 18 April 2024

UNCLASSIFIED
"""
    }
}


def main():
    print("=" * 60)
    print("MoD Semantic Search - Sample Data Creation")
    print("=" * 60)

    # Determine project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    sample_data_dir = project_root / "sample_data"

    # Create directories
    print("\n[1/3] Creating directory structure...")
    dirs = [
        sample_data_dir / "pdfs",
        sample_data_dir / "audio",
        sample_data_dir / "images"
    ]

    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {dir_path}")

    # Create PDF files
    print("\n[2/3] Creating sample PDF files...")

    if not REPORTLAB_AVAILABLE:
        print("\n  ⚠️  reportlab not installed. Installing...")
        print("  Run: pip install reportlab")
        print("\n  Creating text files as fallback...\n")

        use_text_fallback = True
    else:
        use_text_fallback = False

    pdf_dir = sample_data_dir / "pdfs"

    for filename, data in PDF_CONTENTS.items():
        filepath = pdf_dir / filename

        try:
            if use_text_fallback:
                # Create .txt file instead
                text_filepath = filepath.with_suffix('.txt')
                create_text_file_fallback(text_filepath, data['title'], data['content'])
            else:
                create_pdf(str(filepath), data['title'], data['content'])
        except Exception as e:
            print(f"  ✗ Failed to create {filename}: {e}")

    # Create placeholder files for audio and images
    print("\n[3/3] Creating placeholder files for audio and images...")

    audio_files = [
        "artillery_briefing.mp3",
        "tank_maintenance_guide.mp3",
        "engineer_training.mp3",
        "radio_comms_training.mp3",
        "logistics_convoy.mp3"
    ]

    image_files = [
        "challenger2_desert.jpg",
        "as90_artillery.jpg",
        "convoy_formation.jpg",
        "warrior_ifv.jpg",
        "ammunition_display.jpg"
    ]

    audio_dir = sample_data_dir / "audio"
    for audio_file in audio_files:
        placeholder = audio_dir / f"{audio_file}.placeholder"
        placeholder.write_text(
            f"This is a placeholder for {audio_file}\n"
            f"The actual audio file should be placed here.\n"
            f"The transcript is available in manifest.json"
        )
        print(f"  ✓ Created placeholder: {placeholder}")

    image_dir = sample_data_dir / "images"
    for image_file in image_files:
        placeholder = image_dir / f"{image_file}.placeholder"
        placeholder.write_text(
            f"This is a placeholder for {image_file}\n"
            f"The actual image file should be placed here.\n"
            f"The caption is available in manifest.json"
        )
        print(f"  ✓ Created placeholder: {placeholder}")

    # Summary
    print("\n" + "=" * 60)
    print("Sample Data Creation Complete!")
    print("=" * 60)
    print(f"\n  ✓ Created {len(PDF_CONTENTS)} PDF files (or text fallbacks)")
    print(f"  ✓ Created {len(audio_files)} audio placeholders")
    print(f"  ✓ Created {len(image_files)} image placeholders")

    if use_text_fallback:
        print("\n  ℹ️  Note: Text files were created instead of PDFs")
        print("  Install reportlab for proper PDF generation:")
        print("    pip install reportlab")

    print("\n  ℹ️  Audio and image files are placeholders")
    print("  For full functionality:")
    print("    - Add actual audio files (.mp3) to sample_data/audio/")
    print("    - Add actual image files (.jpg) to sample_data/images/")
    print("    - Or proceed with text-only data for testing")

    print("\nNext step: Run the seeding script")
    print("  cd backend && python3 seed_database.py")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
