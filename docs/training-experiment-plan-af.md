# Reproduzierbarer Experiment-Plan A-F

Dieses Runbook beschreibt den standardisierten Vergleichslauf fuer Routing-Fine-Tuning.

## Ziel

- Vergleich von Legacy-Setup, kontrolliertem Setup und LoRA-Kapazitaet.
- Optionaler Transfer auf groesseres Basismodell (E).
- Optionaler Transfer auf vergroesserten Datensatz (F).

## Schritte

- A: Base-Modell Referenz (ohne Trainingsjob, nur dokumentierter Referenzschritt)
- B: Legacy-Konfiguration reproduzieren (`1 epoch`, `lr 2e-4`, `batch 1`, `grad_acc 8`)
- C: Kontrolllauf (`4 epoch`, `lr 1e-4`, `batch 1`, `grad_acc 4`, `seq 768`, `lora_r 16`)
- D: Wie C, aber `lora_r 32`
- E: Bestes Setup mit groesserem Basismodell (optional)
- F: Bestes Setup auf vergroessertem Datensatz (optional)

## Voraussetzungen

- Backend laeuft lokal (Standard: `http://127.0.0.1:8000`)
- Training ist in den Settings aktiviert
- Datensatz und Basismodell sind im System registriert

## Ausfuehrung

Beispiel mit B/C/D und optional E/F-Parametern:

```powershell
Set-Location "f:\symple chat\python-chat-system"
.\.venv-chat\Scripts\python.exe .\scripts\run_training_experiment_plan.py \
  --api-base "http://127.0.0.1:8000" \
  --user-id 1 \
  --dataset-id 75 \
  --base-model "Qwen3.5-2B" \
  --trainer-name "peft_lora" \
  --best-run D \
  --base-model-e "Qwen3.5-4B" \
  --dataset-id-f 101 \
  --run-tag "routing-af"
```

Nur Validierung des Plans ohne Job-Submit:

```powershell
.\.venv-chat\Scripts\python.exe .\scripts\run_training_experiment_plan.py \
  --dataset-id 75 \
  --base-model "Qwen3.5-2B" \
  --dry-run
```

## Ergebnisartefakt

Der Lauf schreibt einen Report nach:

- `artifacts/jobs/experiment-plan-af-last.json`

Der Report enthaelt pro Schritt:

- preflight status
- queue result
- `job_id` (falls eingereiht)
- Fehlermeldung (falls vorhanden)

## Auswertung

Nach Abschluss der Jobs liegt pro Lauf ein erweiterter Evaluation-Report unter:

- `training-artifacts/.../run-.../evaluation-report.json`

Der Report umfasst:

- `base_vs_adapter` (Basis, Adapter, Delta)
- Konfusionsmatrizen fuer `intent`, `agent`, `tool`
- Warnung bei zu kleinem Testset
