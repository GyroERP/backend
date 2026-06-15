"""
DomainEvaluator — converts a JSON domain expression to a Django Q object.

Domain format (identical shape to Odoo's, but implemented independently):
    [["field", "operator", "value"], ["field2", "op2", "value2"], ...]

All top-level conditions are AND-joined.  Nested OR/AND is not supported in
this version — the kernel keeps it simple and adds it later if needed.

Supported operators
-------------------
=       exact match
!=      exclude
<       less than
<=      less than or equal
>       greater than
>=      greater than or equal
in      value must be a list; maps to field__in
not in  value must be a list; maps to ~field__in
like    case-insensitive contains  (maps to field__icontains)
ilike   alias for like

Context variables
-----------------
String values starting with "@" are resolved from the context dict:
    "@user_id"     → context["user_id"]
    "@company_id"  → context["company_id"]
    "@company_ids" → context["company_ids"]

Raises DomainError (subclass of ValueError) for unknown operators or
malformed domain structure.  Never calls eval() or exec().
"""

from __future__ import annotations

from django.db.models import Q


class DomainError(ValueError):
    """Raised when a domain expression is structurally invalid or uses unknown operators."""


_OP_MAP: dict[str, str] = {
    "=": "exact",
    "!=": None,  # handled specially (negation)
    "<": "lt",
    "<=": "lte",
    ">": "gt",
    ">=": "gte",
    "in": "in",
    "not in": None,  # handled specially
    "like": "icontains",
    "ilike": "icontains",
}

# Field name segments that must never be reachable via domain traversal.
# These protect against ORM-path attacks like ["user.password", "!=", ""]
# that would let a user enumerate sensitive column values via boolean oracles.
# ISO 27001 A.14.2.5 — Secure development principles.
_BLOCKED_SEGMENTS: frozenset[str] = frozenset({
    "password",
    "hashed_key",
    "secret",
    "token",
    "hash",
    "private_key",
    "secret_key",
    "api_secret",
    "smtp_password",
})


def _validate_field(field: str) -> None:
    """
    Reject field names that traverse into sensitive model attributes.

    Segments separated by '.' (which become '__' in ORM lookups) are each
    checked individually.  This allows legitimate FK traversal like
    'company.name' while blocking 'user.password' or 'api_key.hashed_key'.
    """
    if not field or not isinstance(field, str):
        raise DomainError(f"Domain field must be a non-empty string, got: {field!r}")

    segments = field.replace(".", "__").split("__")
    for seg in segments:
        if not seg:
            raise DomainError(f"Empty segment in domain field '{field}'")
        if not seg.replace("_", "").isalnum():
            raise DomainError(
                f"Domain field segment '{seg}' in '{field}' contains illegal characters. "
                "Only letters, digits, and underscores are allowed."
            )
        if seg in _BLOCKED_SEGMENTS:
            raise DomainError(
                f"Field traversal into '{seg}' is not permitted in domain expressions. "
                "Access to sensitive attributes is restricted."
            )


class DomainEvaluator:
    """Stateless converter from JSON domain lists to Django Q objects."""

    def to_q(self, domain: list, context: dict | None = None) -> Q:
        """
        Convert domain to a Django Q object (AND of all conditions).

        Parameters
        ----------
        domain:
            List of [field, operator, value] triples.
        context:
            Optional dict for resolving @variable references in values.

        Returns
        -------
        Q object — pass directly to queryset.filter(q).
        """
        if not isinstance(domain, list):
            raise DomainError(f"Domain must be a list, got {type(domain).__name__}")

        if not domain:
            return Q()

        q = Q()
        for item in domain:
            q &= self._condition_to_q(item, context or {})
        return q

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _condition_to_q(self, condition: list, context: dict) -> Q:
        if not isinstance(condition, (list, tuple)) or len(condition) != 3:
            raise DomainError(
                f"Each domain condition must be a [field, op, value] triple, got: {condition!r}"
            )

        field, op, value = condition

        # Validate field name before any ORM translation
        _validate_field(field)

        if op not in _OP_MAP:
            raise DomainError(
                f"Unknown domain operator '{op}'. "
                f"Supported: {', '.join(sorted(_OP_MAP))}"
            )

        value = self._resolve_value(value, context)

        # Django ORM field name: replace dots with __ for related fields
        orm_field = field.replace(".", "__")

        if op == "=":
            return Q(**{orm_field: value})

        if op == "!=":
            return ~Q(**{orm_field: value})

        if op == "in":
            if not isinstance(value, (list, tuple)):
                raise DomainError(f"'in' operator requires a list value, got {type(value).__name__}")
            return Q(**{f"{orm_field}__in": value})

        if op == "not in":
            if not isinstance(value, (list, tuple)):
                raise DomainError(f"'not in' operator requires a list value, got {type(value).__name__}")
            return ~Q(**{f"{orm_field}__in": value})

        # All remaining ops map 1-to-1 to Django ORM lookup suffixes
        lookup = _OP_MAP[op]
        return Q(**{f"{orm_field}__{lookup}": value})

    @staticmethod
    def _resolve_value(value, context: dict):
        """Replace '@variable' references with context values."""
        if isinstance(value, str) and value.startswith("@"):
            key = value[1:]
            if key not in context:
                raise DomainError(
                    f"Domain context variable '@{key}' not found in context. "
                    f"Available: {list(context)}"
                )
            return context[key]
        return value
