## Operational Context
RLM project - Postgres + pgvector context store.
- lib/db/schema.py contains SQLAlchemy models
- lib/db/migrations/0001_init.sql has SQL schema
- Current: VECTOR(2048) hardcoded, should be dynamic
- Models: RLMDocument, RLMChunk, RLMEmbedding
- Related issues: rlm-r0z, rlm-29t
