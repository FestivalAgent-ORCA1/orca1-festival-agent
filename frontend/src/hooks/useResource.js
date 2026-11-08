import { useEffect, useState } from "react";

export function useResource(load, enabled = true) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState({
    status: enabled ? "loading" : "idle",
    data: null,
    error: null,
  });
  useEffect(() => {
    const controller = new AbortController();
    if (!enabled) {
      setState({ status: "idle", data: null, error: null });
      return () => controller.abort();
    }
    setState({ status: "loading", data: null, error: null });
    Promise.resolve()
      .then(() => load(controller.signal))
      .then(
        (data) => {
          if (!controller.signal.aborted)
            setState({ status: "success", data, error: null });
        },
        (error) => {
          if (!controller.signal.aborted)
            setState({ status: "error", data: null, error });
        },
      );
    return () => controller.abort();
  }, [load, enabled, attempt]);
  return { ...state, retry: () => setAttempt((value) => value + 1) };
}
