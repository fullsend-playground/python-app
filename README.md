# python-app

A simple Flask REST API for managing a todo list.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Service health check |
| GET | `/items` | List all items |
| GET | `/items/:id` | Get a single item by ID |
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
