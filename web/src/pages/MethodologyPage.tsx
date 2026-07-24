import { Disclaimer } from '../components/Disclaimer';

export function MethodologyPage() {
  return (
    <article className="container prose">
      <h1>Methodology</h1>
      <p className="lead">
        How raw, lawfully collected public posts become the aggregated summaries shown on the map —
        and the safeguards applied at each step.
      </p>

      <Disclaimer />

      <h2>1. Import, not scraping</h2>
      <p>
        The project is <strong>import-first</strong>. It never bypasses logins, CAPTCHAs, rate
        limits or other access controls. A maintainer supplies posts that were collected by
        permitted means as CSV or JSON, and a documented adapter interface allows further approved
        sources to be added later.
      </p>

      <h2>2. Anonymisation</h2>
      <p>
        On import, post, comment and author identifiers are replaced with salted, non-reversible
        hashes. Source URLs are discarded. Researcher names, if present, are retained only locally
        for entity resolution and are never published, ranked or scored.
      </p>

      <h2>3. Moderation before summarisation</h2>
      <p>
        An automated pass routes sensitive content to a private, local-only moderation queue before
        anything is aggregated. It errs toward withholding and removes serious allegations and
        accusations of misconduct, identifying medical information, and personally targeted insults.
        This is a conservative safety net that supports, and never replaces, human review.
      </p>

      <h2>4. Location assignment without a default campus</h2>
      <p>
        A university-wide coordinate is not a reliable physical location for a multi-campus
        institution. The catalogue therefore keeps a display-only map centre separate from verified
        campuses, institutes and research locations. The public interface calls these{' '}
        <strong>Locations</strong> collectively and uses <strong>Campus</strong> only where the
        institution officially describes the site that way. The compatible internal schema retains
        <code>campus_id</code> and <code>campus_ids</code>.
      </p>
      <p>
        A location is assigned when a valid canonical id is provided, when raw wording matches one
        catalogue entry, or—only when safe—when the relevant lab has exactly one known campus. An
        ambiguous item remains under <strong>Location unspecified</strong>; it is never silently
        moved to an institution&rsquo;s main campus and never enters location-specific statistics.
        Raw location wording stays local and is blocked from public output.
      </p>

      <h2>5. Aggregation with evidence thresholds</h2>
      <p>
        Remaining items are grouped by lab. A lab summary is generated only when there are at least{' '}
        <strong>5 relevant items</strong> from at least <strong>3 distinct authors</strong>. Below
        that, the site shows &ldquo;Insufficient public data for a reliable summary.&rdquo; instead.
        Location summaries use the same independent threshold. A multi-location lab keeps one
        overall lab summary unless one location&rsquo;s evidence independently reaches that
        threshold. Institution totals deduplicate labs, items and authors across locations.
      </p>

      <h2>6. Local LLM summarisation</h2>
      <p>
        Summaries are produced by a <strong>local</strong> language model (via Ollama) that defaults
        to a Qwen instruct model handling Chinese and English. Raw text is only ever sent to that
        local model — never to a cloud service, a build server or the browser. The model is
        instructed to describe only supported patterns, treat every statement as an unverified
        perception, separate positive themes, challenges and neutral observations, and lower its
        confidence when evidence is sparse, contradictory or dominated by one author. Output is
        validated against a strict JSON schema, with content-hash caching so identical inputs are
        never re-summarised.
      </p>

      <h2>7. Sanitised export</h2>
      <p>
        Only aggregated, sanitised JSON is copied into the website. Every published summary reports
        its number of source items, number of distinct authors, date range and generation date. An
        automated privacy test fails the build if any forbidden field — such as a username, author
        identifier, profile URL, raw comment text or unredacted source URL — appears in the output.
      </p>

      <h2>Confidence &amp; evidence indicators</h2>
      <p>
        The site deliberately avoids a red/amber/green rating. Instead it shows a neutral
        three-segment <em>confidence</em> indicator and a plain <em>evidence</em> readout (item and
        author counts), so readers can judge how much material a summary rests on.
      </p>

      <h2>Adding Oxford and Cambridge later</h2>
      <p>
        The same model extends to future regions: add an institution display centre, then add each
        verified campus or research location with coordinate provenance and connect departments and
        labs through campus ids. Collegiate or multi-site universities must not be reduced to a
        single physical marker. Activating the region then requires no map-specific code change.
      </p>

      <p className="callout">
        See also the <a href="#/ethics">Ethics &amp; limitations</a> page for what these summaries
        can and cannot tell you.
      </p>
    </article>
  );
}
