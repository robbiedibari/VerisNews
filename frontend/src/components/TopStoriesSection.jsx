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

function TopStoryCard({ article, rank, now, isRead, onRead }) {
  const badgeClass = SOURCE_BADGE[article.source] ?? "bg-slate-100 text-slate-600";
  const diff = Math.max(0, now - new Date(article.published_at).getTime());
  const mins = Math.floor(diff / 60000);
  const age  = mins < 60 ? `${mins}m ago` : `${Math.floor(mins / 60)}h ago`;

  return (
    <a
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      onClick={onRead}
      className={`group flex gap-3 p-3 rounded-xl border transition-all duration-150 active:scale-[0.99]
        ${isRead
          ? "bg-slate-50 dark:bg-slate-900/40 border-slate-100 dark:border-slate-800/50 opacity-60"
          : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 hover:shadow-sm"
        }`}
    >
      {/* Rank number */}
      <span className="flex-shrink-0 w-6 text-center text-sm font-bold text-slate-300 dark:text-slate-600 mt-0.5">
        {rank}
      </span>

      {/* Content */}
      <div className="min-w-0 flex-1">
        {/* Importance + source + time */}
        <div className="flex items-center gap-2 flex-wrap mb-1.5">
          <ImportanceBadge level={article.importance_level} size="sm" />
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${badgeClass}`}>
            {article.source}
          </span>
          <span className="text-xs text-slate-400 dark:text-slate-500">{age}</span>
        </div>

        <p className={`text-sm leading-snug line-clamp-2
          ${isRead
            ? "text-slate-400 dark:text-slate-500 font-normal"
            : "text-slate-800 dark:text-slate-100 font-medium group-hover:text-slate-900 dark:group-hover:text-white"
          }`}
        >
          {article.title}
        </p>
      </div>
    </a>
  );
}

export default function TopStoriesSection({ stories, loading, now, isRead, onRead }) {
  return (
    <div className="flex flex-col gap-3">
      {loading && (
        Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-16 rounded-xl bg-slate-100 dark:bg-slate-800 animate-pulse" />
        ))
      )}

      {!loading && stories.length === 0 && (
        <div className="text-center py-16 text-slate-400 dark:text-slate-500">
          <p className="text-4xl mb-3">🏆</p>
          <p className="font-medium">No ranked stories yet</p>
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
