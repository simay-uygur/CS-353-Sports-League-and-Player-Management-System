# CS-353-Sports-League-and-Player-Management-System

## Dev Environment
### Setup
Commands to run:

```bash
docker compose -f docker-compose.yml --build
docker compose up --build
```

## Teardown
Commands to run:
```bash
docker compose down
```

If you want to start from init.sql (delete you changes for the db volume):
```bash
docker compose down -v
```
