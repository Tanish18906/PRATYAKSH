# Ideas (not building)

Good ideas that are out of scope go here, not into code.
- Request body size limit: a 5 MB JSON body is accepted and parsed before it fails as `not_found`. Add a limit (for example 1 MB) in a middleware or at the reverse proxy if the API is ever exposed beyond localhost. Not built: single-user localhost demo.
