import { Navigate, Route, Routes } from "react-router-dom";

import { useDemo } from "./context/DemoContext";
import { CareerPage } from "./pages/CareerPage";
import { CoachPage } from "./pages/CoachPage";
import { DashboardPage } from "./pages/DashboardPage";
import { HRPage } from "./pages/HRPage";
import { ProfilePage } from "./pages/ProfilePage";
import { QuestsPage } from "./pages/QuestsPage";
import { SelectorPage } from "./pages/SelectorPage";
import { SkillsPage } from "./pages/SkillsPage";


export default function App() {
  const { employeeId } = useDemo();
  return (
    <Routes>
      <Route path="/" element={<SelectorPage />} />
      <Route path="/dashboard/:employeeId" element={<DashboardPage />} />
      <Route path="/career/:employeeId" element={<CareerPage />} />
      <Route path="/skills/:employeeId" element={<SkillsPage />} />
      <Route path="/quests/:employeeId" element={<QuestsPage />} />
      <Route path="/coach/:employeeId" element={<CoachPage />} />
      <Route path="/profile/:employeeId" element={<ProfilePage />} />
      <Route path="/hr" element={<HRPage />} />
      <Route path="*" element={<Navigate to={employeeId ? `/dashboard/${employeeId}` : "/"} replace />} />
    </Routes>
  );
}
