<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

- Keep GeneMindAI as one TanStack index route with in-page navigation because the product story and analysis workflow are intentionally one cohesive long-scroll experience.
- Keep FastAPI communication isolated in `src/services/api.ts` because the frontend must preserve the external backend contract without mock logic.