"use client";

import { useEffect, useMemo, useState } from "react";

type LeagueKey = "gl" | "ul" | "ml";

type LeagueConfig = {
  key: LeagueKey;
  label: string;
  description: string;
  max: number;
};

type TrashFilters = {
  gl_top: number | null;
  ul_top: number | null;
  ml_top: number | null;
};

type PokemonSummary = {
  entity_key: string;
  pokedex_id: number;
  nome: string;
  forma_regional: string;
  rank_gl: number | null;
  rank_ul: number | null;
  rank_ml: number | null;
};

type TrashStringResponse = {
  ids: number[];
  query_string: string;
  lists: {
    gl: PokemonSummary[];
    ul: PokemonSummary[];
    ml: PokemonSummary[];
    all: PokemonSummary[];
    trash: PokemonSummary[];
  };
  strings: {
    gl: string;
    ul: string;
    ml: string;
    all: string;
    trash: string;
  };
};

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

const LEAGUES: LeagueConfig[] = [
  {
    key: "gl",
    label: "Great League",
    description: "CP 1500",
    max: 150,
  },
  {
    key: "ul",
    label: "Ultra League",
    description: "CP 2500",
    max: 100,
  },
  {
    key: "ml",
    label: "Master League",
    description: "Sem limite de CP",
    max: 40,
  },
];

const DEFAULT_ENABLED: Record<LeagueKey, boolean> = {
  gl: true,
  ul: true,
  ml: true,
};

const DEFAULT_RANKS: Record<LeagueKey, number> = {
  gl: 150,
  ul: 100,
  ml: 40,
};

const FORM_LABELS: Record<string, string> = {
  base: "Base/Kanto",
  alola: "Alola",
  galar: "Galar",
  hisui: "Hisui",
  paldea: "Paldea",
};

function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timeout = window.setTimeout(() => setDebounced(value), delayMs);
    return () => window.clearTimeout(timeout);
  }, [delayMs, value]);

  return debounced;
}

export default function Home() {
  const [enabled, setEnabled] =
    useState<Record<LeagueKey, boolean>>(DEFAULT_ENABLED);
  const [ranks, setRanks] = useState<Record<LeagueKey, number>>(DEFAULT_RANKS);
  const [result, setResult] = useState<TrashStringResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const filters = useMemo<TrashFilters>(
    () => ({
      gl_top: enabled.gl ? ranks.gl : null,
      ul_top: enabled.ul ? ranks.ul : null,
      ml_top: enabled.ml ? ranks.ml : null,
    }),
    [enabled, ranks],
  );
  const debouncedFilters = useDebouncedValue(filters, 280);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    fetch(`${API_BASE_URL}/trash-string`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(debouncedFilters),
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) {
          const payload = await response.json().catch(() => null);
          throw new Error(payload?.detail ?? "Falha ao consultar a API.");
        }
        return response.json() as Promise<TrashStringResponse>;
      })
      .then((payload) => {
        setResult(payload);
      })
      .catch((fetchError: Error) => {
        if (fetchError.name !== "AbortError") {
          setError(fetchError.message);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      });

    return () => controller.abort();
  }, [debouncedFilters]);

  async function copyString(key: string, value: string) {
    if (!value) {
      return;
    }
    await navigator.clipboard.writeText(value);
    setCopiedKey(key);
    window.setTimeout(() => setCopiedKey(null), 1400);
  }

  const sections = [
    {
      title: "Great League",
      items: result?.lists.gl ?? [],
      rankKey: "rank_gl" as const,
    },
    {
      title: "Ultra League",
      items: result?.lists.ul ?? [],
      rankKey: "rank_ul" as const,
    },
    {
      title: "Master League",
      items: result?.lists.ml ?? [],
      rankKey: "rank_ml" as const,
    },
    {
      title: "Todas as ligas",
      items: result?.lists.all ?? [],
      rankKey: null,
    },
    {
      title: "Lixeira",
      items: result?.lists.trash ?? [],
      rankKey: null,
    },
  ];
  const stringSections = [
    {
      key: "gl",
      title: "String meta Great League",
      value: result?.strings.gl ?? "",
    },
    {
      key: "ul",
      title: "String meta Ultra League",
      value: result?.strings.ul ?? "",
    },
    {
      key: "ml",
      title: "String meta Master League",
      value: result?.strings.ml ?? "",
    },
    {
      key: "all",
      title: "String meta todas as ligas",
      value: result?.strings.all ?? "",
    },
    {
      key: "trash",
      title: "String Lixeira Segura",
      value: result?.strings.trash ?? result?.query_string ?? "",
    },
  ];

  return (
    <main className="app-shell">
      <div className="page">
        <header className="topbar">
          <div className="title-group">
            <h1>Lixeira Segura</h1>
            <p>
              Ajuste os cortes por liga e gere uma string de transferencia
              baseada nos rankings PvPoke mais recentes do banco local.
            </p>
          </div>
          <div className="status">{loading ? "Atualizando" : "Pronto"}</div>
        </header>

        <section className="workspace">
          <div className="panel filters" aria-label="Filtros de ranking">
            {LEAGUES.map((league) => (
              <div className="league-control" key={league.key}>
                <div className="league-copy">
                  <h2>{league.label}</h2>
                  <p>{league.description}</p>
                </div>

                <button
                  aria-label={`Alternar ${league.label}`}
                  className="toggle"
                  data-active={enabled[league.key]}
                  type="button"
                  onClick={() =>
                    setEnabled((current) => ({
                      ...current,
                      [league.key]: !current[league.key],
                    }))
                  }
                >
                  <span />
                </button>

                <div className="slider-row">
                  <input
                    aria-label={`Top ${league.label}`}
                    disabled={!enabled[league.key]}
                    max={league.max}
                    min={1}
                    onChange={(event) =>
                      setRanks((current) => ({
                        ...current,
                        [league.key]: Number(event.target.value),
                      }))
                    }
                    type="range"
                    value={ranks[league.key]}
                  />
                  <div className="rank-value">
                    {enabled[league.key] ? ranks[league.key] : "Off"}
                  </div>
                </div>
              </div>
            ))}
          </div>

          <aside className="panel result">
            <h2>Strings</h2>
            <div className="string-stack">
              {stringSections.map((section) => (
                <SearchStringCard
                  copied={copiedKey === section.key}
                  key={section.key}
                  onCopy={() => copyString(section.key, section.value)}
                  title={section.title}
                  value={section.value}
                />
              ))}
            </div>
            {error ? <p className="error">{error}</p> : null}
          </aside>
        </section>

        <section className="list-sections" aria-label="Listas filtradas">
          {sections.map((section) => (
            <PokemonListSection
              items={section.items}
              key={section.title}
              rankKey={section.rankKey}
              title={section.title}
            />
          ))}
        </section>
      </div>
    </main>
  );
}

function SearchStringCard({
  copied,
  onCopy,
  title,
  value,
}: {
  copied: boolean;
  onCopy: () => void;
  title: string;
  value: string;
}) {
  return (
    <section className="string-card">
      <div className="string-card-header">
        <h3>{title}</h3>
        <button disabled={!value} type="button" onClick={onCopy}>
          {copied ? "Copiado" : "Copiar"}
        </button>
      </div>
      <pre className="string-box">{value || "Aguardando API..."}</pre>
    </section>
  );
}

function PokemonListSection({
  items,
  rankKey,
  title,
}: {
  items: PokemonSummary[];
  rankKey: "rank_gl" | "rank_ul" | "rank_ml" | null;
  title: string;
}) {
  return (
    <section className="panel list-panel">
      <header className="list-header">
        <h2>{title}</h2>
        <span>{items.length}</span>
      </header>

      {items.length === 0 ? (
        <p className="empty-list">Nenhum Pokemon nessa lista.</p>
      ) : (
        <div className="pokemon-list">
          {items.slice(0, 80).map((pokemon) => (
            <article className="pokemon-row" key={pokemon.entity_key}>
              <div>
                <strong>
                  #{pokemon.pokedex_id} {pokemon.nome}
                </strong>
                <span>{FORM_LABELS[pokemon.forma_regional] ?? pokemon.forma_regional}</span>
              </div>
              {rankKey ? <b>#{pokemon[rankKey]}</b> : <RankBadges pokemon={pokemon} />}
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function RankBadges({ pokemon }: { pokemon: PokemonSummary }) {
  const ranks = [
    ["GL", pokemon.rank_gl],
    ["UL", pokemon.rank_ul],
    ["ML", pokemon.rank_ml],
  ] as const;

  return (
    <div className="rank-badges">
      {ranks.map(([label, rank]) =>
        rank ? (
          <span key={label}>
            {label} #{rank}
          </span>
        ) : null,
      )}
    </div>
  );
}
