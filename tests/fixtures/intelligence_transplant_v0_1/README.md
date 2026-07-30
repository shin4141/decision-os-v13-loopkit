# Intelligence Transplant v0.1 fixtures

`valid_charter.json` is the canonical single-record lineage root used to check
exact Guided Intake bindings and self-hash behavior.

`unknown_future_charter.json` preserves a correctly self-hashed but unsupported
future version. It must remain read-only and reduce to `HOLD`.

The complete valid E1–E5 lineage and the adversarial mutations are constructed
by `tests/test_decision_os_intelligence_transplant.py`. Building those records
in dependency order keeps every exact `{object_id, content_hash}` reference
visible to each test and prevents a fixture rewrite from silently repairing the
specific tamper under test.
