# RunPod GraphQL API Reference

## Authentication

**IMPORTANT**: Use the query parameter method, NOT Bearer token header.

### Correct Method (Tested 2024-12-23)
```bash
curl -s --request POST \
  --header 'content-type: application/json' \
  --url 'https://api.runpod.io/graphql?api_key=YOUR_API_KEY' \
  --data '{"query": "query QueryName { ... }"}'
```

### API Key Location
```bash
# Stored in ~/.zshrc
grep RUNPOD_API_KEY ~/.zshrc
# Key format: rpa_XXXXX (scoped key with rpa_ prefix)
```

### What Does NOT Work
- `Authorization: Bearer $API_KEY` header - returns `{"error": {}}`
- `Authorization: $API_KEY` header - returns `myself: null`

## Query Examples

### Check Pod Status
```bash
curl -s --request POST \
  --header 'content-type: application/json' \
  --url 'https://api.runpod.io/graphql?api_key=YOUR_KEY' \
  --data '{"query": "query Pods { myself { pods { id name desiredStatus runtime { uptimeInSeconds ports { ip isIpPublic privatePort publicPort type } } } } }"}'
```

### Start Pod (Resume)
```bash
curl -s --request POST \
  --header 'content-type: application/json' \
  --url 'https://api.runpod.io/graphql?api_key=YOUR_KEY' \
  --data '{"query": "mutation { podResume(input: { podId: \"POD_ID\" }) { id desiredStatus } }"}'
```

### Stop Pod
```bash
curl -s --request POST \
  --header 'content-type: application/json' \
  --url 'https://api.runpod.io/graphql?api_key=YOUR_KEY' \
  --data '{"query": "mutation { podStop(input: { podId: \"POD_ID\" }) { id desiredStatus } }"}'
```

## Pod Info

| Property | Value |
|----------|-------|
| Pod ID | k02604uwhjq6dm |
| Pod Name | vibevoice |
| GPU | NVIDIA RTX A6000 (48GB VRAM) |
| Network Volume | ul56y9ya5h (50GB, EU-SE-1) |
| Cost | $0.33/hr |

## Important Notes

1. **Named queries required**: Use `query QueryName { ... }` format, not just `query { ... }`
2. **SSH port changes**: After each pod restart, the public SSH port changes
3. **Ports array**: Look for `privatePort: 22` to find SSH port mapping
4. **desiredStatus values**: `RUNNING`, `EXITED`, `STOPPED`

## Sources

- [RunPod GraphQL API Spec](https://graphql-spec.runpod.io/)
- [RunPod API Keys Documentation](https://docs.runpod.io/get-started/api-keys)
- [RunPod Manage Pods GraphQL](https://github.com/runpod/docs/blob/main/docs/sdks/graphql/manage-pods.md)
