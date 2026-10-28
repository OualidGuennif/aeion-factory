# Fresh project

Your new Fresh project is ready to go. You can follow the Fresh "Getting Started" guide here:
https://fresh.deno.dev/docs/getting-started

### Usage

Make sure to install Deno: https://docs.deno.com/runtime/getting_started/installation

Then start the project in development mode:

```
deno task dev
```

This will watch the project directory and restart as necessary.

### Docker

```
docker compose up -d --build     # the board on http://localhost:8000, healthy within 30 s
./container_check.sh             # health, non-root, clean image, data kept across restarts, frozen lock
docker compose down -v           # remove the container and its data volume
```

Ideas live in the named volume `ideas-data`; `docker compose down` keeps them, `down -v` deletes them.
