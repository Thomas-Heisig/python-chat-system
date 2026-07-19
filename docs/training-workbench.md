# Training Workbench Architektur

## Ziel

Diese Architektur erweitert das Chat-System zu einer LLM-Workbench mit reproduzierbarem Dataset-, Training-, Evaluations- und Registrierungsfluss.

## Namensraum

Statt einer eng gefassten `finetuning`-Domane wird ein allgemeiner `training`-Namensraum verwendet.

Begruendung:

- Fine-Tuning und LoRA/QLoRA sollen gemeinsam abbildbar sein.
- Zukuenftige Verfahren (DPO, PPO, Reward Models, Reranker, Embeddings) sollen ohne Umbenennung integrierbar sein.

## Zielstruktur

```text
app/
  training/
    datasets/
      exporter.py
      validator.py
      splitter.py
      tokenizer.py
    trainers/
      base.py
      unsloth.py
      axolotl.py
      trl.py
      mlx.py
    evaluation/
      evaluator.py
      benchmark.py
    jobs/
      training_job.py
      scheduler.py
    services/
      training_service.py
    repositories/
      dataset_repository.py
      experiment_repository.py
      run_repository.py
    models/
      dataset.py
      experiment.py
      run.py
    api/
      routes.py
```

## Trainer-Abstraktion

Trainer duerfen nicht direkt an ein einzelnes Backend gekoppelt sein.

Prinzip:

```text
Trainer Interface
  -> UnslothTrainer
  -> AxolotlTrainer
  -> TRLTrainer
  -> MLXTrainer
  -> FutureTrainer
```

## Dataset-Domane

Datasets werden als eigene Domane mit Metadaten, Versionen und Reproduzierbarkeit gefuehrt.

Pflichtfelder (Minimum):

- name
- description
- created_by
- project_id
- source
- version
- num_examples
- split_train
- split_validation
- split_test
- tokenizer
- prompt_template
- license
- tags
- language
- status
- checksum
- created_at
- updated_at

## Validator-Aufgaben

`validator.py` prueft mindestens:

- JSON-Struktur
- Rollen und Nachrichtenformat
- Tokenlaengen
- Duplikate
- Datensatzqualitaet (Schema und Mindestinhalte)

## Exporter-Aufgaben

`exporter.py` erzeugt Trainingsdaten aus:

- Chats
- Bibliothek
- Dokumenten
- Bewertungen
- Projekten

Zusatz:

- Konvertierung in Prompt-Templates (z. B. ChatML, Alpaca, ShareGPT, OpenAI, Llama, Qwen, Gemma).

## Job-Lifecycle

Dokumentierter Ziel-Lifecycle (granular):

- created
- queued
- preparing
- validating
- tokenizing
- training
- evaluating
- saving
- registering
- completed

Sonderpfade:

- validating -> validation_failed
- \* -> cancelling -> cancelled
- \* -> failed

### Aktueller Implementierungsstand

- API erstellt Jobs jetzt in `queued` statt reinem Placeholder-Status.
- Ein separater Background-Worker laeuft im App-Lifecycle und verarbeitet `queued`-Jobs ohne den API-Request zu blockieren.
- Aktueller Runtime-Pfad verwendet noch `running` als Oberstatus fuer aktive Trainingsphasen; dieses Verhalten wird schrittweise auf den granularen Statussatz migriert.
- Laufzeitfortschritt wird als Runtime-Envelope am Job gespeichert (`progress`, `current_step`, `total_steps`, `current_epoch`, `loss`, `learning_rate`, `logs`).
- Trainer-Registry ist eingefuehrt und unterscheidet jetzt explizit zwischen Referenz- und Echt-Trainern (`reference`, `peft_lora`, `unsloth_lora`).
- Ein echter `PeftLoRATrainer` ist integriert (Transformers + PEFT + bitsandbytes, optional 4-bit Laden) und verarbeitet JSONL-Datasets ueber einen Dataset-Adapter.
- Simulationsstatus ist explizit: Jobs enthalten `is_simulation`, damit Referenzlaeufe im API-/Frontend-Flow klar von echten Trainingslaeufen getrennt sind.
- Lifecycle erweitert um `saving` und `validation_failed`; Validation-Fehler (z. B. Dataset-Schema/Secrets) werden nachvollziehbar als Jobstatus abgelegt.
- Base-Model-Auswahl ist zentralisiert: Training verwendet den Model Manager (`GET /api/models`) als einzige Quelle fuer Basismodelle.
- `training.base_model` dient als globales Default im Settings-Service; Job-Submission kann dieses Default ohne Duplikation von Modellscan-Logik verwenden.
- Modellwechsel-Kompatibilitaet fuer LoRA-Zielmodule: `training.target_modules` unterstuetzt den Modus `auto` (Standard), bei dem Zielmodule pro Modellarchitektur automatisch aus den linearen Layernamen abgeleitet werden.
- Fuer Spezialfaelle kann `training.target_modules` weiterhin explizit als Liste gesetzt werden (z. B. `q_proj,k_proj,v_proj,o_proj`), wenn ein fester Zielbereich erzwungen werden soll.
- Beim Job-Submit werden Registry-Metadaten (Pfad, Name, Registry-ID, Backend) in Hyperparametern mitgefuehrt, damit Trainer den konkreten Modellpfad reproduzierbar nutzen.
- Trainings-Preflight ist umgesetzt (`/api/training/preflight`) und prueft vor Jobstart Modellregistrierung, Pfad/Format, Transformers-Tokenizer-/Architektur-Checks, CUDA/4-bit-Abhaengigkeiten, Dataset-Validitaet sowie Artefaktverzeichnis und freien Speicherplatz.
- Jobstart ist bei harten Preflight-Fehlern serverseitig blockiert; das Frontend zeigt das Preflight-Ergebnis mit Fehler- und Warncodes im Training-Tab an.
- CUDA-Regel ist konfigurationsabhaengig: bei `load_in_4bit=true` bleibt fehlendes CUDA ein harter Fehler; bei `load_in_4bit=false` ist CPU-Training nur mit explizitem `allow_cpu_training=true` erlaubt, sonst blockiert der Preflight.

## Promotions-Gate

Ein trainiertes Modell wird nicht direkt aktiviert.

Verpflichtender Ablauf:

```text
Training
-> Evaluation
-> Healthcheck
-> Benchmark
-> Registrierung
-> Aktivierbar
```

## Evaluation

Nach jedem Training wird automatisch eine Evaluation gestartet.

Mindestens:

- Perplexity
- Testsatz-Ergebnis
- Antwortqualitaet
- Benchmark-Scores
- Regression-Checks

## Experiment Tracking

Jeder Run speichert:

- experiment_id
- run_id
- hyperparameters
- seed
- git_commit
- trainer_version
- cuda_version
- dataset_version
- base_model
- result_summary

## Trainingshistorie

Pro Run werden Metriken fortlaufend gespeichert:

- loss
- learning_rate
- epoch
- gradient_norm
- eta
- checkpoint
- gpu
- vram
- ram
- temperature

## GPU-Scheduling

Zur Entkopplung vom Live-Chat gilt Priorisierung:

- Prioritaet 1: Chat
- Prioritaet 2: Embedding
- Prioritaet 3: Training

## Entwicklungsreihenfolge

1. Dataset-Management (Import, Validierung, Versionierung)
2. Training-Backends (zunaechst Unsloth ueber gemeinsames Interface)
3. Job-System (Queue, Fortschritt, Abbruch)
4. Evaluation und Benchmarks
5. Modellregistrierung
6. Frontend fuer Datasets und Trainingslaeufe
