# 🌐 Website-Ausgabe

Das Skript generiert automatisch eine **statische HTML-Website** mit modernem Design.

## 📂 Struktur

```
output/
├── index.html              # Startseite mit Theorem-Übersicht
└── [theorem_id].html       # Individuelle Theorem-Seiten
```

## 🎨 Features der Website

### Index-Seite (`index.html`)
- **Tabelle** mit allen Theoremen
- **Statistiken**: Anzahl Theoreme, verifizierte Beweise, Beweis-Schritte
- **Status-Badges**: Visual Feedback für Beweisstatus
- **Responsive Design**: Funktioniert auf allen Geräten

### Theorem-Detailseiten
Jedes Theorem bekommt eine dedizierte Seite mit:
- **Header** mit Metadaten (ID, Status, Schwierigkeit, Quelle)
- **Inhaltsverzeichnis** für schnelle Navigation
- **Beschreibung** des Theorems
- **Natürlichsprachliche Aussage**
- **Formale Notation** (HOL/Why3)
- **Strukturierte Hypothesen** mit farblicher Kategorisierung
- **Bedingungen** (Fall a, b, c, ...)
- **Beweis mit Schritten** (nummeriert, mit Begründung, Referenzen)
- **Formale Ausdrücke** für jeden Schritt
- **WHY3 Solver Konfiguration** - Was der Solver erhält und wie er es nutzt
- **Fußnoten** und zusätzliche Notizen

#### WHY3 Solver Sektion
Eine dedizierte Sektion zeigt transparent:

**Beweis-Pipeline:**
```
Formale Aussage → WHY3 Solver → Verifikation
```

**Input-Parameter Tabelle:**
- Ziel-Name und ID
- Solver-Backend (why3, z3, cvc4)
- Timeout-Konfiguration
- Beweismethode
- Hypothesen-Anzahl
- Zertifikat-Generierung

**Formale Aussage:**
Zeigt die exakte formale Notation, die an WHY3 übertragen wird

**WHY3 Vollständige Konfiguration:**
JSON-Format mit allen Parametern und Einstellungen, die der Solver erhält

**Verwendete Hypothesen im Solver:**
Auflistung aller Hypothesen mit:
- Namen und Typ (Definition, Assumption, Constraint)
- Natürlichsprachlicher Ausdruck
- Formale HOL/Why3-Notation (mit Pfeil-Notation)

## 🎯 Beispiel: L'Hospital-Regel

**Datei:** `output/lhopital_7_15.html`

Diese Seite zeigt:
- Satz 7.15 - Regel von l'Hospital
- 8 Hypothesen (Definitionen, Annahmen, Constraints)
- 3 Bedingungen (Fall a, b, c)
- 6 Beweis-Schritte
- Formale und natürlichsprachliche Formulierungen
- Verweise auf zugrundeliegende Theoreme

**WHY3 Solver Section zeigt zusätzlich:**
- Welche exakte formale Aussage der Solver erhält
- Alle Parameter (Timeout, Backend, Strategie)
- Komplette JSON-Konfiguration
- Wie Hypothesen in formale Notation konvertiert werden

## 🎨 Design-Elemente

| Element | Farbe | Bedeutung |
|---------|-------|-----------|
| Definition | Grün | Definitionen von Begriffen |
| Assumption | Blau | Annahmen und Voraussetzungen |
| Constraint | Orange | Einschränkungen und Bedingungen |
| Beweis-Schritt | Violett | Nummerierte Schritte des Beweises |
| Pending | Gelb | Beweis noch nicht verifiziert |
| Verified | Grün | Beweis verifiziert |
| Failed | Rot | Beweis-Fehler |

## 🚀 Verwendung

1. Starte das Skript:
   ```bash
   python why3_solver.py
   ```

2. Öffne im Browser:
   ```
   output/index.html
   ```

3. Klicke auf ein Theorem um Details zu sehen

## 💡 Tipps

- **Schnelle Navigation**: Nutze das Inhaltsverzeichnis auf jeder Theorem-Seite
- **Lokale Ansicht**: Die Website funktioniert vollständig offline
- **Responsive**: Öffne auf Tablet oder Mobilgeräten
- **Druckbar**: Alle Seiten lassen sich drucken

---

**Generiert von:** WHY3 Proof Solver v1.0
