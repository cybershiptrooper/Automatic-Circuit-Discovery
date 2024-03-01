from dataclasses import dataclass
from pathlib import Path

import torch
from jaxtyping import Float, Integer

from acdc.nudb.adv_opt.data_fetchers import AdvOptTaskName
from acdc.nudb.adv_opt.utils import device


@dataclass
class TaskSpecificSettings:
    task_name: AdvOptTaskName
    metric_name: str = "kl_div"


@dataclass
class TracrReverseTaskSpecificSettings(TaskSpecificSettings):
    metric_name: str = "l2"

    artificially_corrupt_model: bool = True


@dataclass
class ExperimentSettings:
    task: TaskSpecificSettings
    num_epochs: int
    adam_lr: float = 1e-3
    wandb_run_name: str | None = None
    wandb_group_name: str | None = None
    use_wandb: bool = False
    random_seed: int | None = None
    use_experiment_cache: bool = False


@dataclass
class ExperimentArtifacts:
    base_input: Integer[torch.Tensor, "batch pos"] | None = None
    coefficients_init: Float[torch.Tensor, " batch"] | None = None
    coefficients_final: Float[torch.Tensor, " batch"] | None = None

    def save(self, output_dir: Path):
        output_dir.mkdir(parents=True, exist_ok=True)
        torch.save(self.base_input, output_dir / "base_input.pt")
        torch.save(self.coefficients_init, output_dir / "coefficients_init.pt")
        torch.save(self.coefficients_final, output_dir / "coefficients_final.pt")

    @classmethod
    def load(cls, output_dir: Path) -> "ExperimentArtifacts":
        map_location = torch.device("cpu") if device == "cpu" else None
        return cls(
            base_input=torch.load(output_dir / "base_input.pt", map_location=map_location),
            coefficients_init=torch.load(output_dir / "coefficients_init.pt", map_location=map_location),
            coefficients_final=torch.load(output_dir / "coefficients_final.pt", map_location=map_location),
        )

    def base_input_embedded(self, embedder: torch.nn.Module) -> Float[torch.Tensor, "batch pos vocab"]:
        return embedder(self.base_input)

    def convex_combination(self, embedder: torch.nn.Module) -> Float[torch.Tensor, "batch vocab"]:
        return torch.einsum("b,bpd -> pd", self.coefficients_final, self.base_input_embedded(embedder))
