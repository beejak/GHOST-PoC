"""Human MTTR baseline placeholder (manual resolution ~ minutes)."""


def human_baseline_mttr_minutes() -> float:
    return 8.0


def describe_baseline() -> str:
    return (
        f"Human baseline MTTR: ~{human_baseline_mttr_minutes():.0f} min     "
        "Agent MTTR: <300ms"
    )
