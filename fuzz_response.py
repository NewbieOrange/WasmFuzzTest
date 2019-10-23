from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class FuzzResponse:
    origin_wast: str
    mutation_wast: str
    run_results: dict


@dataclass_json
@dataclass
class RunResult:
    return_code: int
    stdout: str
    stderr: str


@dataclass_json
@dataclass
class VMResult:
    origin_result: RunResult
    mutation_result: RunResult
