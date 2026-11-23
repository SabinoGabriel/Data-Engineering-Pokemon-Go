# Frontend Architecture

The frontend is a Next.js App Router client for configuring PvP rank filters and copying Pokemon GO search strings.

## Responsibilities

- Let the user enable or disable GL, UL, and ML filters.
- Let the user choose dynamic Top N cutoffs per league.
- Fetch the backend `/trash-string` response with debounce.
- Display copyable meta strings before the safe trash string.
- Keep the UI mobile-first and predictable for repeated use.

## Current Structure

```text
frontend/
|-- app/
|   |-- layout.tsx       # App metadata and root layout
|   |-- page.tsx         # Current client-side UI and API integration
|   `-- globals.css      # Global styles
|-- package.json
`-- tsconfig.json
```

## Current Data Flow

1. `page.tsx` stores enabled leagues and rank values in local state.
2. A debounced filter payload is sent to `POST /trash-string`.
3. The API returns per-league lists, per-league strings, combined strings, and trash strings.
4. The page renders copyable strings and filtered Pokemon list sections.

## Architecture Cleanup Plan

The current page is functional, but too much UI, typing, fetching, and rendering logic is inline. The next refactor should split the page into reusable layers:

```text
frontend/
|-- app/
|   `-- page.tsx
|-- src/
|   |-- api/
|   |   `-- trash.ts              # Fetch client and API types
|   |-- components/
|   |   |-- LeagueFilterPanel.tsx
|   |   |-- LeagueSlider.tsx
|   |   |-- SearchStringCard.tsx
|   |   `-- PokemonListSection.tsx
|   |-- hooks/
|   |   |-- useDebouncedValue.ts
|   |   `-- useTrashStrings.ts
|   `-- domain/
|       |-- leagues.ts            # League metadata and defaults
|       `-- pokemon.ts            # Display labels and shared types
```

Recommended reusable structures:

- `LEAGUES` metadata in `src/domain/leagues.ts`.
- `TrashFilters`, `PokemonSummary`, and `TrashStringResponse` in `src/api/trash.ts`.
- `useTrashStrings(filters)` to own loading, error, abort, and fetch state.
- `SearchStringCard` for every copyable string block.
- `PokemonListSection` for every rendered Pokemon list.

This makes `app/page.tsx` an orchestration shell rather than a long inline implementation.

## UI Guidelines

- Keep controls compact and mobile-first.
- Show meta strings before the trash string.
- Keep copy actions local to each string.
- Avoid duplicating league labels, default ranks, and form labels across components.
