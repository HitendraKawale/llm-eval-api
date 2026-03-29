from app.models import EvaluationRun
from app.schemas import EvaluationRunCompareResponse, EvaluationRunCompareRow


def compare_evaluation_runs(
    *,
    run_a: EvaluationRun,
    run_b: EvaluationRun,
) -> EvaluationRunCompareResponse:
    if run_a.dataset_id != run_b.dataset_id:
        raise ValueError("Evaluation runs must belong to the same dataset.")

    results_a = {result.row_index: result for result in run_a.results}
    results_b = {result.row_index: result for result in run_b.results}

    if set(results_a.keys()) != set(results_b.keys()):
        raise ValueError("Evaluation runs must contain the same row indexes.")

    rows: list[EvaluationRunCompareRow] = []
    both_passed = 0
    both_failed = 0
    run_a_wins = 0
    run_b_wins = 0
    ties = 0

    for row_index in sorted(results_a.keys()):
        a = results_a[row_index]
        b = results_b[row_index]

        winner: str | None = None

        if a.passed is True and b.passed is not True:
            winner = "run_a"
            run_a_wins += 1
        elif b.passed is True and a.passed is not True:
            winner = "run_b"
            run_b_wins += 1
        else:
            if a.passed is True and b.passed is True:
                both_passed += 1
            elif a.passed is False and b.passed is False:
                both_failed += 1
            ties += 1

        rows.append(
            EvaluationRunCompareRow(
                row_index=row_index,
                expected_output=a.expected_output_snapshot,
                output_a=a.output_text,
                output_b=b.output_text,
                passed_a=a.passed,
                passed_b=b.passed,
                winner=winner,
            )
        )

    delta_score_mean = None
    if run_a.score_mean is not None and run_b.score_mean is not None:
        delta_score_mean = run_b.score_mean - run_a.score_mean

    delta_pass_rate = None
    if run_a.pass_rate is not None and run_b.pass_rate is not None:
        delta_pass_rate = run_b.pass_rate - run_a.pass_rate

    return EvaluationRunCompareResponse(
        run_a_id=run_a.id,
        run_b_id=run_b.id,
        dataset_id=run_a.dataset_id,
        run_a_score_mean=run_a.score_mean,
        run_b_score_mean=run_b.score_mean,
        run_a_pass_rate=run_a.pass_rate,
        run_b_pass_rate=run_b.pass_rate,
        delta_score_mean=delta_score_mean,
        delta_pass_rate=delta_pass_rate,
        both_passed=both_passed,
        both_failed=both_failed,
        run_a_wins=run_a_wins,
        run_b_wins=run_b_wins,
        ties=ties,
        rows=rows,
    )
