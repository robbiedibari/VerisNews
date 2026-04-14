import React from "react";
import ImportanceBadge from "./ImportanceBadge";

const SOURCE_BADGE = {
  AP:  "bg-blue-100   text-blue-800   dark:bg-blue-900/40   dark:text-blue-300",
  AFP: "bg-green-100  text-green-700  dark:bg-green-900/40  dark:text-green-300",
  NPR: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300",
  BBC: "bg-red-100    text-red-700    dark:bg-red-900/40    dark:text-red-300",
  DW:  "bg-amber-100  text-amber-700  dark:bg-amber-900/40  dark:text-amber-300",
  NHK: "bg-rose-100   text-rose-700   dark:bg-rose-900/40   dark:text-rose-300",
  ABC: "bg-teal-100   text-teal-700   dark:bg-teal-900/40   dark:text-teal-300",
  CBC: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300",
  RFI: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300",
  PBS: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300",
};

const ExternalLinkIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
  </svg>
);

const CheckIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 00-1.414 0L8 12.586 4.707 9.293a1 1 0 00-1.414 1.414l4 4a1 1 0 001.414 0l8-8a1 1 0 000-1.414z" clipRule="evenodd" />
  </svg>
);

function TopStoryCard({ article, rank, now, isRead, onRead }) {
  const badgeClass = SOURCE_BADGE[article.source] ?? "bg-stone-100 text-stone-600";
  const diff = Math.max(0, now - new Date(article.published_at).getTime());
  const mins = Math.floor(diff / 60000);
  const age  = mins < 60 ? `${mins}m ago` : `${Math.floor(mins / 60)}h ago`;
  const hasSummary = Boolean(article.summary);

  return (
    <div className="border border-theme rounded-xl overflow-hidden transition-all duration-150 bg-card hover:shadow-card">
      <div className="flex">
        {/* Read stripe */}
        {isRead && <div className="w-1 flex-shrink-0 bg-stripe" />}

        <div className="flex-1 p-4 min-w-0">
          {/* Rank + meta */}
          <div className="flex items-center gap-2 flex-wrap mb-2">
            <span className="flex-shrink-0 w-5 text-center text-sm font-bold text-muted">
              {rank}
            </span>
            <ImportanceBadge level={article.importance_level} size="sm" />
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${badgeClass}`}>
              {article.source}
            </span>
            <span className="text-xs text-muted">{age}</span>

            {isRead && (
              <span className="ml-auto flex items-center gap-1 text-xs font-medium text-stripe">
                <CheckIcon /> Read
              </span>
            )}
          </div>

          {/* Headline */}
          <p className="text-sm font-semibold leading-snug text-primary">
            {article.title}
          </p>

          {/* Summary */}
          {hasSummary && (
            <p className="mt-2.5 text-sm leading-relaxed text-secondary">
              {article.summary}
            </p>
          )}

          {/* Footer link */}
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={onRead}
            className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium
              text-muted hover:text-blue-600 dark:hover:text-blue-400
              transition-colors active:scale-[0.98]"
          >
            <ExternalLinkIcon />
            <span>{new URL(article.url).hostname.replace("www.", "")}</span>
            <span className="opacity-40">·</span>
            <span>Read full article</span>
          </a>
        </div>
      </div>
    </div>
  );
}

export default function TopStoriesSection({ stories, loading, now, isRead, onRead }) {
  return (
    <div className="flex flex-col gap-3">
      {loading &&
        Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-24 rounded-xl bg-skel-base animate-pulse" />
        ))
      }

      {!loading && stories.length === 0 && (
        <div className="text-center py-16 text-muted">
          <p className="text-4xl mb-3">🏆</p>
          <p className="font-medium text-secondary">No ranked stories yet</p>
          <p className="text-sm mt-1">New stories are fetched automatically — check back soon.</p>
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
