import React, { useState, useEffect } from "react";
import Header from "./components/Header";
import FilterTabs from "./components/FilterTabs";
import ArticleCard from "./components/ArticleCard";
import SkeletonCard from "./components/SkeletonCard";
import ErrorBanner from "./components/ErrorBanner";
import InfiniteScrollSentinel from "./components/InfiniteScrollSentinel";
import TopStoriesSection from "./components/TopStoriesSection";
import { useArticles } from "./hooks/useArticles";
import { useReadArticles } from "./hooks/useReadArticles";
import { useNow } from "./hooks/useNow";
import { useTopStories } from "./hooks/useTopStories";

function useDarkMode() {
  const [dark, setDark] = useState(() => {
    const stored = localStorage.getItem("veris-dark-mode");
    if (stored !== null) return stored === "true";
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("veris-dark-mode", dark);
  }, [dark]);

  return [dark, () => setDark((d) => !d)];
}

export default function App() {
  const [darkMode, toggleDark] = useDarkMode();
  const [activeSource, setActiveSource] = useState("Top Stories");

  const isTopStories = activeSource === "Top Stories";

  const { articles, loading, error, hasMore, loadMore } =
    useArticles(isTopStories || activeSource === "All" ? null : activeSource);

  const { stories, loading: topLoading } = useTopStories(10);
  const { markRead, isRead } = useReadArticles();
  const now = useNow(1000);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 transition-colors duration-200">
      <Header
        darkMode={darkMode}
        onToggleDark={toggleDark}
        now={now}
      />

      <FilterTabs active={activeSource} onChange={setActiveSource} />

      <main className="max-w-2xl mx-auto px-4 py-4">
        {/* Top Stories tab */}
        {isTopStories && (
          <TopStoriesSection
            stories={stories}
            loading={topLoading}
            now={now}
            isRead={isRead}
            onRead={markRead}
          />
        )}

        {/* Regular feed tabs */}
        {!isTopStories && (
          <>
            {error && <ErrorBanner message={error} />}

            <div className="flex flex-col gap-3">
              {articles.map((article) => (
                <ArticleCard
                  key={article.id}
                  article={article}
                  isRead={isRead(article.id)}
                  onRead={() => markRead(article.id)}
                  now={now}
                />
              ))}

              {loading && articles.length === 0 &&
                Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
            </div>

            {!loading && !error && articles.length === 0 && (
              <div className="text-center py-16 text-slate-400 dark:text-slate-500">
                <p className="text-4xl mb-3">📡</p>
                <p className="font-medium">No articles in the last 24 hours</p>
                <p className="text-sm mt-1">New stories are fetched automatically — check back soon.</p>
              </div>
            )}

            {loading && articles.length > 0 && (
              <div className="flex justify-center py-6">
                <div className="h-6 w-6 rounded-full border-2 border-slate-300 dark:border-slate-600 border-t-slate-700 dark:border-t-slate-300 animate-spin" />
              </div>
            )}

            <InfiniteScrollSentinel onIntersect={loadMore} enabled={hasMore && !loading} />

            {!hasMore && !loading && articles.length > 0 && (
              <p className="text-center text-xs text-slate-400 dark:text-slate-600 py-8">
                All caught up — showing last 24 hours
              </p>
            )}
          </>
        )}
      </main>
    </div>
  );
}
