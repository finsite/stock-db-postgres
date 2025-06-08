# TODO — Stock DB Writer

## 🧩 Missing Features

- [ ] Add support for other database types (e.g., ClickHouse, TimescaleDB)
- [ ] Add schema versioning and migration enforcement
- [ ] Auto-create tables based on schema config
- [ ] Optional support for async writes

## 🛠️ Infrastructure Enhancements

- [ ] Add retry logic using `tenacity`
- [ ] Enable Pydantic schema validation on incoming data
- [ ] Support alternate output backends (REST, S3) via handler interface
- [ ] Add detailed metrics per batch insert

## 📈 Monitoring & Logging

- [ ] Use structured logs with metadata and status per batch
- [ ] Add Prometheus-compatible insert metrics
- [ ] Log malformed records and send to DLQ

## ✅ Security & Compliance

- [ ] Vault integration validation in CI
- [ ] Bandit + Safety + SBOM (syft or cyclonedx)
- [ ] Enable Cosign image signing
- [ ] Enable license enforcement via REUSE and license-checker

## 🧪 Testing & CI

- [ ] Add integration tests using testcontainers
- [ ] Add fixture-based unit tests for queue + output modules
- [ ] Mirror pre-commit in CI workflows

## 🧹 Code Hygiene

- [ ] Ensure typing with `pyright` and `mypy`
- [ ] Generate missing docstrings with `pyment`
- [ ] Audit and remove unused packages with `deptry`

## 🪄 Optional Enhancements

- [ ] Add REST endpoint for ingestion preview/testing
- [ ] Auto-rotate DB credentials using Vault leases
