import { Routes, Route } from "react-router-dom";
import PageLayout from "../components/layout/PageLayout.jsx";
import HomePage from "../pages/HomePage.jsx";
import FestivalListPage from "../pages/FestivalListPage.jsx";
import FestivalDetailPage from "../pages/FestivalDetailPage.jsx";
import LikesPage from "../pages/LikesPage.jsx";
import UnavailablePage from "../pages/UnavailablePage.jsx";
import ChatPage from "../pages/ChatPage.jsx";
import MySchedulesPage from "../pages/MySchedulesPage.jsx";
import ScheduleDetailPage from "../pages/ScheduleDetailPage.jsx";

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<PageLayout />}>
        <Route index element={<HomePage />} />
        <Route path="festivals" element={<FestivalListPage />} />
        <Route path="festivals/:contentId" element={<FestivalDetailPage />} />
        <Route path="likes" element={<LikesPage />} />
        {/* FE2: AI 채팅 · 내 일정 */}
        <Route path="chat" element={<ChatPage />} />
        <Route path="schedules" element={<MySchedulesPage />} />
        <Route path="schedules/:id" element={<ScheduleDetailPage />} />
        {/* FE3의 LoginPage가 완성되면 이 경로의 element만 교체합니다. */}
        <Route path="login" element={<UnavailablePage />} />
        <Route path="*" element={<UnavailablePage />} />
      </Route>
    </Routes>
  );
}
