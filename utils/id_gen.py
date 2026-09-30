from ulid import ULID

def generate_ulid(prefix: str) -> str:
    """
    Generates a time-sortable ULID with a custom prefix.
    Example output: DS-01ARZ3NDEKTSV4RRFFQ69G5FAV
    """
    return f"{prefix}-{str(ULID())}"
