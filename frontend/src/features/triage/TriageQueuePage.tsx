import AssignmentTurnedInOutlinedIcon from "@mui/icons-material/AssignmentTurnedInOutlined";
import PlayArrowOutlinedIcon from "@mui/icons-material/PlayArrowOutlined";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  Grid,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";

import { getTriageQueue, startTriage } from "../../services/api";
import { useAuth } from "../auth/AuthContext";

export function TriageQueuePage() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const queue = useQuery({ queryKey: ["triage-queue"], queryFn: () => getTriageQueue(accessToken!), enabled: Boolean(accessToken) });
  const start = useMutation({
    mutationFn: (trackingCode: string) => startTriage(accessToken!, trackingCode),
    onSuccess: (triage) => { void queryClient.invalidateQueries({ queryKey: ["triage-queue"] }); navigate(`/triages/${triage.id}`); },
  });
  const waiting = queue.data?.items.filter((item) => !item.active_triage_id).length ?? 0;
  const inProgress = queue.data?.items.filter((item) => item.active_triage_id).length ?? 0;

  return (
    <Box sx={{ px: { xs: 2, md: 4 }, py: 3, maxWidth: 1500, mx: "auto" }}>
      <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" alignItems={{ md: "end" }} gap={2} mb={3}>
        <Box><Typography variant="overline" color="text.secondary">OPERAÇÃO TÉCNICA</Typography><Typography component="h1" variant="h3">Fila de triagem</Typography><Typography color="text.secondary" mt={0.75}>Avaliações pendentes e trabalhos já assumidos pela equipe.</Typography></Box>
        <Grid container component={Paper} variant="outlined" sx={{ minWidth: { md: 340 } }}>
          <Grid size={6}><Box p={1.75}><Typography variant="caption" color="text.secondary">AGUARDANDO</Typography><Typography variant="h4">{waiting}</Typography></Box></Grid>
          <Grid size={6} borderLeft={1} borderColor="divider"><Box p={1.75}><Typography variant="caption" color="text.secondary">EM ANDAMENTO</Typography><Typography variant="h4">{inProgress}</Typography></Box></Grid>
        </Grid>
      </Stack>
      {queue.isLoading && <Box textAlign="center" py={8}><CircularProgress /></Box>}
      {queue.error && <Alert severity="error">{(queue.error as Error).message}</Alert>}
      {start.error && <Alert severity="error" sx={{ mb: 2 }}>{(start.error as Error).message}</Alert>}
      {queue.data?.items.length === 0 && <Paper variant="outlined" sx={{ textAlign: "center", py: 8 }}><AssignmentTurnedInOutlinedIcon color="success" sx={{ fontSize: 48 }} /><Typography variant="h5" mt={1}>Fila concluída</Typography><Typography color="text.secondary">Nenhum equipamento aguarda triagem.</Typography></Paper>}
      {queue.data && queue.data.items.length > 0 && (
        <Paper variant="outlined">
          <Box px={2.5} py={1.75}><Typography fontWeight={650}>Equipamentos para avaliação</Typography><Typography variant="caption" color="text.secondary">Ordenação operacional da fila</Typography></Box><Divider />
          <TableContainer>
            <Table>
              <TableHead><TableRow><TableCell>Código</TableCell><TableCell>Equipamento</TableCell><TableCell>Origem</TableCell><TableCell>Patrimônio</TableCell><TableCell>Situação</TableCell><TableCell align="right">Ação</TableCell></TableRow></TableHead>
              <TableBody>
                {queue.data.items.map((item) => (
                  <TableRow key={item.equipment_id} hover>
                    <TableCell sx={{ fontFamily: "monospace", fontWeight: 650 }}>{item.tracking_code}</TableCell>
                    <TableCell><Typography fontWeight={600}>{item.equipment_description}</Typography><Typography variant="caption" color="text.secondary">{item.category_name}</Typography></TableCell>
                    <TableCell>{item.origin_sector_name}</TableCell>
                    <TableCell>{item.asset_number ?? "—"}</TableCell>
                    <TableCell><Chip size="small" color={item.active_triage_id ? "warning" : "default"} variant="outlined" label={item.active_triage_id ? `Em andamento · ${item.evaluator_name ?? "Equipe"}` : "Aguardando"} /></TableCell>
                    <TableCell align="right"><Button variant={item.active_triage_id ? "outlined" : "contained"} size="small" startIcon={<PlayArrowOutlinedIcon />} disabled={start.isPending} onClick={() => item.active_triage_id ? navigate(`/triages/${item.active_triage_id}`) : start.mutate(item.tracking_code)}>{item.active_triage_id ? "Continuar" : "Iniciar"}</Button></TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}
    </Box>
  );
}
