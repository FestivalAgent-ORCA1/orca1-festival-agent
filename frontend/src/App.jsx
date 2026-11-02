import { BrowserRouter } from "react-router-dom";
import { ToastProvider } from "./contexts/ToastContext.jsx";
import { FavoritesProvider } from "./contexts/FavoritesContext.jsx";
import AppRoutes from "./router/index.jsx";
export default function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <FavoritesProvider>
          <AppRoutes />
        </FavoritesProvider>
      </ToastProvider>
    </BrowserRouter>
  );
}
