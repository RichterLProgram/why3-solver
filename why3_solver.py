"""
WHY3 Formal Proof Solver
=========================
Ein Python-Skript zur Verwaltung und Verarbeitung formeller mathematischer Beweise
mit WHY3. Das Skript liest Beweise aus JSON-Dateien ein und verarbeitet sie strukturiert.

Zusätzlich generiert es eine statische HTML-Website zur Anzeige der Beweise.

Autor: Automatisiert
Datum: Januar 2026
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from enum import Enum
from pathlib import Path
from datetime import datetime
import sys
import io

# Unicode-Output für Windows aktivieren
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


# ============================================================================
# Logging-Konfiguration
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Enums und Datentypen
# ============================================================================

class ProofStatus(Enum):
    """Status eines formellen Beweises"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    FAILED = "failed"


class HypothesisType(Enum):
    """Typ einer Hypothese/Annahme"""
    DEFINITION = "definition"
    ASSUMPTION = "assumption"
    CONSTRAINT = "constraint"
    THEOREM = "theorem"


# ============================================================================
# Datenklassen für strukturierte Beweisrepräsentation
# ============================================================================

@dataclass
class Hypothesis:
    """Repräsentiert eine Hypothese oder Annahme in einem Beweis"""
    name: str
    hypothesis_type: HypothesisType
    expression: str
    description: Optional[str] = None
    formal_notation: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Hypothese zu Dictionary"""
        return {
            'name': self.name,
            'type': self.hypothesis_type.value,
            'expression': self.expression,
            'description': self.description,
            'formal_notation': self.formal_notation
        }


@dataclass
class ProofStep:
    """Repräsentiert einen Schritt in einem formellen Beweis"""
    step_number: int
    description: str
    justification: str
    referenced_hypotheses: List[str] = field(default_factory=list)
    referenced_theorems: List[str] = field(default_factory=list)
    formal_expression: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Beweisschritt zu Dictionary"""
        return asdict(self)


@dataclass
class Theorem:
    """Repräsentiert einen formellen Satz/Theorem mit Beweis"""
    theorem_id: str
    name: str
    description: str
    statement: str
    formal_statement: str
    
    # Hypothesen und Bedingungen
    hypotheses: List[Hypothesis] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    
    # Beweis
    conclusion: str = ""
    proof_steps: List[ProofStep] = field(default_factory=list)
    proof_strategy: str = "structured"  # structured, by_cases, induction, etc.
    
    # Metadaten
    status: ProofStatus = ProofStatus.PENDING
    source: Optional[str] = None
    difficulty_level: str = "medium"  # easy, medium, hard
    
    # Zusätzliche Informationen
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Theorem zu Dictionary"""
        return {
            'theorem_id': self.theorem_id,
            'name': self.name,
            'description': self.description,
            'statement': self.statement,
            'formal_statement': self.formal_statement,
            'hypotheses': [h.to_dict() for h in self.hypotheses],
            'conditions': self.conditions,
            'conclusion': self.conclusion,
            'proof_steps': [step.to_dict() for step in self.proof_steps],
            'proof_strategy': self.proof_strategy,
            'status': self.status.value,
            'source': self.source,
            'difficulty_level': self.difficulty_level,
            'notes': self.notes
        }


@dataclass
class ProofContext:
    """Konfiguration für die Verarbeitung von Beweisen"""
    solver_backend: str = "why3"  # which3, z3, cvc4, etc.
    timeout_seconds: int = 30
    verbose: bool = True
    generate_certificates: bool = True


# ============================================================================
# Hauptklasse für WHY3-Solver
# ============================================================================

class WHY3ProofSolver:
    """
    Hauptklasse für die Verwaltung und Verarbeitung formeller Beweise mit WHY3.
    
    Diese Klasse:
    - Lädt Beweise aus JSON-Dateien
    - Validiert die Beweisstruktur
    - Verwaltet Beweisstatus
    - Generiert WHY3-Konfigurationen
    """

    def __init__(self, context: Optional[ProofContext] = None):
        """
        Initialisiert den WHY3-Solver
        
        Args:
            context: Konfigurationskontext für die Beweisverarbeitung
        """
        self.context = context or ProofContext()
        self.theorems: Dict[str, Theorem] = {}
        logger.info(f"WHY3-Solver initialisiert mit Backend: {self.context.solver_backend}")

    def load_proof_from_json(self, json_path: str) -> Optional[Theorem]:
        """
        Lädt einen formellen Beweis aus einer JSON-Datei
        
        Args:
            json_path: Pfad zur JSON-Datei
            
        Returns:
            Theorem-Objekt oder None bei Fehler
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"JSON-Beweis geladen von: {json_path}")
            theorem = self._parse_theorem_from_json(data)
            
            if theorem:
                self.theorems[theorem.theorem_id] = theorem
                logger.info(f"Theorem '{theorem.name}' erfolgreich registriert")
            
            return theorem
            
        except FileNotFoundError:
            logger.error(f"JSON-Datei nicht gefunden: {json_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Fehler beim Parsen von JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Unerwarteter Fehler beim Laden des Beweises: {e}")
            return None

    def _parse_theorem_from_json(self, data: Dict[str, Any]) -> Optional[Theorem]:
        """
        Parsed JSON-Daten zu einem Theorem-Objekt
        
        Args:
            data: Dictionary mit Theorem-Daten
            
        Returns:
            Theorem-Objekt oder None bei ungültiger Struktur
        """
        try:
            # Validiere erforderliche Felder
            required_fields = ['theorem_id', 'name', 'statement', 'formal_statement']
            if not all(field in data for field in required_fields):
                logger.warning(f"Theorem fehlen erforderliche Felder: {required_fields}")
                return None

            # Parse Hypothesen
            hypotheses = []
            if 'hypotheses' in data:
                for hyp_data in data['hypotheses']:
                    hypothesis = Hypothesis(
                        name=hyp_data.get('name', ''),
                        hypothesis_type=HypothesisType(hyp_data.get('type', 'assumption')),
                        expression=hyp_data.get('expression', ''),
                        description=hyp_data.get('description'),
                        formal_notation=hyp_data.get('formal_notation')
                    )
                    hypotheses.append(hypothesis)

            # Parse Beweisschritte
            proof_steps = []
            if 'proof_steps' in data:
                for step_data in data['proof_steps']:
                    step = ProofStep(
                        step_number=step_data.get('step_number', 0),
                        description=step_data.get('description', ''),
                        justification=step_data.get('justification', ''),
                        referenced_hypotheses=step_data.get('referenced_hypotheses', []),
                        referenced_theorems=step_data.get('referenced_theorems', []),
                        formal_expression=step_data.get('formal_expression')
                    )
                    proof_steps.append(step)

            # Erstelle Theorem-Objekt
            theorem = Theorem(
                theorem_id=data['theorem_id'],
                name=data['name'],
                description=data.get('description', ''),
                statement=data['statement'],
                formal_statement=data['formal_statement'],
                hypotheses=hypotheses,
                conditions=data.get('conditions', []),
                conclusion=data.get('conclusion', ''),
                proof_steps=proof_steps,
                proof_strategy=data.get('proof_strategy', 'structured'),
                status=ProofStatus(data.get('status', 'pending')),
                source=data.get('source'),
                difficulty_level=data.get('difficulty_level', 'medium'),
                notes=data.get('notes')
            )

            return theorem

        except (KeyError, ValueError) as e:
            logger.error(f"Fehler beim Parsen des Theorems: {e}")
            return None

    def validate_theorem(self, theorem: Theorem) -> bool:
        """
        Validiert die Struktur eines Theorems
        
        Args:
            theorem: Zu validierendes Theorem
            
        Returns:
            True wenn valid, False sonst
        """
        # Prüfe ob Theorem-Name leer ist
        if not theorem.name or not theorem.name.strip():
            logger.warning(f"Theorem '{theorem.theorem_id}' hat keinen Namen")
            return False

        # Prüfe ob Statement leer ist
        if not theorem.statement or not theorem.statement.strip():
            logger.warning(f"Theorem '{theorem.theorem_id}' hat keine Statement")
            return False

        # Prüfe ob formales Statement vorhanden ist
        if not theorem.formal_statement or not theorem.formal_statement.strip():
            logger.warning(f"Theorem '{theorem.theorem_id}' hat kein formales Statement")
            return False

        # Prüfe wenn Beweisschritte vorhanden sind
        if theorem.proof_steps:
            # Validiere dass Schritte sequenziell nummeriert sind
            step_numbers = [step.step_number for step in theorem.proof_steps]
            if step_numbers != list(range(1, len(step_numbers) + 1)):
                logger.warning(f"Theorem '{theorem.theorem_id}' hat ungültige Schrittnummerierung")
                return False

        logger.info(f"Theorem '{theorem.name}' erfolgreich validiert")
        return True

    def generate_why3_config(self, theorem: Theorem) -> Dict[str, Any]:
        """
        Generiert eine WHY3-Konfiguration für ein Theorem
        
        Args:
            theorem: Theorem für das WHY3-Konfiguration generiert wird
            
        Returns:
            Dictionary mit WHY3-Konfiguration
        """
        config = {
            'goal_name': theorem.name,
            'goal_id': theorem.theorem_id,
            'solver': self.context.solver_backend,
            'timeout': self.context.timeout_seconds,
            'formal_statement': theorem.formal_statement,
            'hypotheses': [h.to_dict() for h in theorem.hypotheses],
            'proof_strategy': theorem.proof_strategy,
            'generate_certificates': self.context.generate_certificates
        }
        
        logger.info(f"WHY3-Konfiguration generiert für: {theorem.name}")
        return config

    def print_theorem_summary(self, theorem: Theorem) -> None:
        """
        Gibt eine übersichtliche Zusammenfassung eines Theorems aus
        
        Args:
            theorem: Zu beschreibendes Theorem
        """
        print("\n" + "="*80)
        print(f"THEOREM: {theorem.name}")
        print("="*80)
        print(f"ID: {theorem.theorem_id}")
        print(f"Status: {theorem.status.value}")
        print(f"Schwierigkeitsgrad: {theorem.difficulty_level}")
        print(f"\nBeschreibung:\n{theorem.description}")
        print(f"\nAussage (natürlichsprachlich):\n{theorem.statement}")
        print(f"\nFormale Aussage:\n{theorem.formal_statement}")
        
        if theorem.hypotheses:
            print(f"\nHypothesen ({len(theorem.hypotheses)}):")
            for hyp in theorem.hypotheses:
                print(f"  • {hyp.name} ({hyp.hypothesis_type.value}):")
                print(f"    {hyp.expression}")
                if hyp.description:
                    print(f"    ({hyp.description})")
        
        if theorem.conditions:
            print(f"\nBedingungen ({len(theorem.conditions)}):")
            for i, cond in enumerate(theorem.conditions, 1):
                print(f"  ({chr(96+i)}) {cond}")
        
        print(f"\nSchlussfolgerung:\n{theorem.conclusion}")
        
        if theorem.proof_steps:
            print(f"\nBeweis ({len(theorem.proof_steps)} Schritte):")
            for step in theorem.proof_steps:
                print(f"\n  Schritt {step.step_number}: {step.description}")
                print(f"    Begründung: {step.justification}")
                if step.formal_expression:
                    print(f"    Formal: {step.formal_expression}")
                if step.referenced_hypotheses:
                    print(f"    Hypothesen: {', '.join(step.referenced_hypotheses)}")
                if step.referenced_theorems:
                    print(f"    Theoreme: {', '.join(step.referenced_theorems)}")
        
        if theorem.notes:
            print(f"\nNotizen:\n{theorem.notes}")
        
        print("="*80 + "\n")

    def export_theorem_to_json(self, theorem: Theorem, output_path: str) -> bool:
        """
        Exportiert ein Theorem zu JSON
        
        Args:
            theorem: Zu exportierendes Theorem
            output_path: Zieldatei
            
        Returns:
            True bei Erfolg, False sonst
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(theorem.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"Theorem zu {output_path} exportiert")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Export: {e}")
            return False

    def get_theorem(self, theorem_id: str) -> Optional[Theorem]:
        """
        Ruft ein registriertes Theorem ab
        
        Args:
            theorem_id: ID des Theorems
            
        Returns:
            Theorem oder None wenn nicht vorhanden
        """
        return self.theorems.get(theorem_id)

    def list_theorems(self) -> List[str]:
        """
        Listet alle Theorem-IDs auf
        
        Returns:
            Liste mit Theorem-IDs
        """
        return list(self.theorems.keys())

    def generate_html_for_theorem(self, theorem: Theorem) -> str:
        """
        Generiert HTML-Darstellung eines Theorems
        
        Args:
            theorem: Zu konvertierendes Theorem
            
        Returns:
            HTML-String
        """
        # WHY3-Konfiguration generieren
        why3_config = self.generate_why3_config(theorem)
        why3_config_json = json.dumps(why3_config, indent=2, ensure_ascii=False)
        
        # CSS-Styling - Dark Mode, elegant
        css = """
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            
            :root {
                --primary: #667eea;
                --primary-dark: #5568d3;
                --bg-dark: #0f1419;
                --bg-secondary: #1a1f2e;
                --bg-tertiary: #242b3c;
                --text-primary: #e8eef7;
                --text-secondary: #a8b2cc;
                --border: #313d52;
                --accent: #667eea;
            }
            
            body {
                font-family: 'Segoe UI', 'Roboto', sans-serif;
                background-color: var(--bg-dark);
                color: var(--text-primary);
                line-height: 1.7;
                letter-spacing: 0.3px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: var(--bg-dark);
            }
            
            .header {
                background: linear-gradient(135deg, var(--primary) 0%, #5568d3 100%);
                padding: 60px 40px;
                text-align: center;
                border-bottom: 1px solid var(--border);
            }
            
            .header h1 {
                font-size: 2.2em;
                font-weight: 300;
                letter-spacing: 1px;
                margin-bottom: 10px;
            }
            
            .header p {
                font-size: 0.95em;
                opacity: 0.9;
            }
            
            .content {
                padding: 50px 40px;
            }
            
            .section {
                margin: 40px 0;
            }
            
            .section-title {
                font-size: 1.6em;
                font-weight: 400;
                color: var(--primary);
                border-bottom: 2px solid var(--primary);
                padding-bottom: 12px;
                margin-bottom: 25px;
                letter-spacing: 0.5px;
            }
            
            .metadata {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            
            .metadata-item {
                background: var(--bg-secondary);
                padding: 18px;
                border-radius: 6px;
                border-left: 3px solid var(--primary);
            }
            
            .metadata-label {
                font-size: 0.85em;
                color: var(--text-secondary);
                text-transform: uppercase;
                letter-spacing: 0.8px;
                margin-bottom: 8px;
            }
            
            .metadata-value {
                font-size: 1.1em;
                color: var(--text-primary);
                font-weight: 500;
            }
            
            .status-badge {
                display: inline-block;
                padding: 6px 14px;
                border-radius: 4px;
                font-size: 0.9em;
                font-weight: 600;
                letter-spacing: 0.5px;
            }
            
            .status-pending { background: rgba(255, 193, 7, 0.15); color: #ffc107; }
            .status-verified { background: rgba(76, 175, 80, 0.15); color: #4caf50; }
            .status-in_progress { background: rgba(33, 150, 243, 0.15); color: #2196f3; }
            .status-failed { background: rgba(244, 67, 54, 0.15); color: #f44336; }
            
            .description {
                background: var(--bg-secondary);
                padding: 25px;
                border-radius: 6px;
                border-left: 3px solid var(--primary);
                line-height: 1.8;
            }
            
            .formal-statement {
                background: var(--bg-secondary);
                padding: 25px;
                border-radius: 6px;
                border-left: 3px solid var(--primary);
                font-family: 'Courier New', monospace;
                overflow-x: auto;
                font-size: 0.95em;
                line-height: 1.6;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            
            .hypothesis-list, .conditions-list {
                display: grid;
                gap: 18px;
                margin: 25px 0;
            }
            
            .hypothesis-item, .condition-item {
                background: var(--bg-secondary);
                padding: 20px;
                border-radius: 6px;
                border-left: 3px solid var(--primary);
            }
            
            .hypothesis-item.definition { border-left-color: #4caf50; }
            .hypothesis-item.assumption { border-left-color: #2196f3; }
            .hypothesis-item.constraint { border-left-color: #ff9800; }
            .hypothesis-item.theorem { border-left-color: #9c27b0; }
            
            .hypothesis-name {
                font-weight: 600;
                color: var(--text-primary);
                font-size: 1.05em;
                margin-bottom: 8px;
            }
            
            .hypothesis-type {
                display: inline-block;
                background: var(--primary);
                color: white;
                padding: 3px 10px;
                border-radius: 3px;
                font-size: 0.8em;
                margin-left: 12px;
                font-weight: 600;
                letter-spacing: 0.5px;
            }
            
            .hypothesis-expression {
                font-family: 'Courier New', monospace;
                background: var(--bg-tertiary);
                padding: 12px;
                border-radius: 4px;
                margin: 12px 0;
                font-size: 0.95em;
            }
            
            .proof-steps {
                background: var(--bg-secondary);
                padding: 25px;
                border-radius: 6px;
                margin: 25px 0;
            }
            
            .proof-step {
                background: var(--bg-tertiary);
                padding: 20px;
                margin: 15px 0;
                border-left: 3px solid var(--primary);
                border-radius: 4px;
            }
            
            .proof-step-number {
                display: inline-block;
                background: var(--primary);
                color: white;
                width: 32px;
                height: 32px;
                border-radius: 50%;
                text-align: center;
                line-height: 32px;
                font-weight: 600;
                margin-right: 12px;
            }
            
            .proof-step-title {
                font-weight: 600;
                font-size: 1.05em;
                color: var(--text-primary);
                margin-bottom: 12px;
                display: inline-block;
            }
            
            .proof-step-justification {
                background: var(--bg-secondary);
                padding: 14px;
                margin: 12px 0;
                border-radius: 4px;
                border-left: 2px solid var(--primary);
                font-size: 0.95em;
                line-height: 1.6;
            }
            
            .proof-step-formal {
                font-family: 'Courier New', monospace;
                background: var(--bg-secondary);
                padding: 14px;
                border-radius: 4px;
                margin: 12px 0;
                font-size: 0.9em;
                overflow-x: auto;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            
            .references {
                margin-top: 15px;
                padding-top: 15px;
                border-top: 1px solid var(--border);
            }
            
            .reference-list {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
                margin-top: 8px;
            }
            
            .reference-tag {
                background: var(--bg-secondary);
                padding: 5px 12px;
                border-radius: 4px;
                font-size: 0.85em;
                border: 1px solid var(--border);
            }
            
            .code-block {
                background: var(--bg-secondary);
                color: var(--text-primary);
                padding: 20px;
                border-radius: 6px;
                overflow-x: auto;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
                line-height: 1.6;
                margin: 15px 0;
                border-left: 3px solid var(--primary);
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            
            .why3-section {
                background: var(--bg-secondary);
                padding: 25px;
                border-radius: 6px;
                margin: 25px 0;
                border-left: 3px solid var(--primary);
            }
            
            .why3-title {
                font-size: 1.25em;
                font-weight: 600;
                color: var(--primary);
                margin-bottom: 20px;
                letter-spacing: 0.5px;
            }
            
            .why3-flow {
                display: flex;
                align-items: center;
                gap: 12px;
                margin: 20px 0;
                flex-wrap: wrap;
            }
            
            .why3-flow-item {
                background: var(--bg-tertiary);
                padding: 12px 18px;
                border-radius: 4px;
                border: 1px solid var(--primary);
                font-weight: 500;
                color: var(--primary);
                font-size: 0.95em;
            }
            
            .why3-flow-arrow {
                font-size: 1.3em;
                color: var(--primary);
            }
            
            .config-table {
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }
            
            .config-table th {
                background: var(--primary);
                color: white;
                padding: 14px;
                text-align: left;
                font-weight: 600;
                font-size: 0.95em;
                letter-spacing: 0.5px;
            }
            
            .config-table td {
                padding: 12px 14px;
                border-bottom: 1px solid var(--border);
                font-size: 0.95em;
            }
            
            .config-table tr:hover {
                background: var(--bg-tertiary);
            }
            
            .config-key { color: #2196f3; font-weight: 600; font-family: monospace; }
            .config-value { color: var(--text-secondary); }
            
            .toc {
                background: var(--bg-secondary);
                padding: 20px;
                border-radius: 6px;
                margin: 25px 0;
                border-left: 3px solid var(--primary);
            }
            
            .toc h3 {
                color: var(--primary);
                margin-bottom: 15px;
                font-size: 1.1em;
                letter-spacing: 0.5px;
            }
            
            .toc ul {
                list-style: none;
            }
            
            .toc li {
                margin: 8px 0;
                padding-left: 20px;
            }
            
            .toc li:before {
                content: "⊢";
                margin-right: 10px;
                color: var(--primary);
            }
            
            .toc a {
                color: var(--primary);
                text-decoration: none;
                font-size: 0.95em;
                transition: opacity 0.2s;
            }
            
            .toc a:hover {
                opacity: 0.7;
            }
            
            .footer {
                background: var(--bg-secondary);
                padding: 25px 40px;
                text-align: center;
                border-top: 1px solid var(--border);
                color: var(--text-secondary);
                font-size: 0.9em;
            }
        </style>
        """
        
        # Status-CSS-Klasse
        status_class = f"status-{theorem.status.value}"
        
        # HTML-Template
        html = f"""
        <!DOCTYPE html>
        <html lang="de">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{theorem.name} - WHY3 Proof Solver</title>
            {css}
        </head>
        <body>
            <div class="container">
                <!-- Header -->
                <div class="header">
                    <h1>Formal Proof Solver</h1>
                    <p>Mathematical Proof Verification via WHY3</p>
                </div>
                
                <!-- Content -->
                <div class="content">
                    <!-- Theorem Title -->
                    <div class="section">
                        <h1 style="color: var(--primary); margin-bottom: 15px; font-weight: 300; letter-spacing: 0.5px;">{theorem.name}</h1>
                        <div class="metadata">
                            <div class="metadata-item">
                                <div class="metadata-label">Identifier</div>
                                <div class="metadata-value">{theorem.theorem_id}</div>
                            </div>
                            <div class="metadata-item">
                                <div class="metadata-label">Status</div>
                                <div class="metadata-value">
                                    <span class="status-badge {status_class}">
                                        {theorem.status.value.upper()}
                                    </span>
                                </div>
                            </div>
                            <div class="metadata-item">
                                <div class="metadata-label">Difficulty</div>
                                <div class="metadata-value">{theorem.difficulty_level.upper()}</div>
                            </div>
                            <div class="metadata-item">
                                <div class="metadata-label">Source</div>
                                <div class="metadata-value">{theorem.source or "Unknown"}</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Table of Contents -->
                    <div class="toc">
                        <h3>Contents</h3>
                        <ul>
                            <li><a href="#description">Description</a></li>
                            <li><a href="#statement">Theorem Statement</a></li>
                            <li><a href="#hypotheses">Hypotheses</a></li>
                            <li><a href="#conditions">Conditions</a></li>
                            <li><a href="#proof">Proof</a></li>
                            <li><a href="#why3">WHY3 Configuration</a></li>
                            <li><a href="#conclusion">Conclusion</a></li>
                        </ul>
                    </div>
                    
                    <!-- Description -->
                    <div class="section" id="description">
                        <h2 class="section-title">Description</h2>
                        <div class="description">
                            {theorem.description}
                        </div>
                    </div>
                    
                    <!-- Statement -->
                    <div class="section" id="statement">
                        <h2 class="section-title">Theorem Statement</h2>
                        <p style="margin-bottom: 15px; color: var(--text-secondary);">Natural Language Formulation:</p>
                        <div class="description">{theorem.statement}</div>
                        <p style="margin-top: 20px; margin-bottom: 15px; color: var(--text-secondary);">Formal Notation (HOL/Why3):</p>
                        <div class="formal-statement">{theorem.formal_statement}</div>
                    </div>
                    
                    <!-- Hypotheses -->
                    <div class="section" id="hypotheses">
                        <h2 class="section-title">Hypotheses ({len(theorem.hypotheses)})</h2>
                        <div class="hypothesis-list">
                            {self._generate_hypotheses_html(theorem.hypotheses)}
                        </div>
                    </div>
                    
                    <!-- Conditions -->
                    {f'''<div class="section" id="conditions">
                        <h2 class="section-title">Conditions ({len(theorem.conditions)})</h2>
                        <div class="conditions-list">
                            {"".join([f'<div class="condition-item"><strong>({chr(96+i)})</strong> {cond}</div>' for i, cond in enumerate(theorem.conditions, 1)])}
                        </div>
                    </div>''' if theorem.conditions else ''}
                    
                    <!-- Proof -->
                    <div class="section" id="proof">
                        <h2 class="section-title">Proof ({len(theorem.proof_steps)} steps)</h2>
                        <p style="margin-bottom: 20px; color: var(--text-secondary);">
                            Proof Method: <strong>{theorem.proof_strategy}</strong>
                        </p>
                        <div class="proof-steps">
                            {self._generate_proof_steps_html(theorem.proof_steps)}
                        </div>
                    </div>
                    
                    <!-- WHY3 Solver Section -->
                    <div class="section" id="why3">
                        <h2 class="section-title">WHY3 Solver Configuration</h2>
                        
                        <div class="why3-section">
                            <div class="why3-title">Proof Pipeline</div>
                            <div class="why3-flow">
                                <div class="why3-flow-item">Formal Statement</div>
                                <div class="why3-flow-arrow">→</div>
                                <div class="why3-flow-item">WHY3 Solver</div>
                                <div class="why3-flow-arrow">→</div>
                                <div class="why3-flow-item">Verification</div>
                            </div>
                        </div>
                        
                        <h3 style="color: var(--primary); margin-top: 30px; margin-bottom: 18px; font-size: 1.15em; font-weight: 600; letter-spacing: 0.5px;">Input Parameters for WHY3:</h3>
                        <table class="config-table">
                            <tr>
                                <th>Parameter</th>
                                <th>Value</th>
                                <th>Description</th>
                            </tr>
                            <tr>
                                <td><span class="config-key">goal_name</span></td>
                                <td><span class="config-value">{theorem.name}</span></td>
                                <td>Name of the proof goal</td>
                            </tr>
                            <tr>
                                <td><span class="config-key">goal_id</span></td>
                                <td><span class="config-value">{theorem.theorem_id}</span></td>
                                <td>Unique identifier</td>
                            </tr>
                            <tr>
                                <td><span class="config-key">solver</span></td>
                                <td><span class="config-value">{self.context.solver_backend}</span></td>
                                <td>Solver backend</td>
                            </tr>
                            <tr>
                                <td><span class="config-key">timeout</span></td>
                                <td><span class="config-value">{self.context.timeout_seconds}s</span></td>
                                <td>Time limit per proof</td>
                            </tr>
                            <tr>
                                <td><span class="config-key">proof_strategy</span></td>
                                <td><span class="config-value">{theorem.proof_strategy}</span></td>
                                <td>Proof method</td>
                            </tr>
                            <tr>
                                <td><span class="config-key">hypotheses_count</span></td>
                                <td><span class="config-value">{len(theorem.hypotheses)}</span></td>
                                <td>Number of hypotheses</td>
                            </tr>
                            <tr>
                                <td><span class="config-key">generate_certificates</span></td>
                                <td><span class="config-value">{"true" if self.context.generate_certificates else "false"}</span></td>
                                <td>Generate certificates</td>
                            </tr>
                        </table>
                        
                        <h3 style="color: var(--primary); margin-top: 30px; margin-bottom: 18px; font-size: 1.15em; font-weight: 600; letter-spacing: 0.5px;">Formal Statement Input to WHY3:</h3>
                        <div class="code-block">{theorem.formal_statement}</div>
                        
                        <h3 style="color: var(--primary); margin-top: 30px; margin-bottom: 18px; font-size: 1.15em; font-weight: 600; letter-spacing: 0.5px;">Complete WHY3 Configuration (JSON):</h3>
                        <div class="code-block">{why3_config_json}</div>
                        
                        <h3 style="color: var(--primary); margin-top: 30px; margin-bottom: 18px; font-size: 1.15em; font-weight: 600; letter-spacing: 0.5px;">Hypotheses Used by Solver:</h3>
                        <div style="display: grid; gap: 15px;">
                            {self._generate_why3_hypotheses_html(theorem.hypotheses)}
                        </div>
                    </div>
                    
                    <!-- Conclusion -->
                    <div class="section" id="conclusion">
                        <h2 class="section-title">Conclusion</h2>
                        <div class="formal-statement">{theorem.conclusion}</div>
                    </div>
                    
                    <!-- Notes -->
                    {f'''<div class="section">
                        <h2 class="section-title">Notes</h2>
                        <div class="description">{theorem.notes}</div>
                    </div>''' if theorem.notes else ''}
                    
                </div>
                
                <!-- Footer -->
                <div class="footer">
                    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Formal Proof Solver v1.0 | WHY3</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html

    def _generate_hypotheses_html(self, hypotheses: List[Hypothesis]) -> str:
        """Generiert HTML für Hypothesen-Liste"""
        html_parts = []
        for hyp in hypotheses:
            type_class = hyp.hypothesis_type.value
            html = f"""
            <div class="hypothesis-item {type_class}">
                <div class="hypothesis-name">
                    {hyp.name}
                    <span class="hypothesis-type">{hyp.hypothesis_type.value.upper()}</span>
                </div>
                <div class="hypothesis-expression">{hyp.expression}</div>
                {f'<p style="font-size: 0.9em; color: #666; margin-top: 10px;">{hyp.description}</p>' if hyp.description else ''}
                {f'<p style="font-family: monospace; font-size: 0.85em; color: #999; margin-top: 5px;">Formal: {hyp.formal_notation}</p>' if hyp.formal_notation else ''}
            </div>
            """
            html_parts.append(html)
        return "".join(html_parts)

    def _generate_proof_steps_html(self, proof_steps: List[ProofStep]) -> str:
        """Generiert HTML für Beweis-Schritte"""
        html_parts = []
        for step in proof_steps:
            references = ""
            if step.referenced_hypotheses or step.referenced_theorems:
                ref_hyps = "".join([f'<span class="reference-tag">{h}</span>' 
                                   for h in step.referenced_hypotheses])
                ref_thms = "".join([f'<span class="reference-tag">{t}</span>' 
                                   for t in step.referenced_theorems])
                references = f"""
                <div class="references">
                    <strong>Referenzen:</strong>
                    <div class="reference-list">
                        {ref_hyps}{ref_thms}
                    </div>
                </div>
                """
            
            html = f"""
            <div class="proof-step">
                <div>
                    <span class="proof-step-number">{step.step_number}</span>
                    <span class="proof-step-title">{step.description}</span>
                </div>
                <div class="proof-step-justification">
                    {step.justification}
                </div>
                {f'<div class="proof-step-formal">{step.formal_expression}</div>' if step.formal_expression else ''}
                {references}
            </div>
            """
            html_parts.append(html)
        return "".join(html_parts)

    def _generate_why3_hypotheses_html(self, hypotheses: List[Hypothesis]) -> str:
        """Generiert HTML für WHY3 Hypothesen-Übersicht"""
        html_parts = []
        for hyp in hypotheses:
            html = f"""
            <div class="hypothesis-item {hyp.hypothesis_type.value}" style="margin: 0;">
                <div class="hypothesis-name">
                    {hyp.name}
                    <span class="hypothesis-type">{hyp.hypothesis_type.value.upper()}</span>
                </div>
                <div class="hypothesis-expression">{hyp.expression}</div>
                {f'<p style="font-family: monospace; font-size: 0.85em; color: #666; margin-top: 8px;">→ {hyp.formal_notation}</p>' if hyp.formal_notation else ''}
            </div>
            """
            html_parts.append(html)
        return "".join(html_parts)

    def generate_static_website(self, output_dir: str = "output") -> bool:
        """
        Generiert eine statische HTML-Website für alle Theoreme
        
        Args:
            output_dir: Ausgabe-Verzeichnis
            
        Returns:
            True bei Erfolg, False sonst
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Generiere statische Website in: {output_dir}")
            
            # Generiere Index-Seite
            self._generate_index_page(output_path)
            
            # Generiere Seiten für jeden Theorem
            for theorem_id, theorem in self.theorems.items():
                html = self.generate_html_for_theorem(theorem)
                theorem_file = output_path / f"{theorem_id}.html"
                
                with open(theorem_file, 'w', encoding='utf-8') as f:
                    f.write(html)
                
                logger.info(f"Theorem-Seite erstellt: {theorem_file}")
            
            # Kopiere CSS zu separater Datei wenn nötig
            logger.info(f"Statische Website erfolgreich generiert in: {output_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Fehler beim Generieren der Website: {e}")
            return False

    def _generate_index_page(self, output_path: Path) -> None:
        """Generiert Index-Seite mit Übersicht aller Theoreme"""
        
        theorem_rows = ""
        for theorem_id, theorem in self.theorems.items():
            status_class = f"status-{theorem.status.value}"
            row = f"""
            <tr>
                <td><a href="{theorem_id}.html" style="color: var(--primary); text-decoration: none; font-weight: 600;">{theorem.name}</a></td>
                <td>{theorem.theorem_id}</td>
                <td><span class="status-badge {status_class}">{theorem.status.value.upper()}</span></td>
                <td>{theorem.difficulty_level.upper()}</td>
                <td>{theorem.source or '-'}</td>
                <td style="text-align: center;">{len(theorem.proof_steps)}</td>
            </tr>
            """
            theorem_rows += row
        
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Formal Proof Solver - Theorems Overview</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                :root {{
                    --primary: #667eea;
                    --bg-dark: #0f1419;
                    --bg-secondary: #1a1f2e;
                    --bg-tertiary: #242b3c;
                    --text-primary: #e8eef7;
                    --text-secondary: #a8b2cc;
                    --border: #313d52;
                }}
                body {{ 
                    font-family: 'Segoe UI', 'Roboto', sans-serif;
                    background: var(--bg-dark);
                    color: var(--text-primary);
                    min-height: 100vh;
                    padding: 30px 20px;
                }}
                .container {{ 
                    max-width: 1200px; 
                    margin: 0 auto;
                    background: var(--bg-dark);
                }}
                .header {{
                    background: linear-gradient(135deg, var(--primary) 0%, #5568d3 100%);
                    color: white;
                    padding: 50px 40px;
                    text-align: center;
                    border-bottom: 1px solid var(--border);
                    margin-bottom: 40px;
                }}
                .header h1 {{ font-size: 2.2em; margin-bottom: 10px; font-weight: 300; letter-spacing: 1px; }}
                .header p {{ font-size: 1em; opacity: 0.9; }}
                .content {{ padding: 0; }}
                .stats {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 40px;
                }}
                .stat-card {{
                    background: var(--bg-secondary);
                    padding: 25px;
                    border-radius: 6px;
                    border-left: 3px solid var(--primary);
                    text-align: center;
                }}
                .stat-value {{
                    font-size: 2.2em;
                    font-weight: 300;
                    color: var(--primary);
                    margin-bottom: 8px;
                }}
                .stat-label {{
                    color: var(--text-secondary);
                    font-size: 0.9em;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                h2 {{
                    font-size: 1.6em;
                    font-weight: 400;
                    color: var(--primary);
                    border-bottom: 2px solid var(--primary);
                    padding-bottom: 12px;
                    margin-bottom: 25px;
                    letter-spacing: 0.5px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th {{
                    background: var(--primary);
                    color: white;
                    padding: 14px;
                    text-align: left;
                    font-weight: 600;
                    font-size: 0.95em;
                    letter-spacing: 0.5px;
                }}
                td {{
                    padding: 14px;
                    border-bottom: 1px solid var(--border);
                    font-size: 0.95em;
                }}
                tr:hover {{ background: var(--bg-secondary); }}
                .status-badge {{
                    display: inline-block;
                    padding: 6px 14px;
                    border-radius: 4px;
                    font-size: 0.85em;
                    font-weight: 600;
                    letter-spacing: 0.5px;
                }}
                .status-pending {{ background: rgba(255, 193, 7, 0.15); color: #ffc107; }}
                .status-verified {{ background: rgba(76, 175, 80, 0.15); color: #4caf50; }}
                .status-in_progress {{ background: rgba(33, 150, 243, 0.15); color: #2196f3; }}
                .status-failed {{ background: rgba(244, 67, 54, 0.15); color: #f44336; }}
                .footer {{
                    background: var(--bg-secondary);
                    padding: 25px 40px;
                    text-align: center;
                    border-top: 1px solid var(--border);
                    color: var(--text-secondary);
                    font-size: 0.9em;
                    margin-top: 40px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Formal Proof Solver</h1>
                    <p>Mathematical Proof Verification via WHY3</p>
                </div>
                
                <div class="content">
                    <h2>Theorems Overview</h2>
                    
                    <div class="stats">
                        <div class="stat-card">
                            <div class="stat-value">{len(self.theorems)}</div>
                            <div class="stat-label">Theorems</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{sum(1 for t in self.theorems.values() if t.status == ProofStatus.VERIFIED)}</div>
                            <div class="stat-label">Verified</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">{sum(len(t.proof_steps) for t in self.theorems.values())}</div>
                            <div class="stat-label">Proof Steps</div>
                        </div>
                    </div>
                    
                    <table>
                        <thead>
                            <tr>
                                <th>Theorem</th>
                                <th>Identifier</th>
                                <th>Status</th>
                                <th>Difficulty</th>
                                <th>Source</th>
                                <th>Steps</th>
                            </tr>
                        </thead>
                        <tbody>
                            {theorem_rows}
                        </tbody>
                    </table>
                </div>
                
                <div class="footer">
                    <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Formal Proof Solver v1.0 | WHY3</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        index_file = output_path / "index.html"
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(html)
        
        logger.info(f"Generated index page: {index_file}")


# ============================================================================
# Entry Point
# ============================================================================

def main():
    """Main function for testing the solver"""
    
    # Create solver with standard configuration
    context = ProofContext(
        solver_backend="why3",
        timeout_seconds=60,
        verbose=True,
        generate_certificates=True
    )
    
    solver = WHY3ProofSolver(context)
    
    print("\n" + "="*80)
    print("FORMAL PROOF SOLVER")
    print("="*80)
    print("Ready to load proofs from JSON files\n")
    
    # Example: Load a proof if JSON exists
    json_file = Path("proofs/lhopital_rule.json")
    if json_file.exists():
        theorem = solver.load_proof_from_json(str(json_file))
        
        if theorem and solver.validate_theorem(theorem):
            solver.print_theorem_summary(theorem)
            
            # Generate WHY3 configuration
            config = solver.generate_why3_config(theorem)
            print("WHY3 Configuration:")
            print(json.dumps(config, indent=2, ensure_ascii=False))
            
            # Generate static website
            print("\n" + "="*80)
            print("Generating static HTML website...")
            print("="*80 + "\n")
            if solver.generate_static_website("output"):
                print("Website generated successfully!")
                print("   Open 'output/index.html' in your browser to view the proofs.\n")
    else:
        print(f"Note: Example JSON not found at {json_file}")
        print("Create a JSON file with the proof structure first.\n")


if __name__ == "__main__":
    main()
