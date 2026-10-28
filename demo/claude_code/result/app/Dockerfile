# Spec: knowledge/components/idea-board-runtime.md
# The latest stable Deno, pinned: the same version the app is developed and tested with.
FROM denoland/deno:2.9.8

WORKDIR /app
# The deno user owns the app and the volume mount point, so nothing after this runs as root.
RUN mkdir -p /data && chown deno:deno /app /data
USER deno

# Dependencies first, so a code change reuses this layer; --frozen fails when the lock does not match.
COPY --chown=deno:deno deno.json deno.lock ./
RUN deno install --frozen

# One production build, inside the image.
COPY --chown=deno:deno . .
RUN deno task build

ENV PORT=8000 KV_PATH=/data/ideas.sqlite3
EXPOSE 8000
# Only what the server needs: the network, its env, reading the app, and writing the KV volume; no download at run time.
CMD ["deno", "run", "--cached-only", "--allow-net", "--allow-env", "--allow-read=/app,/data", "--allow-write=/data", "serve.ts"]
