"""Miscellaneous utilities used throughout analysis"""


def _type_defence(obj, exp_type, param_nm: str) -> None:
    """Assert that a passed object is of the correct type."""
    if not isinstance(obj, exp_type):
        raise TypeError(
            f"Expected an object of type {type(exp_type)} for '{param_nm}'. Got {type(obj)}"
        )
    return None
