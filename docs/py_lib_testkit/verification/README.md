# Verification

Run the package tests with:

```bash
uv run pytest
```

Run the complete repository gate with:

```bash
uv run pre-commit run --all-files --hook-stage pre-push
```

The gate covers types, imports, complexity, security, dependency hygiene, documentation, packaging, manifest contents, and isolated distribution checks.
