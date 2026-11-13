import { createContext, useContext, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";
import { repository } from "../api/repository.js";
import { useAuth } from "./AuthContext.jsx";

const NotificationsContext = createContext({ unread: 0, setUnread: () => {} });

// 헤더·하단 메뉴·내 정보에 보여줄 안 읽은 알림 수. 페이지를 옮길 때마다 다시 확인합니다.
export function NotificationsProvider({ children }) {
  const { status } = useAuth();
  const { pathname } = useLocation();
  const [unread, setUnread] = useState(0);
  useEffect(() => {
    if (status !== "authenticated") {
      setUnread(0);
      return undefined;
    }
    const controller = new AbortController();
    repository
      .getUnreadCount(controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) setUnread(result?.count || 0);
      })
      .catch(() => {
        /* 배지는 보조 정보라 실패해도 화면을 막지 않습니다 */
      });
    return () => controller.abort();
  }, [status, pathname]);
  return (
    <NotificationsContext.Provider value={{ unread, setUnread }}>
      {children}
    </NotificationsContext.Provider>
  );
}
export const useNotifications = () => useContext(NotificationsContext);
