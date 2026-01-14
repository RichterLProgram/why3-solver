# 🤖 WHY3 Solver Visualization

Die Website zeigt jetzt transparent, **was der WHY3-Solver erhält und wie er es nutzt**.

## 📋 WHY3 Sektion auf jeder Theorem-Seite

### 1. **Beweis-Pipeline Diagramm**
Visualisiert den Datenfluss:
```
Formale Aussage → WHY3 Solver → Verifikation
```

Das zeigt, dass:
- Die formale Aussage der INPUT ist
- WHY3 der PROCESSOR ist
- Das Ergebnis die VERIFIKATION ist

---

### 2. **Input-Parameter Tabelle**

Eine übersichtliche Tabelle mit allen Konfigurationsparametern:

| Parameter | Wert | Bedeutung |
|-----------|------|-----------|
| `goal_name` | Theorem-Name | Name des zu beweisenden Ziels |
| `goal_id` | Eindeutige ID | Kennung für Tracking |
| `solver` | why3 | Welcher Solver verwendet wird |
| `timeout` | 60s | Zeitlimit pro Beweis |
| `proof_strategy` | structured | Beweismethode |
| `hypotheses_count` | 8 | Anzahl Hypothesen |
| `generate_certificates` | true | Ob Zertifikate generiert werden |

**Nutzen:** Zeigt sofort, mit welchen Einstellungen der Beweis verarbeitet wird.

---

### 3. **Formale Aussage an WHY3**

Code-Block mit der exakten formalen Notation:

```
∀(a b : ℝ) (f g : ℝ → ℝ) (x₀ : ℝ),
  (a < b) ∧
  (∀x ∈ (a,b), ∃f'(x), ∃g'(x), g'(x) ≠ 0) ∧
  ...
```

**Nutzen:** Zeigt GENAU, was dem Solver übergeben wird. Dies ist die Quelle der Verifikation!

---

### 4. **WHY3 Vollständige Konfiguration (JSON)**

Die komplette Konfiguration als JSON mit allen Details:

```json
{
  "goal_name": "Satz 7.15 - Regel von l'Hospital",
  "goal_id": "lhopital_7_15",
  "solver": "why3",
  "timeout": 60,
  "formal_statement": "...",
  "hypotheses": [
    {
      "name": "domain_boundaries",
      "type": "definition",
      "expression": "a, b ∈ ℝ ∪ {-∞, ∞}",
      "formal_notation": "∀(a b : ℝ ∪ {-∞, +∞})"
    },
    ...
  ],
  "proof_strategy": "structured",
  "generate_certificates": true
}
```

**Nutzen:** 
- Reproduzierbar: Jeder kann diese exakte JSON an WHY3 übergeben
- Transparent: Keine versteckten Parameter
- Debuggbar: Kann direkt mit WHY3 CLI verwendet werden

---

### 5. **Verwendete Hypothesen im Solver**

Auflistung aller Hypothesen mit Konvertierung:

**Natürlichsprachlich:**
```
domain_boundaries (DEFINITION)
a, b ∈ ℝ ∪ {-∞, ∞}
```

**→ Formal (WHY3-Syntax):**
```
∀(a b : ℝ ∪ {-∞, +∞})
```

**Nutzen:**
- Zeigt die Transformation von menschlich-lesbaren zu formalen Aussagen
- Hilft zu verstehen, wie natürliche Mathematik in HOL übersetzt wird
- Ermöglicht Validierung: Ist die formale Notation korrekt?

---

## 🔍 Wie dies beim Debugging hilft

### Szenario 1: Der Beweis schlägt fehl
1. Man schaut auf die Website
2. Sieht die exakte WHY3-Konfiguration
3. Kann diese direkt in WHY3 debuggen
4. Findet das Problem in der formalen Notation

### Szenario 2: Man vertraut dem Beweis nicht
1. Man schaut die formale Aussage an
2. Verifiziert, dass sie mathematisch korrekt ist
3. Sieht die Hypothesen und ihre formalen Äquivalente
4. Hat Vertrauen, weil alles transparent ist

### Szenario 3: Optimierung
1. Man sieht das Timeout ist 60s
2. Kann es anpassen falls nötig
3. Sieht die Beweismethode
4. Kann Alternative (by_cases, induction) versuchen

---

## 💡 Transparenz = Vertrauenswürdigkeit

Die WHY3-Sektion macht **explizit**, was vorher implizit war:

| Vorher | Nachher |
|--------|---------|
| "Der Beweis ist verifiziert" | "Der Beweis wurde mit WHY3 mit diesen exakten Einstellungen und dieser formalen Aussage verifiziert" |
| Schwarz/Weiß | Transparent mit allen Details |
| Nicht nachvollziehbar | Reproduzierbar und debuggbar |

---

## 🚀 Für Forscher und Entwickler

Diese Sektion ist wertvoll für:

✅ **Mathematiker:** Verstehen die formale Umsetzung
✅ **Informatiker:** Können Solver-Performance analysieren
✅ **Studenten:** Lernen, wie natürliche Mathematik in HOL übersetzt wird
✅ **DevOps:** Können Probleme schnell debuggen
✅ **Reviewer:** Können die Verifikation nachvollziehen

---

**Beispiel ansehen:** `output/lhopital_7_15.html` → Scrolle zu "🤖 WHY3 Solver Konfiguration"
