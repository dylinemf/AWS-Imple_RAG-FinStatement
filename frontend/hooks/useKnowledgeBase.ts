import { useEffect, useState } from "react";
import { API_BASE_URL } from '../config';

export default function useKnowledgeBase() {
  const [ready, setReady] = useState<null | boolean>(null);
  const [count, setCount] = useState<number>(0);
  const [trigger, setTrigger] = useState(0);

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/chunks`)
      .then((r) => r.json())
      .then((d) => {
        setReady(Boolean(d.total_count && d.total_count > 0));
        setCount(d.total_count || 0);
      })
      .catch(() => setReady(false));
  }, [trigger]);

  function refresh() { setTrigger(v => v + 1); }
  return { ready, count, isLoading: ready === null, refresh };
}