# Final GeneMindAI integration polish

## Scope
- Preserve the existing single-page, long-scroll GeneMindAI experience and its current styling.
- Keep all FastAPI calls centralized in the existing service and keep the `/predict`, `/`, and report-image contracts unchanged.
- Make no backend, database, authentication, mock-data, or prediction changes.

## Changes
1. Normalize the API response at the service boundary so supported response fields, including `timestamp`, are retained with strict TypeScript types.
2. Format backend timestamps safely: support standard dates and the backend’s human-readable `September 30, 2026 at 18:43:43` format, while preserving the exact backend text if it cannot be parsed. Use “Not provided” only when absent.
3. Preserve manual input, whitespace cleanup, FASTA header removal, file types, sample inputs, validation, loading, errors, clear behavior, real predictions, SHAP image URLs, and health status.
4. Verify desktop and mobile rendering, navigation, empty/invalid input, sample loading, FASTA parsing, clear behavior, API/offline handling, and SHAP fallbacks against the running preview.

## Technical note
The current project is intentionally implemented as one TanStack page with in-page navigation rather than separate page routes. This pass will preserve that established architecture and validate each named destination as a working section without introducing a second routing model.
