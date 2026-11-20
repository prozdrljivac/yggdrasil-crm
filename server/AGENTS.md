# Backend Instructions

## API Documentation

- Use FastAPI's generated OpenAPI schema as the API reference.
- Keep API descriptions, request and response models, and declared responses in the backend code so OpenAPI stays current.
- Do not document endpoint lists, request or response schemas, or status-code specifications in README files. README files may link to the generated API reference.
- Check the generated schema when changing API behavior.
- Do not include secrets or real business data in schema defaults, descriptions, or examples.
