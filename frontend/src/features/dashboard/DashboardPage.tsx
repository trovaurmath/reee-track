import ArrowForwardOutlinedIcon from "@mui/icons-material/ArrowForwardOutlined";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import {
  Alert,
  Box,
  Button,
  Chip,
  Divider,
  Grid,
  LinearProgress,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { Link as RouterLink } from "react-router-dom";

import { getEquipments, getHealth, getStorageDashboard, getTraceabilityFeed } from "../../services/api";
import { useAuth } from "../auth/AuthContext";

const EVENT_LABELS: Record<string, string> = {
  COLLECTED: "Recolhimento",
  EQUIPMENT_REGISTERED: "Cadastro",
  QUEUED_FOR_TRIAGE: "Fila de triagem",
  TRIAGE_STARTED: "Triagem iniciada",
  TRIAGE_COMPLETED: "Triagem concluída",
  CLASSIFIED: "Classificação",
  STATUS_CHANGED: "Mudança de status",
  OPERATIONAL_NOTE: "Nota operacional",
  STORAGE_ENTRY: "Entrada em depósito",
  STORAGE_TRANSFER: "Transferência física",
  STORAGE_EXIT: "Saída de depósito",
  EQUIPMENT_ARCHIVED: "Exclusão segura",
};

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}

export function DashboardPage() {
  const { user, accessToken } = useAuth();
  const health = useQuery({ queryKey: ["health"], queryFn: getHealth, refetchInterval: 30_000 });
  const summary = useQuery({
    queryKey: ["equipments", "operational-summary"],
    queryFn: async () => {
      const [all, awaiting, reuse, recycling] = await Promise.all([
        getEquipments(accessToken!, { limit: 1 }),
        getEquipments(accessToken!, { limit: 1, status: "AGUARDANDO_TRIAGEM" }),
        getEquipments(accessToken!, { limit: 1, status: "SEPARADO_REUTILIZACAO" }),
        getEquipments(accessToken!, { limit: 1, status: "AGUARDANDO_RECICLAGEM" }),
      ]);
      return { total: all.total, awaiting: awaiting.total, reuse: reuse.total, recycling: recycling.total };
    },
    enabled: Boolean(accessToken),
  });
  const activity = useQuery({
    queryKey: ["traceability", "dashboard"],
    queryFn: () => getTraceabilityFeed(accessToken!, { limit: 6 }),
    enabled: Boolean(accessToken),
  });
  const storage = useQuery({
    queryKey: ["storage", "dashboard"],
    queryFn: () => getStorageDashboard(accessToken!),
    enabled: Boolean(accessToken),
  });
  const canTriage = user?.is_superuser || user?.permissions.includes("triage:execute");
  const stats = [
    ["Acervo registrado", summary.data?.total, "Total acumulado"],
    ["Aguardando triagem", summary.data?.awaiting, "Ação técnica pendente"],
    ["Separados p/ reúso", summary.data?.reuse, "Em fluxo de reutilização"],
    ["Aguardando reciclagem", summary.data?.recycling, "Em fluxo de reciclagem"],
  ];

  return (
    <Box sx={{ px: { xs: 2, md: 4 }, py: 3, maxWidth: 1500, mx: "auto" }}>
      <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" alignItems={{ md: "end" }} gap={2} mb={3}>
        <Box>
          <Typography variant="overline" color="text.secondary">{new Intl.DateTimeFormat("pt-BR", { dateStyle: "long" }).format(new Date()).toUpperCase()} · OPERAÇÃO LOCAL</Typography>
          <Typography component="h1" variant="h3" mt={0.25}>Centro de controle</Typography>
          <Typography color="text.secondary" mt={0.75}>Situação atual do fluxo de equipamentos eletroeletrônicos.</Typography>
        </Box>
        <Stack direction="row" gap={1} alignItems="center">
          <CheckCircleOutlineIcon fontSize="small" color={health.data ? "success" : "disabled"} />
          <Typography variant="body2" color="text.secondary">{health.data ? "Serviços operacionais" : "Verificando serviços"}</Typography>
        </Stack>
      </Stack>
      {health.isError && <Alert severity="error" sx={{ mb: 2 }}>A API não está pronta.</Alert>}

      <Paper variant="outlined">
        <Grid container>
          {stats.map(([label, value, description], index) => (
            <Grid key={String(label)} size={{ xs: 12, sm: 6, lg: 3 }} sx={{ borderRight: { lg: index < stats.length - 1 ? "1px solid" : 0 }, borderBottom: { xs: index < stats.length - 1 ? "1px solid" : 0, lg: 0 }, borderColor: "divider" }}>
              <Box p={2.5}>
                <Typography variant="caption" color="text.secondary" sx={{ textTransform: "uppercase", letterSpacing: ".055em" }}>{label}</Typography>
                <Typography variant="h2" mt={0.75}>{value ?? "—"}</Typography>
                <Typography variant="caption" color="text.secondary">{description}</Typography>
              </Box>
            </Grid>
          ))}
        </Grid>
      </Paper>

      <Grid container spacing={2.5} mt={0.25}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <Paper variant="outlined">
            <Stack direction="row" justifyContent="space-between" alignItems="center" px={2.5} py={1.75}>
              <Box><Typography fontWeight={650}>Atividade recente</Typography><Typography variant="caption" color="text.secondary">Últimos registros do livro de eventos</Typography></Box>
              <Button component={RouterLink} to="/traceability" size="small" endIcon={<ArrowForwardOutlinedIcon />}>Ver histórico</Button>
            </Stack>
            <Divider />
            {activity.isLoading && <LinearProgress />}
            <Table size="small">
              <TableHead><TableRow><TableCell>Horário</TableCell><TableCell>Equipamento</TableCell><TableCell>Evento</TableCell><TableCell>Registro</TableCell></TableRow></TableHead>
              <TableBody>
                {activity.data?.items.map((event) => (
                  <TableRow key={event.id}>
                    <TableCell sx={{ whiteSpace: "nowrap", color: "text.secondary" }}>{formatDate(event.timestamp)}</TableCell>
                    <TableCell><Button component={RouterLink} to={`/equipment/${event.tracking_code}`} size="small" sx={{ fontFamily: "monospace", p: 0 }}>{event.tracking_code}</Button></TableCell>
                    <TableCell><Chip size="small" variant="outlined" label={EVENT_LABELS[event.event_type] ?? event.event_type} /></TableCell>
                    <TableCell><Typography variant="body2" noWrap maxWidth={360}>{event.description}</Typography></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Paper>
        </Grid>
        <Grid size={{ xs: 12, lg: 4 }}>
          <Paper variant="outlined">
            <Box px={2.5} py={1.75}><Typography fontWeight={650}>Próximas ações</Typography><Typography variant="caption" color="text.secondary">Prioridades da operação</Typography></Box>
            <Divider />
            <Stack divider={<Divider flexItem />}>
              <Box p={2.5}>
                <Typography fontWeight={650}>
                  {summary.data?.awaiting ?? "—"} {summary.data?.awaiting === 1
                    ? "equipamento aguarda triagem"
                    : "equipamentos aguardam triagem"}
                </Typography>
                <Typography variant="body2" color="text.secondary" mt={0.5}>Concluir a avaliação libera o fluxo de destinação.</Typography>
                {canTriage && <Button component={RouterLink} to="/triages" size="small" sx={{ mt: 1.5, px: 0 }} endIcon={<ArrowForwardOutlinedIcon />}>Abrir fila</Button>}
              </Box>
              <Box p={2.5}>
                <Typography fontWeight={650}>{storage.data?.occupied_total ?? "—"} itens em armazenamento</Typography>
                <Typography variant="body2" color="text.secondary" mt={0.5}>{storage.data?.dwell_alerts ?? "—"} alerta(s) de permanência acima de 30 dias.</Typography>
                <Button component={RouterLink} to="/storage" size="small" sx={{ mt: 1.5, px: 0 }} endIcon={<ArrowForwardOutlinedIcon />}>Gerenciar posições</Button>
              </Box>
              <Box p={2.5}>
                <Typography fontWeight={650}>Rastreabilidade V0.5 ativa</Typography>
                <Typography variant="body2" color="text.secondary" mt={0.5}>Alterações, exclusões seguras e movimentações integram o histórico auditável.</Typography>
                <Button component={RouterLink} to="/traceability" size="small" sx={{ mt: 1.5, px: 0 }} endIcon={<ArrowForwardOutlinedIcon />}>Consultar eventos</Button>
              </Box>
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
