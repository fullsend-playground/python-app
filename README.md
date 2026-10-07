# python-app

A simple Flask REST API for managing a todo list.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |
| GET | `/items` | List all items |
| POST | `/items` | Create an item (`{"name": "..."}`) |
| PATCH | `/items/:id` | Update an item (`{"done": true}`) |
| DELETE | `/items/:id` | Delete an item |

## Development

```bash
# Install dependencies
make install

# Run locally
make run

# Run tests
make test

# Lint
make lint
```

## Docker

```bash
docker build -t python-app .
docker run -p 5000:5000 python-app
```

## Fullsend examples

See the [Pi Bash-loop example](examples/pi-script-loop/README.md) for deterministic
in-sandbox orchestration, repeatable proof commands, and sanitized evidence.
The [implementation report](docs/pi-script-loop-implementation.md) records the
Fullsend upgrade and validation.
