"use client";

import { useEffect, useMemo, useState } from "react";

type LeagueKey = "gl" | "ul" | "ml";

type LeagueConfig = {
  key: LeagueKey;
  label: string;
  description: string;
  max: number;
};

type Lang = "en" | "pt";

type TrashFilters = {
  gl_top: number | null;
  ul_top: number | null;
  ml_top: number | null;
  lang: Lang;
  max_length: number | null;
};

type MixedPokemon = {
  pokedex_id: number;
  nome: string;
  protected_forms: string[];
  trash_forms: string[];
};

type MixedString = {
  label: string;
  pokedex_ids: number[];
  chunks: string[];
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
  chunks: string[];
  mixed: MixedPokemon[];
  mixed_strings: MixedString[];
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

const CHUNK_OPTIONS: { label: string; value: number | null }[] = [
  { label: "Uma string so", value: null },
  { label: "Blocos de ate 300 caracteres", value: 300 },
  { label: "Blocos de ate 500 caracteres", value: 500 },
  { label: "Blocos de ate 800 caracteres", value: 800 },
];

const FORM_LABELS: Record<string, string> = {
  base: "Base/Kanto",
  alola: "Alola",
  galar: "Galar",
  hisui: "Hisui",
  paldea: "Paldea",
};

// True when the useful and useless forms sit in different regions, so a
// region search can tell them apart. Otherwise (Deoxys, Zacian...) it cannot.
function isRegionSplit(item: MixedPokemon): boolean {
  return item.trash_forms.some((form) => !item.protected_forms.includes(form));
}

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
  const [lang, setLang] = useState<Lang>("en");
  const [maxLength, setMaxLength] = useState<number | null>(null);

  const filters = useMemo<TrashFilters>(
    () => ({
      gl_top: enabled.gl ? ranks.gl : null,
      ul_top: enabled.ul ? ranks.ul : null,
      ml_top: enabled.ml ? ranks.ml : null,
      lang,
      max_length: maxLength,
    }),
    [enabled, ranks, lang, maxLength],
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
    try {
      await navigator.clipboard.writeText(value);
      setCopiedKey(key);
      window.setTimeout(() => setCopiedKey(null), 1400);
    } catch {
      setError("Nao foi possivel copiar. Selecione o texto e copie manualmente.");
    }
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
  ];
  const trashChunks = result?.chunks ?? [];
  const sameRegionMixed = (result?.mixed ?? []).filter(
    (item) => !isRegionSplit(item),
  );

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

            <div className="league-control options">
              <label>
                Idioma do jogo
                <select
                  value={lang}
                  onChange={(event) => setLang(event.target.value as Lang)}
                >
                  <option value="en">English</option>
                  <option value="pt">Portugues (nao testado)</option>
                </select>
              </label>
              <label>
                Tamanho da busca
                <select
                  value={maxLength ?? ""}
                  onChange={(event) =>
                    setMaxLength(
                      event.target.value ? Number(event.target.value) : null,
                    )
                  }
                >
                  {CHUNK_OPTIONS.map((option) => (
                    <option key={option.label} value={option.value ?? ""}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </div>

          <aside className="panel result">
            <h2>Strings meta (para guardar)</h2>
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

          <div className="panel trash-panel">
            <h2>Lixeira Segura</h2>
            <p className="notice">
              Transferir e irreversivel. Cole a string na busca do
              armazenamento e confira a lista na tela antes de transferir.
              {lang === "pt"
                ? " Os termos em portugues ainda nao foram testados no jogo, e um termo que o jogo nao reconhece e ignorado sem aviso (um Pokemon brilhante, favorito ou Dinamax poderia ser transferido). Antes de usar, busque cada termo sozinho, sem o !, e confira se a lista vem com Pokemon."
                : ""}
            </p>
            {trashChunks.length === 0 ? (
              <p className="empty-list">Nada para transferir com esses cortes.</p>
            ) : (
              <div className="string-stack">
                {trashChunks.map((chunk, index) => (
                  <SearchStringCard
                    copied={copiedKey === `trash-${index}`}
                    key={`trash-${index}`}
                    onCopy={() => copyString(`trash-${index}`, chunk)}
                    title={
                      trashChunks.length > 1
                        ? `Bloco ${index + 1} de ${trashChunks.length}`
                        : "String Lixeira Segura"
                    }
                    value={chunk}
                  />
                ))}
              </div>
            )}

            {result && result.mixed.length > 0 ? (
              <details className="mixed">
                <summary>
                  {result.mixed.length} numeros da Pokedex ficaram de fora
                  (formas mistas)
                </summary>
                <p className="notice">
                  A busca por numero pega todas as formas. Nesses casos uma
                  forma presta e outra nao, entao eles nao entram na string
                  principal para nao transferir um Pokemon util.
                </p>
                <ul className="mixed-list">
                  {result.mixed
                    .filter((item) => isRegionSplit(item))
                    .map((item) => (
                    <li key={item.pokedex_id}>
                      #{item.pokedex_id} {item.nome}: guardar{" "}
                      {item.protected_forms
                        .map((form) => FORM_LABELS[form] ?? form)
                        .join(", ")}
                      ; sobra{" "}
                      {item.trash_forms
                        .map((form) => FORM_LABELS[form] ?? form)
                        .join(", ")}
                    </li>
                  ))}
                </ul>
                {sameRegionMixed.length > 0 ? (
                  <p className="notice">
                    Tambem ficaram de fora porque tem formas de batalha ou
                    variacoes que a busca nao separa (por exemplo Deoxys,
                    Zacian, Castform):{" "}
                    {sameRegionMixed
                      .map((item) => `#${item.pokedex_id} ${item.nome}`)
                      .join(", ")}
                    . Revise esses manualmente no jogo.
                  </p>
                ) : null}
                {result.mixed_strings.length > 0 ? (
                  <>
                    <p className="notice">
                      Experimental: strings por regiao. So funcionam se a
                      busca por nome da regiao tambem trouxer as formas
                      regionais. Confira o resultado na tela antes de
                      transferir.
                    </p>
                    <div className="string-stack">
                      {result.mixed_strings.flatMap((entry) =>
                        entry.chunks.map((chunk, index) => {
                          const key = `mixed-${entry.label}-${index}`;
                          const suffix =
                            entry.chunks.length > 1
                              ? ` (${index + 1}/${entry.chunks.length})`
                              : "";
                          return (
                            <SearchStringCard
                              copied={copiedKey === key}
                              key={key}
                              onCopy={() => copyString(key, chunk)}
                              title={`${entry.label}${suffix}`}
                              value={chunk}
                            />
                          );
                        }),
                      )}
                    </div>
                  </>
                ) : null}
              </details>
            ) : null}
          </div>
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
