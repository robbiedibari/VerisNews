import React from "react";

export default function ErrorBanner({ message, onRetry }) {
  return (
    <div className="max-w-2xl mx-auto px-4 mt-4">
      <div className="flex items-center justify-between gap-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl px-4 py-3 text-sm text-red-700 dark:text-red-400">
        <span>Failed to load articles: {message}</span>
        <button
          onClick={onRetry}
          className="flex-shrink-0 font-medium underline underline-offset-2 hover:no-underline"
        >
          Retry
        </button>
      </div>
    </div>
  );
}
