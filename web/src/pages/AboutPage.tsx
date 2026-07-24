export function AboutPage() {
  return (
    <article className="container prose">
      <h1>About this project</h1>
      <p className="lead">
        Lab Vibes London maps aggregated, user-reported impressions of research laboratories and
        working environments at London universities and research institutes.
      </p>

      <h2>Why it exists</h2>
      <p>
        Prospective students and researchers often rely on word of mouth when choosing a group.
        Public discussion of that experience is scattered and anecdotal. This project gathers such
        public discussion, summarises recurring themes responsibly, and presents them as perceptions
        — so the reader gets context, not a verdict.
      </p>

      <h2>How it is built</h2>
      <p>The project is split into two clearly separated parts:</p>
      <ul>
        <li>
          A <strong>local Python pipeline</strong> (Pydantic, pandas, Ollama for local LLM
          inference) that imports, anonymises, moderates, aggregates and summarises data on a
          maintainer&rsquo;s machine.
        </li>
        <li>
          A <strong>static React site</strong> (TypeScript, Vite, Leaflet with OpenStreetMap / CARTO
          tiles) that displays only the sanitised, aggregated output and is deployed via GitHub
          Pages.
        </li>
      </ul>
      <p>
        Because GitHub Pages is static and cannot run a local model, the two halves communicate only
        through sanitised JSON files. Raw data never reaches the browser or any build server.
      </p>

      <h2>Coverage</h2>
      <p>
        The initial release covers <strong>London</strong>. The data model and interface are
        designed so that <strong>Oxford</strong> and <strong>Cambridge</strong> can be added later
        through a <code>region</code> field, without changing the application architecture — hence
        the region selector already shows them as coming later.
      </p>

      <h2>Institutions in this release</h2>
      <ul>
        <li>Imperial College London</li>
        <li>University College London</li>
        <li>King&rsquo;s College London</li>
        <li>Queen Mary University of London</li>
        <li>London School of Hygiene &amp; Tropical Medicine</li>
        <li>The Francis Crick Institute</li>
      </ul>

      <h2>Demonstration data</h2>
      <p>
        The summaries shipped with this site are generated from{' '}
        <strong>synthetic, fictional</strong> demonstration data so the application works
        immediately. They contain no real posts and no real people. See the{' '}
        <a href="#/methodology">Methodology</a> and <a href="#/ethics">Ethics &amp; limitations</a>{' '}
        pages for detail.
      </p>
    </article>
  );
}
