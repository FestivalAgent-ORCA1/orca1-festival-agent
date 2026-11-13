import { Routes, Route } from "react-router-dom";
import PageLayout from "../components/layout/PageLayout.jsx";
import HomePage from "../pages/HomePage.jsx";
import FestivalListPage from "../pages/FestivalListPage.jsx";
import FestivalDetailPage from "../pages/FestivalDetailPage.jsx";
import LikesPage from "../pages/LikesPage.jsx";
import UnavailablePage from "../pages/UnavailablePage.jsx";
import LoginPage from "../pages/LoginPage.jsx";
import SignupPage from "../pages/SignupPage.jsx";
import OnboardingPage from "../pages/OnboardingPage.jsx";
import ChatPage from "../pages/ChatPage.jsx";
import MySchedulesPage from "../pages/MySchedulesPage.jsx";
import ScheduleDetailPage from "../pages/ScheduleDetailPage.jsx";
import CommunityPage from "../pages/CommunityPage.jsx";
import PostDetailPage from "../pages/PostDetailPage.jsx";
import PostWritePage from "../pages/PostWritePage.jsx";
import ProfilePage from "../pages/ProfilePage.jsx";

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
        {/* FE3: 로그인 · 가입 · 첫 설정 */}
        <Route path="login" element={<LoginPage />} />
        <Route path="signup" element={<SignupPage />} />
        <Route path="onboarding" element={<OnboardingPage />} />
        {/* FE3: 커뮤니티 */}
        <Route path="community" element={<CommunityPage />} />
        <Route path="community/write" element={<PostWritePage />} />
        <Route path="community/:id" element={<PostDetailPage />} />
        <Route path="community/:id/edit" element={<PostWritePage />} />
        {/* FE3: 내 정보 */}
        <Route path="profile" element={<ProfilePage />} />
        <Route path="*" element={<UnavailablePage />} />
      </Route>
    </Routes>
  );
}
