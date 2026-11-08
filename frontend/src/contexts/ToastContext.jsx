import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
const ToastContext = createContext(null);
export function ToastProvider({ children }) {
  const [message, setMessage] = useState("");
  const timer = useRef(null);
  const notify = useCallback((text) => {
    clearTimeout(timer.current);
    setMessage(text);
    timer.current = setTimeout(() => setMessage(""), 3800);
  }, []);
  useEffect(() => () => clearTimeout(timer.current), []);
  return (
    <ToastContext.Provider value={notify}>
      {children}
      <div
        className={`toast ${message ? "show" : ""}`}
        role="status"
        aria-live="polite"
      >
        {message}
      </div>
    </ToastContext.Provider>
  );
}
export const useToast = () => useContext(ToastContext);
