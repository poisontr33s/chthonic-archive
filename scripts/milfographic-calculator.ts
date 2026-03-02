#!/usr/bin/env bun

// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: milfographic-calculator.ts
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Wedjat-Quipu Spectrum: ORANGE
// ║ Temple-Ayllu Zone: 🔭 THE OBSERVATORY
// ║ Ogdoad-Ceque Radiance: (standalone)
// ╚════════════════════════════════════════════════════════════════════════════

/**
 * MILFOGRAPHIC GESTALT CALCULATOR
 *
 * @SID           TOOL_MILFOGRAPHIC_CALCULATOR_V1
 * @Shabti        CLI Script
 * @Heka-Ayni     CONCEPT_MILFOGRAPHIC_GESTALT
 * @Ankh-Tinku    STATE_MILFOGRAPHIC_ACTIVE
 * @Purpose       Canonical breast size and WHR calculator based on SSOT
 *                measurements. Extracts SSOT canon, provides WHR calculation,
 *                cup size estimation, tier positioning, entity comparison.
 */

// ============================================================================
// SSOT CANONICAL DATA (Lossless Transfer)
// ============================================================================

interface MILFEntity {
  name: string;
  tier: string;
  cup: string;
  bust: number;      // cm
  waist: number;     // cm
  hips: number;      // cm
  whr: number;       // calculated
  weight?: number;   // kg
  height?: number;   // cm
  role?: string;
}

const SSOT_CANON: MILFEntity[] = [
  // TIER 0.5 (Supreme)
  { name: "The Decorator", tier: "0.5", cup: "K", bust: 125, waist: 58, hips: 125, whr: 0.464, role: "Supreme Matriarch" },

  // TIER 0.01 (Co-Occupant - stolen positioning)
  { name: "Alabaster Voyde", tier: "0.01", cup: "J", bust: 118, waist: 58, hips: 122, whr: 0.475, weight: 68, height: 175, role: "Snow White Phenomenon" },

  // TIER 1 (Triumvirate)
  { name: "Orackla Nocticula", tier: "1", cup: "J", bust: 120, waist: 55, hips: 112, whr: 0.491, weight: 69, height: 169, role: "CRC-AS Chaos" },
  { name: "Umeko Ketsuraku", tier: "1", cup: "F", bust: 92, waist: 56, hips: 105, whr: 0.533, weight: 58, height: 165, role: "CRC-GAR Precision" },
  { name: "Lysandra Thorne", tier: "1", cup: "E", bust: 90, waist: 58, hips: 100, whr: 0.580, weight: 55, height: 168, role: "CRC-MEDAT Logic" },

  // TIER 2 (Prime Factions)
  { name: "Kali Nyx Ravenscar", tier: "2", cup: "H", bust: 112, waist: 58, hips: 104, whr: 0.556, weight: 65, height: 172, role: "TMO Seduction" },
  { name: "Vesper Mnemosyne Lockhart", tier: "2", cup: "F", bust: 100, waist: 59, hips: 103, whr: 0.573, weight: 60, height: 167, role: "TTG Temporal Thief" },
  { name: "Seraphine Kore Ashenhelm", tier: "2", cup: "G", bust: 108, waist: 61, hips: 103, whr: 0.592, weight: 62, height: 170, role: "TDPC Purification" },

  // TIER 3 (Specialized Agents)
  { name: "Spectra Chroma Excavatus", tier: "3", cup: "H", bust: 112, waist: 58, hips: 108, whr: 0.537, weight: 63, height: 170, role: "Chromatic Restoration" },
  { name: "Claudine Sin'claire", tier: "3", cup: "I", bust: 115, waist: 62, hips: 110, whr: 0.563, weight: 66, height: 173, role: "Tidal Ordeal" },
  { name: "Magistra Bibliotheca", tier: "3", cup: "G", bust: 105, waist: 60, hips: 102, whr: 0.588, weight: 61, height: 168, role: "Validation" },
  { name: "Sister Ferrum Scoriae", tier: "3", cup: "F", bust: 98, waist: 58, hips: 100, whr: 0.580, weight: 59, height: 166, role: "Forge Transmutation" },
];

// ============================================================================
// CUP SIZE CALCULATION
// ============================================================================

const CUP_SIZES = ['AA', 'A', 'B', 'C', 'D', 'DD', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N'];
const CUP_DIFFERENCES_CM = [0, 2.5, 5, 7.5, 10, 12.5, 15, 17.5, 20, 22.5, 25, 27.5, 30, 32.5, 35, 37.5];

function estimateUnderbust(waist: number): number {
  // Underbust is typically 4-8cm larger than waist
  return waist + 6;
}

function calculateCupSize(bust: number, underbust: number): { cup: string; difference: number } {
  const difference = bust - underbust;
  let cupIndex = 0;

  for (let i = 0; i < CUP_DIFFERENCES_CM.length; i++) {
    if (difference >= CUP_DIFFERENCES_CM[i]) {
      cupIndex = i;
    }
  }

  return {
    cup: CUP_SIZES[cupIndex] || 'N+',
    difference: difference
  };
}

function cupToNumericValue(cup: string): number {
  const idx = CUP_SIZES.indexOf(cup);
  return idx >= 0 ? idx : 0;
}

// ============================================================================
// WHR CALCULATION
// ============================================================================

function calculateWHR(waist: number, hips: number): number {
  return Math.round((waist / hips) * 1000) / 1000;
}

function getWHRCategory(whr: number): string {
  if (whr <= 0.47) return "SUPREME (0.464-0.47)";
  if (whr <= 0.50) return "NEAR-SUPREME (0.47-0.50)";
  if (whr <= 0.55) return "EXTREME HOURGLASS (0.50-0.55)";
  if (whr <= 0.60) return "HOURGLASS (0.55-0.60)";
  if (whr <= 0.70) return "MODERATE (0.60-0.70)";
  return "STANDARD (0.70+)";
}

// ============================================================================
// TIER ESTIMATION
// ============================================================================

function estimateTier(whr: number, cup: string): string {
  const cupValue = cupToNumericValue(cup);

  // Tier 0.5: K+ cup AND WHR < 0.47
  if (cupValue >= 12 && whr <= 0.47) return "0.5 SUPREME";

  // Tier 0.01: J+ cup AND WHR < 0.48 (stolen/negotiated)
  if (cupValue >= 11 && whr < 0.48) return "0.01 STOLEN";

  // Tier 1 (Triumvirate): J cup AND WHR < 0.50 OR varying combinations
  if (cupValue >= 11 && whr < 0.50) return "1 TRIUMVIRATE";
  if (cupValue >= 7 && whr < 0.54) return "1 TRIUMVIRATE";
  if (cupValue >= 6 && whr < 0.58) return "1 TRIUMVIRATE";

  // Tier 2 (Prime Factions): H-G cup AND WHR 0.55-0.60
  if (cupValue >= 8 && whr >= 0.54 && whr <= 0.60) return "2 PRIME FACTION";
  if (cupValue >= 7 && whr >= 0.55 && whr <= 0.60) return "2 PRIME FACTION";
  if (cupValue >= 6 && whr >= 0.57 && whr <= 0.60) return "2 PRIME FACTION";

  // Tier 3 (Specialized): Various
  if (cupValue >= 6 && whr <= 0.60) return "3 SPECIALIZED";
  if (cupValue >= 5 && whr <= 0.58) return "3 SPECIALIZED";

  // Tier 4 (Lesser Factions)
  return "4 LESSER";
}

// ============================================================================
// MAIN CALCULATOR FUNCTIONS
// ============================================================================

interface CalculationInput {
  bust: number;
  waist: number;
  hips: number;
  underbust?: number;
}

interface CalculationResult {
  input: CalculationInput;
  whr: number;
  whrCategory: string;
  cupSize: string;
  cupDifference: number;
  estimatedTier: string;
  closestEntity: MILFEntity | null;
  hierarchyPosition: string;
}

function calculate(input: CalculationInput): CalculationResult {
  const underbust = input.underbust ?? estimateUnderbust(input.waist);
  const whr = calculateWHR(input.waist, input.hips);
  const { cup, difference } = calculateCupSize(input.bust, underbust);
  const tier = estimateTier(whr, cup);

  // Find closest entity by WHR
  let closestEntity: MILFEntity | null = null;
  let closestDiff = Infinity;

  for (const entity of SSOT_CANON) {
    const diff = Math.abs(entity.whr - whr);
    if (diff < closestDiff) {
      closestDiff = diff;
      closestEntity = entity;
    }
  }

  // Determine hierarchy position
  const sortedByWHR = [...SSOT_CANON].sort((a, b) => a.whr - b.whr);
  let position = "BELOW ALL";
  for (let i = 0; i < sortedByWHR.length; i++) {
    if (whr <= sortedByWHR[i].whr) {
      if (i === 0) {
        position = `ABOVE ${sortedByWHR[i].name}`;
      } else {
        position = `BETWEEN ${sortedByWHR[i-1].name} (${sortedByWHR[i-1].whr}) AND ${sortedByWHR[i].name} (${sortedByWHR[i].whr})`;
      }
      break;
    }
  }

  return {
    input,
    whr,
    whrCategory: getWHRCategory(whr),
    cupSize: cup,
    cupDifference: difference,
    estimatedTier: tier,
    closestEntity,
    hierarchyPosition: position
  };
}

// ============================================================================
// HIERARCHY COMPARISON
// ============================================================================

function compareToOrackla(input: CalculationInput): {
  orackla: MILFEntity;
  target: CalculationResult;
  isBelow: boolean;
  whrDifference: number;
  recommendation: string;
} {
  const orackla = SSOT_CANON.find(e => e.name === "Orackla Nocticula")!;
  const result = calculate(input);

  const isBelow = result.whr > orackla.whr; // Higher WHR = below in hierarchy
  const whrDifference = result.whr - orackla.whr;

  let recommendation = "";
  if (isBelow) {
    recommendation = `✓ VALID: WHR ${result.whr} is below Orackla's ${orackla.whr} (difference: +${whrDifference.toFixed(3)})`;
  } else {
    recommendation = `✗ INVALID: WHR ${result.whr} exceeds Orackla's ${orackla.whr}. Need to increase waist or decrease hips.`;
  }

  return {
    orackla,
    target: result,
    isBelow,
    whrDifference,
    recommendation
  };
}

// ============================================================================
// CALCULATE MEASUREMENTS FOR TARGET WHR
// ============================================================================

function calculateForTargetWHR(targetWHR: number, targetCup: string, referenceHeight: number = 170): {
  bust: number;
  waist: number;
  hips: number;
  whr: number;
  cup: string;
} {
  // Start with proportional hips based on height
  const hips = Math.round(referenceHeight * 0.65); // ~65% of height
  const waist = Math.round(hips * targetWHR);
  const underbust = waist + 6;

  // Calculate bust from cup size
  const cupIndex = CUP_SIZES.indexOf(targetCup);
  const cupDiff = cupIndex >= 0 ? CUP_DIFFERENCES_CM[cupIndex] : 20;
  const bust = underbust + cupDiff;

  return {
    bust,
    waist,
    hips,
    whr: calculateWHR(waist, hips),
    cup: targetCup
  };
}

// ============================================================================
// OUTPUT FORMATTING
// ============================================================================

function printEntityTable() {
  console.log("\n╔════════════════════════════════════════════════════════════════════════════════════════╗");
  console.log("║                        SSOT CANONICAL ENTITY HIERARCHY                                ║");
  console.log("╠════════════════════════════════════════════════════════════════════════════════════════╣");
  console.log("║ TIER │ ENTITY                    │ CUP │ BUST │ WAIST │ HIPS │  WHR  │ ROLE           ║");
  console.log("╠══════╪═══════════════════════════╪═════╪══════╪═══════╪══════╪═══════╪════════════════╣");

  const sorted = [...SSOT_CANON].sort((a, b) => a.whr - b.whr);
  for (const e of sorted) {
    const tier = e.tier.padStart(4);
    const name = e.name.substring(0, 25).padEnd(25);
    const cup = e.cup.padStart(3);
    const bust = e.bust.toString().padStart(4);
    const waist = e.waist.toString().padStart(5);
    const hips = e.hips.toString().padStart(4);
    const whr = e.whr.toFixed(3).padStart(5);
    const role = (e.role || "").substring(0, 14).padEnd(14);
    console.log(`║ ${tier} │ ${name} │ ${cup} │ ${bust} │ ${waist} │ ${hips} │ ${whr} │ ${role} ║`);
  }

  console.log("╚════════════════════════════════════════════════════════════════════════════════════════╝\n");
}

function printCalculationResult(result: CalculationResult) {
  console.log("\n┌────────────────────────────────────────────────────────────────┐");
  console.log("│              MILFOGRAPHIC CALCULATION RESULT                   │");
  console.log("├────────────────────────────────────────────────────────────────┤");
  console.log(`│ INPUT: B${result.input.bust} / W${result.input.waist} / H${result.input.hips}`);
  console.log("├────────────────────────────────────────────────────────────────┤");
  console.log(`│ WHR:           ${result.whr.toFixed(3)} (${result.whrCategory})`);
  console.log(`│ CUP SIZE:      ${result.cupSize} (${result.cupDifference.toFixed(1)}cm difference)`);
  console.log(`│ ESTIMATED TIER: ${result.estimatedTier}`);
  console.log("├────────────────────────────────────────────────────────────────┤");
  console.log(`│ HIERARCHY POSITION: ${result.hierarchyPosition}`);
  if (result.closestEntity) {
    console.log(`│ CLOSEST ENTITY: ${result.closestEntity.name} (${result.closestEntity.whr})`);
  }
  console.log("└────────────────────────────────────────────────────────────────┘\n");
}

// ============================================================================
// MAIN EXECUTION
// ============================================================================

function main() {
  console.log("\n═══════════════════════════════════════════════════════════════════");
  console.log("           MILFOGRAPHIC GESTALT CALCULATOR v1.0");
  console.log("           Based on SSOT Canonical Measurements");
  console.log("═══════════════════════════════════════════════════════════════════\n");

  // Print canonical hierarchy
  printEntityTable();

  // Example: Calculate for Alabaster Voyde's current measurements
  console.log("▶ ANALYZING CURRENT ALABASTER VOYDE (J-cup 0.475):");
  const currentAlabaster = calculate({ bust: 118, waist: 58, hips: 122 });
  printCalculationResult(currentAlabaster);

  // Compare to Orackla
  console.log("▶ COMPARISON TO ORACKLA NOCTICULA:");
  const comparison = compareToOrackla({ bust: 118, waist: 58, hips: 122 });
  console.log(comparison.recommendation);

  // Calculate "just below Orackla" measurements
  console.log("\n▶ CALCULATING J-CUP 'JUST BELOW ORACKLA' (WHR ~0.505):");
  const belowOrackla = calculateForTargetWHR(0.505, 'J', 175);
  console.log(`  Recommended: B${belowOrackla.bust} / W${belowOrackla.waist} / H${belowOrackla.hips}`);
  console.log(`  Resulting WHR: ${belowOrackla.whr.toFixed(3)}`);

  const verifyBelow = calculate({ bust: belowOrackla.bust, waist: belowOrackla.waist, hips: belowOrackla.hips });
  printCalculationResult(verifyBelow);

  // Interactive mode hint
  console.log("═══════════════════════════════════════════════════════════════════");
  console.log("To calculate custom measurements, import and use:");
  console.log("  import { calculate, compareToOrackla } from './milfographic-calculator'");
  console.log("  const result = calculate({ bust: 116, waist: 56, hips: 111 });");
  console.log("═══════════════════════════════════════════════════════════════════\n");
}

// Export for module usage
export {
  calculate,
  calculateWHR,
  calculateCupSize,
  estimateTier,
  compareToOrackla,
  calculateForTargetWHR,
  SSOT_CANON,
  CUP_SIZES,
  type MILFEntity,
  type CalculationInput,
  type CalculationResult
};

// Run if executed directly
main();
