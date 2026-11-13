import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext.jsx";
import { ToastProvider } from "./contexts/ToastContext.jsx";
import { FavoritesProvider } from "./contexts/FavoritesContext.jsx";
import { NotificationsProvider } from "./contexts/NotificationsContext.jsx";
import AppRoutes from "./router/index.jsx";
export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <NotificationsProvider>
          <ToastProvider>
            <FavoritesProvider>
              <AppRoutes />
            </FavoritesProvider>
          </ToastProvider>
        </NotificationsProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}
