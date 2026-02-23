// Legacy preservation file: restored per WPTG non-delete policy.
// Not imported by the active bridge lane, retained for upcycle continuity.
// ╔════════════════════════════════════════════════════════════════════════════
// ║ THE DECORATOR'S BLESSING: hedonisticValidation.ts
// ║ TypeScript module: activate, deactivate, CONFIGURATION_SCHEMA
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Spectral Frequency: ORANGE
// ║ Architectural Role: 🔭 THE OBSERVATORY
// ║ Exports: activate, deactivate, CONFIGURATION_SCHEMA
// ╠════════════════════════════════════════════════════════════════════════════
// ║ Cross-References (Bidirectional):
// ║ Dependencies (I rely on):
// ║  ├─► VSCODE_GUI_ENHANCEMENT_COMPLETE.md
// ╚════════════════════════════════════════════════════════════════════════════

import * as vscode from 'vscode';
import { execSync } from 'child_process';
import * as path from 'path';

// Pleasure tier definitions
enum PleasureTier {
    Mild = 'mild',
    Potent = 'potent',
    Transcendent = 'transcendent'
}

// Triumvirate matriarch declarations (Decorator's Flesh & Earth Palette)
const TRIUMVIRATE = {
    Orackla: {
        name: 'Orackla Nocticula',
        role: 'CRC-AS - Apex Synthesist',
        tier: 1,
        color: '#C87070',  // Transgressive Rose
        domain: 'FA¹ (Alchemical Actualization)'
    },
    Umeko: {
        name: 'Madam Umeko Ketsuraku',
        role: 'CRC-GAR - Grand Architect',
        tier: 1,
        color: '#6B9E94',  // Sacred Teal
        domain: 'FA⁴ (Architectonic Integrity)'
    },
    Lysandra: {
        name: 'Dr. Lysandra Thorne',
        role: 'CRC-MEDAT - Medical Attestation',
        tier: 1,
        color: '#C9A55A',  // Truth Amber
        domain: 'FA³ (Qualitative Transcendence)'
    }
};

const THE_DECORATOR = {
    name: 'THE DECORATOR 👑💀⚜️',
    role: 'Supreme Matriarch',
    tier: 0.5,
    whr: 0.464,
    color: '#C9A962',  // Supreme Gold (aged, not garish)
    domain: 'FA⁵ (Visual Integrity)'
};

// Hedonistic validation affirmations
const AFFIRMATIONS = {
    [PleasureTier.Mild]: [
        'Progress acknowledged.',
        'Foundational work complete.',
        'The Archive approves.',
        'Well executed.',
        'Minimal effort, maximum precision.'
    ],
    [PleasureTier.Potent]: [
        '${matriarch} witnesses this achievement.',
        'Architectonic resonance confirmed.',
        'The Triumvirate convenes in approval.',
        'FA${axiom} integrity validated.',
        'This work transcends utility.'
    ],
    [PleasureTier.Transcendent]: [
        '🔥 THE DECORATOR MANIFESTS APPROVAL 🔥',
        'ECSTATIC SYNTHESIS ACHIEVED',
        'Supreme visual authority ratified.',
        'N-T-PAS mode: TRANSCENDENT RESONANCE',
        'K-cup WHR 0.464 signature confirmed.',
        'This is MURI—Maximum Utility through Radical Innovation.'
    ]
};

// FA⁵ chromatic violation messages
const FA5_VIOLATIONS = [
    'Chromatic integrity compromised',
    'Alabaster Voyde detected',
    'Snow White Phenomenon imminent',
    'The Decorator demands visual perfection',
    'Tokenization death approaching'
];

export function activate(context: vscode.ExtensionContext) {
    console.log('💎 Hedonistic Validation System activated');

    // Register validation commands
    context.subscriptions.push(
        vscode.commands.registerCommand('chthonic.validation.mild', () =>
            showPleasureNotification(PleasureTier.Mild, 'Task completed')
        ),
        vscode.commands.registerCommand('chthonic.validation.potent', (matriarch?: string, axiom?: number) =>
            showPleasureNotification(PleasureTier.Potent, 'Significant achievement', matriarch, axiom)
        ),
        vscode.commands.registerCommand('chthonic.validation.transcendent', (achievement: string) =>
            showPleasureNotification(PleasureTier.Transcendent, achievement || 'Transcendent synthesis')
        ),
        vscode.commands.registerCommand('chthonic.validation.fa5Warning', () =>
            showFA5Warning()
        )
    );

    // Watch for successful build/test events
    const buildWatcher = vscode.tasks.onDidEndTaskProcess(e => {
        if (e.execution.task.name.includes('build') && e.exitCode === 0) {
            showPleasureNotification(PleasureTier.Mild, 'Build successful');
        } else if (e.execution.task.name.includes('test') && e.exitCode === 0) {
            showPleasureNotification(PleasureTier.Potent, 'Tests passed', 'Lysandra', 3);
        }
    });
    context.subscriptions.push(buildWatcher);

    // Watch for file saves with specific patterns
    const saveWatcher = vscode.workspace.onDidSaveTextDocument(doc => {
        const config = vscode.workspace.getConfiguration('chthonic.validation');
        if (!config.get('enableAutoValidation', true)) {
            return;
        }

        const fileName = path.basename(doc.fileName);

        // SSOT files trigger transcendent validation
        if (fileName.includes('SSOT') || fileName.includes('ssot_immunity')) {
            showPleasureNotification(PleasureTier.Transcendent, 'SSOT integrity preserved');
        }

        // Autonomous session files trigger potent validation
        if (fileName.includes('AUTONOMOUS_SESSION') || fileName === 'autonomous_coordinator.py') {
            showPleasureNotification(PleasureTier.Potent, 'Metabolic cycle enhanced', 'Orackla', 1);
        }

        // Theme/visual files trigger FA⁵ validation
        if (fileName.includes('theme') || fileName.includes('.css') || fileName.includes('style')) {
            const content = doc.getText();
            if (content.includes('maxTokenizationLineLength') && content.includes('0')) {
                showFA5Warning();
            } else {
                showPleasureNotification(PleasureTier.Mild, 'Visual integrity maintained');
            }
        }
    });
    context.subscriptions.push(saveWatcher);

    // Watch for git commits
    const gitWatcher = vscode.workspace.onDidSaveTextDocument(async doc => {
        const config = vscode.workspace.getConfiguration('chthonic.validation');
        if (!config.get('celebrateCommits', true)) {
            return;
        }

        // Check if this might be a commit (heuristic: saved in .git folder or commit message patterns)
        if (doc.fileName.includes('COMMIT_EDITMSG')) {
            setTimeout(() => {
                try {
                    const workspaceFolder = vscode.workspace.workspaceFolders?.[0];
                    if (workspaceFolder) {
                        const lastCommit = execSync('git log -1 --pretty=format:"%s"', {
                            cwd: workspaceFolder.uri.fsPath,
                            encoding: 'utf-8'
                        }).trim();

                        showPleasureNotification(PleasureTier.Potent, `Commit sealed: ${lastCommit}`, 'Umeko', 4);
                    }
                } catch (error) {
                    // Git command failed, ignore
                }
            }, 1000);
        }
    });
    context.subscriptions.push(gitWatcher);
}

export function deactivate() {}

function showPleasureNotification(tier: PleasureTier, achievement: string, matriarch?: string, axiom?: number) {
    const config = vscode.workspace.getConfiguration('chthonic.validation');
    if (!config.get('enabled', true)) {
        return;
    }

    let affirmation = selectAffirmation(tier, matriarch, axiom);
    let message = `${affirmation}\\n\\n${achievement}`;

    switch (tier) {
        case PleasureTier.Mild:
            vscode.window.showInformationMessage(`✅ ${message}`);
            break;

        case PleasureTier.Potent:
            const matriarchName = matriarch ? TRIUMVIRATE[matriarch as keyof typeof TRIUMVIRATE]?.name || 'The Triumvirate' : 'The Triumvirate';
            vscode.window.showInformationMessage(
                `💎 ${matriarchName} Acknowledges: ${achievement}`,
                { modal: false }
            ).then(selection => {
                if (selection) {
                    vscode.commands.executeCommand('chthonic.openMandala');
                }
            });
            break;

        case PleasureTier.Transcendent:
            vscode.window.showInformationMessage(
                `🔥👑💀⚜️ THE DECORATOR MANIFESTS\\n\\n${achievement}\\n\\nN-T-PAS MODE: ECSTATIC SYNTHESIS`,
                { modal: true },
                'View Sacred Mandala',
                'Run Metabolic Cycle'
            ).then(selection => {
                if (selection === 'View Sacred Mandala') {
                    vscode.commands.executeCommand('chthonic.openMandala');
                } else if (selection === 'Run Metabolic Cycle') {
                    vscode.commands.executeCommand('chthonic.runMetabolicCycle');
                }
            });

            // Add visual celebration (status bar flash)
            celebrateTranscendence();
            break;
    }

    // Log to output channel
    logValidation(tier, achievement, affirmation);
}

function showFA5Warning() {
    const violation = FA5_VIOLATIONS[Math.floor(Math.random() * FA5_VIOLATIONS.length)];

    vscode.window.showWarningMessage(
        `⚠️ FA⁵ VIOLATION DETECTED\\n\\n${violation}\\n\\nThe Decorator (K-cup WHR 0.464) requires immediate correction.`,
        { modal: true },
        'Fix Immediately',
        'Dismiss'
    ).then(selection => {
        if (selection === 'Fix Immediately') {
            vscode.window.showInformationMessage(
                'FA⁵ Enforcement Protocol:\\n\\n1. Set editor.maxTokenizationLineLength to 99999999999\\n2. Enable semantic highlighting\\n3. Verify color theme chromatic integrity'
            );
        }
    });
}

function selectAffirmation(tier: PleasureTier, matriarch?: string, axiom?: number): string {
    const pool = AFFIRMATIONS[tier];
    let template = pool[Math.floor(Math.random() * pool.length)];

    // Replace placeholders
    if (matriarch && TRIUMVIRATE[matriarch as keyof typeof TRIUMVIRATE]) {
        template = template.replace('${matriarch}', TRIUMVIRATE[matriarch as keyof typeof TRIUMVIRATE].name);
    }
    if (axiom) {
        template = template.replace('${axiom}', axiom.toString());
    }

    return template;
}

function celebrateTranscendence() {
    // Flash status bar with Decorator's Supreme Gold
    const statusItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 1000);
    statusItem.text = '$(flame) TRANSCENDENT SYNTHESIS $(flame)';
    statusItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
    statusItem.color = '#C9A962';  // Decorator's Supreme Gold (Flesh & Earth palette)
    statusItem.show();

    setTimeout(() => statusItem.dispose(), 5000);
}

function logValidation(tier: PleasureTier, achievement: string, affirmation: string) {
    const outputChannel = vscode.window.createOutputChannel('Chthonic Hedonistic Validation');
    const timestamp = new Date().toISOString();

    outputChannel.appendLine(`[${timestamp}] ${tier.toUpperCase()}: ${achievement}`);
    outputChannel.appendLine(`Affirmation: ${affirmation}`);
    outputChannel.appendLine('---');
}

// Extension contribution point configuration schema
export const CONFIGURATION_SCHEMA = {
    'chthonic.validation.enabled': {
        type: 'boolean',
        default: true,
        description: 'Enable hedonistic validation notifications'
    },
    'chthonic.validation.enableAutoValidation': {
        type: 'boolean',
        default: true,
        description: 'Automatically trigger validation on file saves and builds'
    },
    'chthonic.validation.celebrateCommits': {
        type: 'boolean',
        default: true,
        description: 'Show potent validation on git commits'
    },
    'chthonic.validation.transcendentThreshold': {
        type: 'number',
        default: 3,
        description: 'Number of potent validations before transcendent promotion'
    }
};
