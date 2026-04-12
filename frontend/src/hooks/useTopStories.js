import { useState, useEffect, useCallback } from "react";

const API_BASE = process.env.REACT_APP_API_URL || "/api";

export function useTopStories(n = 10) {
  const [stories,     setStories]     = useState([]);
  const [loading,     setLoading]     = useState(false);
  const [error,       setError]       = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await window.fetch(`${API_BASE}/top?n=${n}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setStories(data.articles);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [n]);

  useEffect(() => { fetch(); }, [fetch]);

  return { stories, loading, error, refresh: fetch, lastUpdated };
}
