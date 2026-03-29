from pydantic import BaseModel, Field


class EvaluationRunCompareQuery(BaseModel):
    run_a: str = Field(min_length=1)
    run_b: str = Field(min_length=1)


class EvaluationRunCompareRow(BaseModel):
    row_index: int
    expected_output: str | None
    output_a: str | None
    output_b: str | None
    passed_a: bool | None
    passed_b: bool | None
    winner: str | None


class EvaluationRunCompareResponse(BaseModel):
    run_a_id: str
    run_b_id: str
    dataset_id: str

    run_a_score_mean: float | None
    run_b_score_mean: float | None
    run_a_pass_rate: float | None
    run_b_pass_rate: float | None

    delta_score_mean: float | None
    delta_pass_rate: float | None

    both_passed: int
    both_failed: int
    run_a_wins: int
    run_b_wins: int
    ties: int

    rows: list[EvaluationRunCompareRow]
