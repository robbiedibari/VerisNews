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

const THEME_CYCLE = { light: "sepia", sepia: "dark", dark: "light" };

function useTheme() {
  const [theme, setTheme] = useState(() => {
    const stored = localStorage.getItem("veris-theme");
    if (stored && THEME_CYCLE[stored]) return stored;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  useEffect(() => {
    const html = document.documentElement;
    html.setAttribute("data-theme", theme);
    // Keep Tailwind's dark: variant working for badge colours
    html.classList.toggle("dark", theme === "dark");
    localStorage.setItem("veris-theme", theme);
  }, [theme]);

  const cycleTheme = () => setTheme((t) => THEME_CYCLE[t] ?? "light");

  return [theme, cycleTheme];
}

export default function App() {
  const [theme, cycleTheme] = useTheme();
  const [activeSource, setActiveSource] = useState("Top Stories");

  const isTopStories = activeSource === "Top Stories";

  const { articles, loading, error, hasMore, loadMore } =
    useArticles(isTopStories || activeSource === "All" ? null : activeSource);

  const { stories, loading: topLoading } = useTopStories(10);
  const { markRead, isRead } = useReadArticles();
  const now = useNow(1000);

  return (
    <div className="min-h-screen bg-page transition-colors duration-250">
      <Header
        theme={theme}
        onCycleTheme={cycleTheme}
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
              <div className="text-center py-16 text-muted">
                <p className="text-4xl mb-3">📡</p>
                <p className="font-medium text-secondary">No articles in the last 24 hours</p>
                <p className="text-sm mt-1">New stories are fetched automatically — check back soon.</p>
              </div>
            )}

            {loading && articles.length > 0 && (
              <div className="flex justify-center py-6">
                <div className="h-6 w-6 rounded-full border-2 border-theme border-t-secondary animate-spin" />
              </div>
            )}

            <InfiniteScrollSentinel onIntersect={loadMore} enabled={hasMore && !loading} />

            {!hasMore && !loading && articles.length > 0 && (
              <p className="text-center text-xs text-muted py-8">
                All caught up — showing last 24 hours
              </p>
            )}
          </>
        )}
      </main>
    </div>
  );
}
