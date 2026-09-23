import { useCallback, useEffect, useRef, useState } from "react";


export function useResource<T>(loader: () => Promise<T>, resourceKey = "default") {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  const loaderRef = useRef(loader);
  const requestRef = useRef(0);

  useEffect(() => {
    loaderRef.current = loader;
  }, [loader]);

  const load = useCallback(async () => {
    const requestId = ++requestRef.current;
    setLoading(true);
    setError(null);
    try {
      const result = await loaderRef.current();
      if (requestId === requestRef.current) setData(result);
    } catch (caught) {
      if (requestId === requestRef.current) {
        setError(caught instanceof Error ? caught : new Error("Unknown error"));
      }
    } finally {
      if (requestId === requestRef.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    void resourceKey;
    void Promise.resolve().then(load);
  }, [load, resourceKey]);

  return { data, error, loading, reload: load, setData };
}
