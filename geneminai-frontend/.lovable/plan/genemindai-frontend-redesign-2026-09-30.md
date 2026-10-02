# GeneMindAI Frontend Redesign

## Goal
Build a complete, premium long-scroll scientific product website that embeds the existing DNA analysis workflow without changing or mocking the FastAPI backend.

## Experience
- Create a sticky, responsive navigation with system health, smooth section links, a compact scrolled state, and a mobile menu.
- Build the full story in order: cinematic genomic hero, platform overview, scientific workflow, technology capabilities, Analysis Lab, conditional results, SHAP explainability, methodology, closing call-to-action, and footer.
- Use an original GeneMindAI identity: obsidian and midnight sections, occasional light editorial sections, cyan/teal accents, large sans-serif typography, monospace genomic details, restrained borders, subtle gradients, and custom CSS/SVG DNA and network visuals.
- Add restrained entrance, workflow, loading, and ambient motion with reduced-motion support.

## Analysis workflow
- Isolate Axios integration in `src/services/api.ts` with `VITE_API_BASE_URL` falling back to `http://localhost:8000`.
- Check `GET /` for the quiet navbar status indicator and submit normalized sequences to `POST /predict`.
- Validate empty input and DNA characters (`A T C G N`) before submission; preserve backend 400 details and distinguish server and offline failures.
- Support browser-only FASTA parsing, drag/drop and file browsing, live sequence length, Clear, Healthy sample, and the verified HbS input sample without treating HbS as a prediction class.
- Disable repeated submissions during the animated loading state.

## Results and explainability
- Reveal results only after a successful response and scroll the report into view.
- Present only Healthy or Beta Thalassemia, convert confidence to a percentage, apply the requested confidence thresholds, and show only response-backed sequence metrics and metadata.
- Display SHAP summary and bar images from the API in large responsive frames with graceful per-image fallbacks.

## Structure and quality
- Split the page into focused reusable section, navigation, lab, upload, loading, result, and visualization components.
- Replace the placeholder home route and define complete route-specific metadata.
- Extend the Tailwind v4 token system in `src/styles.css`; use semantic colors and a reusable button component rather than ad hoc visual values.
- Add Axios only; reuse the installed icon and UI foundations.
- Verify build diagnostics, desktop and mobile layouts, navigation, validation, file loading, offline handling, and conditional result behavior against the live preview.

## Boundaries
- No backend, database, authentication, mock API, client-side prediction, fabricated metrics, people, testimonials, external stock imagery, or extra routes.
- The uploaded CareVoice screenshots remain visual references only and will not be embedded.
