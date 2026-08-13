import { Box, CircularProgress } from "@mui/material";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";

import { EquipmentDetailPage } from "../features/equipment/EquipmentDetailPage";
import { EquipmentFormPage } from "../features/equipment/EquipmentFormPage";
import { EquipmentListPage } from "../features/equipment/EquipmentListPage";
import { DashboardPage } from "../features/dashboard/DashboardPage";
import { useAuth } from "../features/auth/AuthContext";
import { LoginPage } from "../features/auth/LoginPage";
import { TriageConfigPage } from "../features/triage/TriageConfigPage";
import { TriagePage } from "../features/triage/TriagePage";
import { TriageQueuePage } from "../features/triage/TriageQueuePage";
import { TraceabilityPage } from "../features/traceability/TraceabilityPage";
import { StoragePage } from "../features/storage/StoragePage";
import { AppLayout } from "./AppLayout";


function LoginRoute({ authenticated }: { authenticated: boolean }) {
  const location = useLocation();
  const state = location.state as { from?: string } | null;
  return authenticated ? <Navigate to={state?.from ?? "/"} replace /> : <LoginPage />;
}

function ProtectedLayout({ authenticated }: { authenticated: boolean }) {
  const location = useLocation();
  return authenticated ? (
    <AppLayout />
  ) : (
    <Navigate to="/login" replace state={{ from: location.pathname }} />
  );
}

export function App() {
  const { user, loading } = useAuth();
  const canCreateEquipment = user?.is_superuser || user?.permissions.includes("equipment:create");
  const canUpdateEquipment = user?.is_superuser || user?.permissions.includes("equipment:update");
  const canTriage = user?.is_superuser || user?.permissions.includes("triage:execute");
  const canConfigure = user?.is_superuser || user?.permissions.includes("configuration:manage");

  if (loading) {
    return (
      <Box minHeight="100vh" display="grid" alignItems="center" justifyContent="center">
        <CircularProgress aria-label="Carregando sessão" />
      </Box>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginRoute authenticated={Boolean(user)} />} />
      <Route path="/" element={<ProtectedLayout authenticated={Boolean(user)} />}>
        <Route index element={<DashboardPage />} />
        <Route path="equipments" element={<EquipmentListPage />} />
        <Route
          path="equipments/new"
          element={canCreateEquipment ? <EquipmentFormPage /> : <Navigate to="/equipments" replace />}
        />
        <Route path="equipment/:trackingCode" element={<EquipmentDetailPage />} />
        <Route
          path="equipment/:trackingCode/edit"
          element={canUpdateEquipment ? <EquipmentFormPage /> : <Navigate to="/equipments" replace />}
        />
        <Route path="traceability" element={<TraceabilityPage />} />
        <Route path="storage" element={<StoragePage />} />
        <Route path="triages" element={canTriage ? <TriageQueuePage /> : <Navigate to="/" replace />} />
        <Route path="triages/:triageId" element={canTriage ? <TriagePage /> : <Navigate to="/" replace />} />
        <Route path="settings/triage" element={canConfigure ? <TriageConfigPage /> : <Navigate to="/" replace />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
