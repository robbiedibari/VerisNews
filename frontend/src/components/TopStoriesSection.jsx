import React from "react";
import ImportanceBadge from "./ImportanceBadge";

const ArrowIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
  </svg>
);

const CheckIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-2.5 w-2.5" viewBox="0 0 20 20" fill="currentColor">
    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 00-1.414 0L8 12.586 4.707 9.293a1 1 0 00-1.414 1.414l4 4a1 1 0 001.414 0l8-8a1 1 0 000-1.414z" clipRule="evenodd" />
  </svg>
);

function TopStoryCard({ article, rank, now, isRead, onRead }) {
  const diff = Math.max(0, now - new Date(article.published_at).getTime());
  const mins = Math.floor(diff / 60000);
  const age  = mins < 60 ? `${mins}m ago` : `${Math.floor(mins / 60)}h ago`;
  const hasSummary = Boolean(article.summary);

  const craapTitle = article.craap_score != null
    ? `Source quality: ${article.craap_score}/25`
    : undefined;

  return (
    <div className="border border-theme rounded-lg overflow-hidden transition-all duration-150 bg-card hover:shadow-card">
      <div className="flex">
        {/* Read stripe */}
        {isRead && <div className="w-0.5 flex-shrink-0 bg-stripe" />}

        <div className="flex-1 px-5 py-4 min-w-0">

          {/* Meta row */}
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center gap-2">
              {/* Rank number */}
              <span className="text-[11px] font-black text-muted opacity-50 tabular-nums w-4">
                {rank}
              </span>
              <span className="text-muted opacity-20 text-xs">·</span>
              <span
                className="text-[11px] font-bold uppercase tracking-wider text-muted"
                title={craapTitle}
              >
                {article.source}
              </span>
              <span className="text-muted opacity-30 text-xs">·</span>
              <span className="text-[11px] text-muted">{age}</span>

              {isRead && (
                <span className="flex items-center gap-1 text-[10px] font-semibold text-stripe uppercase tracking-wide">
                  <CheckIcon /> Read
                </span>
              )}
            </div>

            <ImportanceBadge level={article.importance_level} />
          </div>

          {/* Headline */}
          <p className="font-serif text-[15px] font-bold leading-snug text-primary">
            {article.title}
          </p>

          {/* Summary */}
          {hasSummary && (
            <p className="mt-2.5 text-[13px] leading-relaxed text-secondary">
              {article.summary}
            </p>
          )}

          {/* Footer */}
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={onRead}
            className="mt-3 inline-flex items-center gap-1.5
              text-[11px] font-semibold uppercase tracking-wide
              text-muted hover:text-primary
              transition-colors duration-150"
          >
            <span>{new URL(article.url).hostname.replace("www.", "")}</span>
            <ArrowIcon />
          </a>

        </div>
      </div>
    </div>
  );
}

export default function TopStoriesSection({ stories, loading, now, isRead, onRead }) {
  return (
    <div className="flex flex-col gap-2.5">
      {loading &&
        Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-24 rounded-lg bg-skel-base animate-pulse" />
        ))
      }

      {!loading && stories.length === 0 && (
        <div className="text-center py-16">
          <p className="text-sm font-semibold text-secondary">No ranked stories yet</p>
          <p className="text-xs text-muted mt-1">Stories are ranked automatically every 5 hours.</p>
        </div>
      )}

      {stories.map((article, i) => (
        <TopStoryCard
          key={article.id}
          article={article}
          rank={i + 1}
          now={now}
          isRead={isRead(article.id)}
          onRead={() => onRead(article.id)}
        />
      ))}
    </div>
  );
}
