DEFAULT_SETTINGS: dict[tuple[str, str], object] = {
    ("model", "base_directories"): [
        "./model-directories",
        r"F:\\KI\\models",
    ],
    ("model", "active_model_id"): None,
    ("model", "relevance_flags"): {},
    ("model", "prefer_gpu"): True,
    ("model", "max_loaded_models"): 1,
    ("model", "gpu_memory_limit_mb"): 11000,
    ("chat", "temperature"): 0.3,
    ("chat", "max_new_tokens"): 512,
    ("chat", "top_p"): 0.9,
    ("chat", "top_k"): 40,
    ("chat", "repetition_penalty"): 1.1,
    ("chat", "stop_sequences"): ["<end_of_turn>", "<eos>"],
    ("chat", "seed"): 42,
    ("chat", "do_sample"): True,
    ("chat", "auto_specialist_enabled"): False,
    ("chat", "stream_response"): True,
    ("chat", "context_limit_tokens"): 8192,
    ("chat", "context_safety_margin_tokens"): 128,
    ("chat", "conversation_context_limit_map"): {},
    ("chat", "conversation_generation_profiles_map"): {},
    ("chat", "conversation_project_map"): {},
    ("knowledge", "top_k"): 6,
    ("knowledge", "min_score_ratio"): 0.5,
    ("knowledge", "min_absolute_score"): 1000,
    ("knowledge", "min_score_gap"): 400,
    ("knowledge", "hybrid_search_enabled"): True,
    (
        "prompt",
        "system_prompt",
    ): (
        "Du bist ein hilfreicher Assistent. "
        "Strukturiere laengere Antworten klar und gut lesbar in Markdown. "
        "Nutze bei Bedarf kurze Ueberschriften (##, ###), kurze Absaetze und Aufzaehlungen. "
        "Vermeide lange ununterbrochene Fliesstexte. "
        "Bei technischen Antworten nutze nach Moeglichkeit: ## Ursache, ## Loesung, ## Verifikation."
    ),
    ("training", "enabled"): False,
    ("training", "default_trainer"): "peft_lora",
    ("training", "base_model"): "",
    ("training", "artifacts_directory"): "./training-artifacts",
    ("training", "datasets_directory"): "./training-datasets",
    ("training", "max_concurrent_jobs"): 1,
    ("training", "auto_start_queue"): True,
    ("training", "auto_evaluate"): True,
    ("training", "auto_register_model"): False,
    ("system", "language"): "de",
    ("system", "theme"): "system",
    ("system", "timezone"): "Europe/Berlin",
    ("system", "log_level"): "INFO",
}

SYSTEM_HARD_LIMITS: dict[tuple[str, str], object] = {
    ("chat", "max_new_tokens"): 4096,
    ("training", "max_concurrent_jobs"): 4,
}
