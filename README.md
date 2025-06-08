# Stock Data Writer (Database)

This repository receives processed or raw stock data via a queue and writes it to a durable database
backend such as PostgreSQL or InfluxDB.

## Features

- Message queue listener with batching support
- Output to PostgreSQL, InfluxDB, or other stores
- Robust error handling and retry logic
- Optional schema validation via Pydantic
- Secure credentials via Vault
- Prometheus-ready logging and metrics
- Docker and Kubernetes deployment support

## Project Structure

```
src/
├── app/
│   ├── config.py
│   ├── main.py
│   ├── queue_handler.py        # Consumes incoming messages
│   ├── output_handler.py       # Writes to target DB
│   └── utils/
```

## Usage

```bash
make install
make run
```

## Environment Variables

| Variable      | Description                   |
| ------------- | ----------------------------- |
| `QUEUE_TYPE`  | `rabbitmq` or `sqs`           |
| `DB_TYPE`     | `postgres` or `influx`        |
| `DB_URL`      | Full connection string        |
| `VAULT_ADDR`  | Vault server address          |
| `VAULT_TOKEN` | Vault token or AppRole config |

## Development

```bash
make lint
make test
make build
```

## License

Apache License 2.0
