from app.training.trainers.peft_lora import _create_training_arguments


def test_training_arguments_transformers_5_aliases() -> None:
    class ArgumentsV5:
        def __init__(self, output_dir=None, eval_strategy="no", use_cpu=False):
            self.output_dir = output_dir
            self.eval_strategy = eval_strategy
            self.use_cpu = use_cpu

    result = _create_training_arguments(ArgumentsV5, {"output_dir": "out", "no_cuda": True}, force_cpu=True)

    assert result.eval_strategy == "steps"
    assert result.use_cpu is True
    assert not hasattr(result, "no_cuda")


def test_training_arguments_transformers_4_aliases() -> None:
    class ArgumentsV4:
        def __init__(self, output_dir=None, evaluation_strategy="no", no_cuda=False):
            self.evaluation_strategy = evaluation_strategy
            self.no_cuda = no_cuda

    result = _create_training_arguments(ArgumentsV4, {"output_dir": "out"}, force_cpu=True)

    assert result.evaluation_strategy == "steps"
    assert result.no_cuda is True


def test_training_arguments_tolerates_stale_signature() -> None:
    class StaleSignature:
        def __init__(self, output_dir=None, no_cuda=False):
            if no_cuda:
                raise TypeError("TrainingArguments.__init__() got an unexpected keyword argument 'no_cuda'")
            self.output_dir = output_dir

    result = _create_training_arguments(StaleSignature, {"output_dir": "out"}, force_cpu=True)

    assert result.output_dir == "out"
