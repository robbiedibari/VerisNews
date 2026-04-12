import { useState, useEffect, useCallback, useRef } from "react";

const API_BASE = process.env.REACT_APP_API_URL || "/api";
const PER_PAGE = 20;

export function useArticles(source) {
  const [articles, setArticles] = useState([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Reset when source filter changes
  const prevSource = useRef(source);
  useEffect(() => {
    if (prevSource.current !== source) {
      prevSource.current = source;
      setArticles([]);
      setPage(1);
      setTotalPages(1);
    }
  }, [source]);

  const fetchPage = useCallback(
    async (pageNum) => {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({
        page: pageNum,
        per_page: PER_PAGE,
      });
      if (source && source !== "All") params.set("source", source);

      try {
        const res = await fetch(`${API_BASE}/articles?${params}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        setArticles((prev) =>
          pageNum === 1 ? data.articles : [...prev, ...data.articles]
        );
        setTotalPages(data.meta.pages);
        setLastUpdated(new Date());
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    },
    [source]
  );

  // Initial load + source change
  useEffect(() => {
    fetchPage(1);
  }, [fetchPage]);

  const loadMore = useCallback(() => {
    if (!loading && page < totalPages) {
      const next = page + 1;
      setPage(next);
      fetchPage(next);
    }
  }, [loading, page, totalPages, fetchPage]);

  const refresh = useCallback(() => {
    setArticles([]);
    setPage(1);
    fetchPage(1);
  }, [fetchPage]);

  return {
    articles,
    loading,
    error,
    hasMore: page < totalPages,
    loadMore,
    refresh,
    lastUpdated,
  };
}
