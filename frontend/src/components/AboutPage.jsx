import React from "react";

const SOURCES = [
  {
    name: "AP",
    tier: "Wire service",
    why: "Non-profit cooperative owned by US member newspapers. No editorial stance — dispatches are straight-news only.",
  },
  {
    name: "AFP",
    tier: "Wire service",
    why: "French public wire service, editorially independent from the state by statute (Loi n°57-32). Global reach.",
  },
  {
    name: "BBC",
    tier: "Public broadcaster",
    why: "Royal Charter and Agreement mandate due impartiality. Regulated by Ofcom — the strongest institutional accountability framework of any outlet we carry.",
  },
  {
    name: "NPR",
    tier: "Public broadcaster",
    why: "US non-profit public radio. Editorial independence protected by NPR ethics handbook; funded by foundations with strict firewalls from editorial.",
  },
  {
    name: "DW",
    tier: "Public broadcaster",
    why: "Deutsche Welle, Germany's international broadcaster. Governed by the DW Act; editorial independence guaranteed by law.",
  },
  {
    name: "NHK",
    tier: "Public broadcaster",
    why: "NHK World, Japan's public international broadcaster. Independent editorial standards regulated under the Broadcast Act.",
  },
  {
    name: "ABC",
    tier: "Public broadcaster",
    why: "Australian Broadcasting Corporation. Statutory independence under the ABC Act 1983; editorial policies prohibit partisan content.",
  },
  {
    name: "CBC",
    tier: "Public broadcaster",
    why: "Canadian Broadcasting Corporation. Crown corporation with editorial independence protected by the Broadcasting Act.",
  },
  {
    name: "RFI",
    tier: "Public broadcaster",
    why: "Radio France Internationale. French public international broadcaster, editorially independent under France Médias Monde governance.",
  },
  {
    name: "PBS",
    tier: "Public broadcaster",
    why: "PBS NewsHour. Non-profit public TV. Journalism funded by foundations with strict firewalls between funders and editorial decisions.",
  },
];

const DIMENSIONS = [
  {
    letter: "C",
    name: "Currency",
    description:
      "How recent is the story? A story published within the last hour scores highest. After 8 hours it begins to lose value; anything beyond 24 hours is excluded entirely.",
  },
  {
    letter: "R",
    name: "Relevance",
    description:
      "Is this actual news? Opinion pieces, listicles, promotional content, celebrity stories, podcast pages, and navigation articles are hard-blocked here — no score, no entry, regardless of source authority.",
  },
  {
    letter: "A",
    name: "Authority",
    description:
      "Who published it, and in what capacity? Wire services and public broadcasters with statutory editorial independence score highest. An opinion column from a top outlet still scores lower than a straight-news dispatch from a smaller one.",
  },
  {
    letter: "A",
    name: "Accuracy",
    description:
      'Does the headline show signs of sensationalism? Weasel words ("reportedly", "sources say"), excessive punctuation, superlatives ("worst ever"), and all-caps shouting all reduce this score. Verifiable specifics — concrete numbers, named officials — increase it.',
  },
  {
    letter: "P",
    name: "Purpose",
    description:
      "Why was this published? Straight-news verbs (arrested, signed, deployed, elected) score highest. Opinion framing and soft-news topics score lowest. Geopolitics — war, sanctions, treaties, elections — receives a relevance boost.",
  },
  {
    letter: "O",
    name: "Objectivity",
    description:
      "Does the institution behind this content exercise quality control? Sponsored URLs, advertorial markers, and propaganda outlets are hard-blocked. Wire services and Ofcom-regulated broadcasters score highest.",
  },
];

function Section({ title, children }) {
  return (
    <section className="mb-10">
      <p className="text-[10px] font-black uppercase tracking-widest text-muted mb-3">
        {title}
      </p>
      {children}
    </section>
  );
}

export default function AboutPage() {
  return (
    <main className="max-w-2xl mx-auto px-4 py-8">

      {/* Mission */}
      <Section title="What Veris is">
        <p className="font-serif text-[18px] font-bold text-primary leading-snug mb-3">
          Verified news, ranked by impact.
        </p>
        <p className="text-[14px] leading-relaxed text-secondary mb-3">
          Veris is a geopolitics news aggregator that filters and ranks stories
          from ten verified international sources before you ever see them.
          Every headline in the feed has passed a multi-point quality check.
          Stories that fail — opinion, promotional content, celebrity news,
          listicles, propaganda — never reach you.
        </p>
        <p className="text-[14px] leading-relaxed text-secondary">
          There is no algorithm optimising for clicks. No personalisation.
          No ads. The ranking reflects credibility and global impact, not
          what keeps you scrolling.
        </p>
      </Section>

      {/* CRAAPO */}
      <Section title="How we score every story — CRAAPO">
        <p className="text-[14px] leading-relaxed text-secondary mb-5">
          Every story is scored across six dimensions before it enters the feed.
          The minimum passing score is <strong className="text-primary font-semibold">20 out of 30</strong>.
          Stories that score below that threshold are silently dropped.
          Top Stories are the highest-scoring articles from the last 48 hours,
          ranked by total score with a cap of two stories per source and
          two stories per major topic.
        </p>

        <div className="flex flex-col gap-3">
          {DIMENSIONS.map((d) => (
            <div key={d.name} className="flex gap-4 border border-theme rounded-lg px-4 py-3 bg-card">
              <span className="font-serif text-[20px] font-black text-muted opacity-40 w-5 flex-shrink-0 leading-none mt-0.5">
                {d.letter}
              </span>
              <div className="min-w-0">
                <p className="text-[12px] font-bold uppercase tracking-wide text-primary mb-1">
                  {d.name}
                </p>
                <p className="text-[13px] leading-relaxed text-secondary">
                  {d.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </Section>

      {/* What gets filtered */}
      <Section title="What gets filtered out">
        <div className="flex flex-col gap-1.5">
          {[
            "Opinion, commentary, and editorial columns",
            "Listicles ("10 reasons why…")",
            "Sponsored, advertorial, and partner content",
            "Celebrity and entertainment news",
            "Podcast, audio, and video-only pages",
            "Homepage navigation articles",
            "Stories older than 24 hours",
            "Weasel-word headlines with no verifiable claim",
          ].map((item) => (
            <div key={item} className="flex items-start gap-2.5">
              <span className="text-muted text-[11px] mt-0.5 flex-shrink-0">—</span>
              <p className="text-[13px] text-secondary">{item}</p>
            </div>
          ))}
        </div>
      </Section>

      {/* Sources */}
      <Section title="Our sources">
        <p className="text-[14px] leading-relaxed text-secondary mb-5">
          Every source was included against a strict set of criteria: no
          partisan ownership, no stated ideological mandate, an established
          corrections policy, and membership in a recognised press council or
          equivalent accountability body. Sources that don't meet all criteria
          are excluded — including outlets with documented state editorial
          influence.
        </p>

        <div className="flex flex-col gap-2.5">
          {SOURCES.map((s) => (
            <div key={s.name} className="border border-theme rounded-lg px-4 py-3 bg-card">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[12px] font-black uppercase tracking-wide text-primary">
                  {s.name}
                </span>
                <span className="text-[10px] font-semibold uppercase tracking-wide text-muted">
                  · {s.tier}
                </span>
              </div>
              <p className="text-[13px] leading-relaxed text-secondary">{s.why}</p>
            </div>
          ))}
        </div>
      </Section>

      {/* What we don't do */}
      <Section title="What Veris doesn't do">
        <div className="flex flex-col gap-1.5">
          {[
            "No AI ranking — every rule is deterministic and auditable",
            "No personalisation — everyone sees the same ranked feed",
            "No ads — we don't optimise for engagement",
            "No paywalled sources — every link you click is readable",
            "No opinion or analysis labelled as news",
          ].map((item) => (
            <div key={item} className="flex items-start gap-2.5">
              <span className="text-muted text-[11px] mt-0.5 flex-shrink-0">—</span>
              <p className="text-[13px] text-secondary">{item}</p>
            </div>
          ))}
        </div>
      </Section>

    </main>
  );
}
