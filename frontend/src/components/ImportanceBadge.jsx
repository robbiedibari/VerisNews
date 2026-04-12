import React from "react";

const LEVELS = {
  Breaking:  { dot: "🔴", bg: "bg-red-100    text-red-700    dark:bg-red-900/40    dark:text-red-300",    ring: "ring-red-300    dark:ring-red-700"    },
  Critical:  { dot: "🟠", bg: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300", ring: "ring-orange-300 dark:ring-orange-700" },
  Important: { dot: "🟡", bg: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-700", ring: "ring-yellow-300 dark:ring-yellow-700" },
  Standard:  { dot: "🔵", bg: "bg-blue-100   text-blue-700   dark:bg-blue-900/40   dark:text-blue-300",   ring: "ring-blue-300   dark:ring-blue-700"   },
  Low:       { dot: "⚪", bg: "bg-slate-100  text-slate-500  dark:bg-slate-800     dark:text-slate-400",  ring: "ring-slate-300  dark:ring-slate-600"  },
};

/**
 * size="sm"  — compact pill for article cards
 * size="lg"  — larger pill for top-story cards
 */
export default function ImportanceBadge({ level, size = "sm" }) {
  if (!level) return null;
  const meta = LEVELS[level] ?? LEVELS.Standard;

  if (size === "lg") {
    return (
      <span className={`
        inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-bold
        ring-1 ${meta.ring} ${meta.bg}
      `}>
        <span>{meta.dot}</span>
        {level}
      </span>
    );
  }

  return (
    <span className={`
      inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold
      ${meta.bg}
    `}>
      <span className="text-[10px]">{meta.dot}</span>
      {level}
    </span>
  );
}
