import React from "react";

export default function SkeletonCard() {
  return (
    <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl p-4 animate-pulse">
      <div className="flex items-center gap-2 mb-3">
        <div className="h-5 w-16 bg-slate-200 dark:bg-slate-700 rounded-full" />
        <div className="h-4 w-12 bg-slate-100 dark:bg-slate-800 rounded" />
      </div>
      <div className="space-y-2">
        <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-full" />
        <div className="h-4 bg-slate-200 dark:bg-slate-700 rounded w-5/6" />
        <div className="h-4 bg-slate-100 dark:bg-slate-800 rounded w-2/3" />
      </div>
      <div className="h-3 w-32 bg-slate-100 dark:bg-slate-800 rounded mt-3" />
    </div>
  );
}
