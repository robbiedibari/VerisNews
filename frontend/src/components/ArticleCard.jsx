import React from "react";
import ImportanceBadge from "./ImportanceBadge";

// Source badge colours
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

// CRAAP score → colour + label
function craapMeta(score) {
  if (score == null) return null;
  if (score >= 22) return { color: "text-emerald-500 dark:text-emerald-400", label: "Strong" };
  if (score >= 18) return { color: "text-green-500  dark:text-green-400",   label: "Good" };
  return              { color: "text-amber-500  dark:text-amber-400",   label: "Fair" };
}

const ExternalLinkIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5 flex-shrink-0 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
  </svg>
);

const CheckIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 00-1.414 0L8 12.586 4.707 9.293a1 1 0 00-1.414 1.414l4 4a1 1 0 001.414 0l8-8a1 1 0 000-1.414z" clipRule="evenodd" />
  </svg>
);

function timeAgo(publishedAt, now) {
  const diff = Math.max(0, now - new Date(publishedAt).getTime());
  const secs  = Math.floor(diff / 1000);
  if (secs < 60)  return "just now";
  const mins  = Math.floor(secs  / 60);
  if (mins < 60)  return `${mins}m ago`;
  const hrs   = Math.floor(mins  / 60);
  if (hrs  < 24)  return `${hrs}h ago`;
  const days  = Math.floor(hrs   / 24);
  return `${days}d ago`;
}

export default function ArticleCard({ article, isRead, onRead, now }) {
  const badgeClass = SOURCE_BADGE[article.source] ?? "bg-slate-100 text-slate-600";
  const craap      = craapMeta(article.craap_score);
  const age        = timeAgo(article.published_at, now);

  return (
    <a
      href={article.url}
      target="_blank"
      rel="noopener noreferrer"
      onClick={onRead}
      className={`group block border rounded-xl transition-all duration-150 active:scale-[0.99] overflow-hidden
        ${isRead
          ? "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800"
          : "bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 hover:shadow-md"
        }`}
    >
      {/* Read stripe + content wrapper */}
      <div className="flex">
        {/* Left accent stripe — only visible when read */}
        {isRead && (
          <div className="w-1 flex-shrink-0 bg-emerald-400 dark:bg-emerald-500 rounded-l-xl" />
        )}

        <div className="flex-1 p-4 min-w-0">
          {/* Meta row */}
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${badgeClass}`}>
              {article.source}
            </span>
            <span className="text-xs text-slate-400 dark:text-slate-500">
              {age}
            </span>

            {/* Importance badge */}
            {article.importance_level && (
              <ImportanceBadge level={article.importance_level} size="sm" />
            )}

            {/* CRAAP score badge */}
            {craap && (
              <span
                className={`text-xs font-medium ${craap.color}`}
                title={`CRAAP score: ${article.craap_score}/25 — Currency · Relevance · Authority · Accuracy · Purpose`}
              >
                ● {article.craap_score}/25
              </span>
            )}

            {/* Read indicator */}
            {isRead && (
              <span className="ml-auto flex items-center gap-1 text-xs font-medium text-emerald-500 dark:text-emerald-400">
                <CheckIcon />
                Read
              </span>
            )}
          </div>

          {/* Title — full colour always, no dimming */}
          <p className="text-sm font-medium leading-snug line-clamp-3 text-slate-800 dark:text-slate-100 group-hover:text-slate-900 dark:group-hover:text-white transition-colors">
            {article.title}
          </p>

          {/* Footer */}
          <div className="flex items-center gap-1 mt-2 text-xs text-slate-400 dark:text-slate-500">
            <ExternalLinkIcon />
            <span className="truncate">{new URL(article.url).hostname.replace("www.", "")}</span>
          </div>
        </div>
      </div>
    </a>
  );
}
