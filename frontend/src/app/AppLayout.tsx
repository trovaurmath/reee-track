import AddOutlinedIcon from "@mui/icons-material/AddOutlined";
import AssignmentOutlinedIcon from "@mui/icons-material/AssignmentOutlined";
import DashboardOutlinedIcon from "@mui/icons-material/DashboardOutlined";
import DevicesOtherOutlinedIcon from "@mui/icons-material/DevicesOtherOutlined";
import HistoryOutlinedIcon from "@mui/icons-material/HistoryOutlined";
import LogoutOutlinedIcon from "@mui/icons-material/LogoutOutlined";
import MenuOutlinedIcon from "@mui/icons-material/MenuOutlined";
import SettingsOutlinedIcon from "@mui/icons-material/SettingsOutlined";
import WarehouseOutlinedIcon from "@mui/icons-material/WarehouseOutlined";
import {
  AppBar,
  Box,
  Button,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Toolbar,
  Typography,
} from "@mui/material";
import { useState, type ReactNode } from "react";
import { Link as RouterLink, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../features/auth/AuthContext";

const drawerWidth = 244;

interface NavigationItem {
  label: string;
  path: string;
  icon: ReactNode;
  visible?: boolean;
  exact?: boolean;
  section: "Operação" | "Administração";
}

const PAGE_TITLES: Array<[string, string]> = [
  ["/settings/triage", "Configuração da triagem"],
  ["/triages", "Triagem técnica"],
  ["/traceability", "Rastreabilidade"],
  ["/storage", "Armazenamento temporário"],
  ["/equipments/new", "Nova entrada"],
  ["/equipment/", "Ficha do equipamento"],
  ["/equipments", "Inventário"],
  ["/", "Visão operacional"],
];

export function AppLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const canCreate = Boolean(user?.is_superuser || user?.permissions.includes("equipment:create"));
  const canTriage = Boolean(user?.is_superuser || user?.permissions.includes("triage:execute"));
  const canConfigure = Boolean(user?.is_superuser || user?.permissions.includes("configuration:manage"));
  const items: NavigationItem[] = [
    { label: "Visão operacional", path: "/", icon: <DashboardOutlinedIcon />, exact: true, section: "Operação" },
    { label: "Inventário", path: "/equipments", icon: <DevicesOtherOutlinedIcon />, section: "Operação" },
    { label: "Nova entrada", path: "/equipments/new", icon: <AddOutlinedIcon />, visible: canCreate, section: "Operação" },
    { label: "Triagem técnica", path: "/triages", icon: <AssignmentOutlinedIcon />, visible: canTriage, section: "Operação" },
    { label: "Rastreabilidade", path: "/traceability", icon: <HistoryOutlinedIcon />, section: "Operação" },
    { label: "Armazenamento", path: "/storage", icon: <WarehouseOutlinedIcon />, section: "Operação" },
    { label: "Critérios de triagem", path: "/settings/triage", icon: <SettingsOutlinedIcon />, visible: canConfigure, section: "Administração" },
  ];
  const pageTitle = location.pathname.endsWith("/edit")
    ? "Editar equipamento"
    : PAGE_TITLES.find(([path]) => path === "/" ? location.pathname === "/" : location.pathname.startsWith(path))?.[1] ?? "REEE-Track";

  const drawer = (
    <Box display="flex" flexDirection="column" height="100%" bgcolor="#FCFCF9">
      <Box px={2.5} py={2.25}>
        <Stack direction="row" alignItems="center" gap={1.25}>
          <Box aria-hidden width={30} height={30} display="grid" gridTemplateColumns="repeat(2,1fr)" gap="3px">
            {[0, 1, 2, 3].map((item) => <Box key={item} bgcolor={item === 3 ? "secondary.main" : "primary.main"} />)}
          </Box>
          <Box>
            <Typography fontWeight={750} lineHeight={1.05} letterSpacing="-.02em">REEE-Track</Typography>
            <Typography variant="caption" color="text.secondary">Controle de resíduos eletrônicos</Typography>
          </Box>
        </Stack>
      </Box>
      <Divider />
      {(["Operação", "Administração"] as const).map((section) => {
        const sectionItems = items.filter((item) => item.section === section && item.visible !== false);
        if (!sectionItems.length) return null;
        return (
          <Box key={section} px={1.25} pt={2.25}>
            <Typography variant="overline" color="text.secondary" px={1.25}>{section}</Typography>
            <List dense disablePadding sx={{ mt: 0.75 }}>
              {sectionItems.map((item) => {
                const selected = item.exact ? location.pathname === item.path : location.pathname.startsWith(item.path);
                return (
                  <ListItemButton
                    key={item.path}
                    component={RouterLink}
                    to={item.path}
                    selected={selected}
                    onClick={() => setMobileOpen(false)}
                    sx={{
                      minHeight: 42,
                      borderRadius: 0,
                      borderLeft: "3px solid transparent",
                      color: "text.secondary",
                      "& .MuiListItemIcon-root": { minWidth: 36, color: "inherit" },
                      "&.Mui-selected": { bgcolor: "#E7EEE9", color: "primary.dark", borderLeftColor: "primary.main" },
                      "&.Mui-selected:hover": { bgcolor: "#E1EBE5" },
                    }}
                  >
                    <ListItemIcon>{item.icon}</ListItemIcon>
                    <ListItemText primary={item.label} slotProps={{ primary: { fontSize: ".9rem", fontWeight: selected ? 650 : 500 } }} />
                  </ListItemButton>
                );
              })}
            </List>
          </Box>
        );
      })}
      <Box flexGrow={1} />
      <Divider />
      <Box px={2.5} py={2}>
        <Typography variant="caption" color="text.secondary" display="block">SESSÃO ATIVA</Typography>
        <Typography variant="body2" fontWeight={650} noWrap>{user?.full_name}</Typography>
        <Stack direction="row" justifyContent="space-between" alignItems="center" mt={1}>
          <Typography variant="caption" color="text.secondary">REEE-Track 0.5</Typography>
          <IconButton size="small" onClick={() => void logout()} aria-label="Sair"><LogoutOutlinedIcon fontSize="small" /></IconButton>
        </Stack>
      </Box>
    </Box>
  );

  return (
    <Box display="flex" minHeight="100vh" bgcolor="background.default">
      <AppBar position="fixed" elevation={0} sx={{ bgcolor: "#173D34", borderBottom: 0, zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar variant="dense" sx={{ minHeight: 54 }}>
          <IconButton color="inherit" edge="start" onClick={() => setMobileOpen(!mobileOpen)} sx={{ display: { sm: "none" }, mr: 1 }} aria-label="Abrir menu"><MenuOutlinedIcon /></IconButton>
          <Typography color="rgba(255,255,255,.65)" variant="body2">REEE /</Typography>
          <Typography color="white" variant="body2" fontWeight={650} ml={0.75}>{pageTitle}</Typography>
          <Box flexGrow={1} />
          {canCreate && <Button component={RouterLink} to="/equipments/new" color="inherit" size="small" startIcon={<AddOutlinedIcon />} sx={{ border: "1px solid rgba(255,255,255,.3)", px: 1.5 }}>Registrar entrada</Button>}
        </Toolbar>
      </AppBar>
      <Box component="nav" sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}>
        <Drawer variant="temporary" open={mobileOpen} onClose={() => setMobileOpen(false)} ModalProps={{ keepMounted: true }} sx={{ display: { xs: "block", sm: "none" }, "& .MuiDrawer-paper": { width: drawerWidth, mt: "54px", height: "calc(100% - 54px)" } }}>{drawer}</Drawer>
        <Drawer variant="permanent" sx={{ display: { xs: "none", sm: "block" }, "& .MuiDrawer-paper": { width: drawerWidth, boxSizing: "border-box", borderRight: "1px solid", borderColor: "divider", mt: "54px", height: "calc(100% - 54px)" } }} open>{drawer}</Drawer>
      </Box>
      <Box component="main" flexGrow={1} width={{ sm: `calc(100% - ${drawerWidth}px)` }} minWidth={0} pt="54px"><Outlet /></Box>
    </Box>
  );
}
