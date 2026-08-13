import ArrowBackOutlinedIcon from "@mui/icons-material/ArrowBackOutlined";
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import EditNoteOutlinedIcon from "@mui/icons-material/EditNoteOutlined";
import SwapHorizOutlinedIcon from "@mui/icons-material/SwapHorizOutlined";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  Grid,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link as RouterLink, useNavigate, useParams } from "react-router-dom";

import {
  addTimelineNote,
  deleteEquipment,
  getEquipmentByCode,
  getEquipmentTimeline,
  getEquipmentTriages,
  getProtectedFile,
  getWorkflowOptions,
  transitionEquipment,
} from "../../services/api";
import { useAuth } from "../auth/AuthContext";
import { formatStatus } from "./EquipmentListPage";

const EVENT_LABELS: Record<string, string> = {
  COLLECTED: "Recolhimento",
  EQUIPMENT_REGISTERED: "Cadastro",
  QUEUED_FOR_TRIAGE: "Fila de triagem",
  TRIAGE_STARTED: "Triagem iniciada",
  TRIAGE_COMPLETED: "Triagem concluída",
  TRIAGE_CANCELLED: "Triagem cancelada",
  CLASSIFIED: "Classificação",
  STATUS_CHANGED: "Mudança de status",
  OPERATIONAL_NOTE: "Nota operacional",
  STORAGE_ENTRY: "Entrada no armazenamento",
  STORAGE_TRANSFER: "Transferência de posição",
  STORAGE_EXIT: "Saída do armazenamento",
  EQUIPMENT_ARCHIVED: "Exclusão do inventário",
};

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(new Date(value));
}

export function EquipmentDetailPage() {
  const { trackingCode = "" } = useParams();
  const navigate = useNavigate();
  const { accessToken, user } = useAuth();
  const queryClient = useQueryClient();
  const [qrUrl, setQrUrl] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [transitionOpen, setTransitionOpen] = useState(false);
  const [noteOpen, setNoteOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteReason, setDeleteReason] = useState("");
  const [transition, setTransition] = useState({ new_status: "", description: "", location: "" });
  const [note, setNote] = useState({ description: "", location: "" });
  const canTransition = Boolean(user?.is_superuser || user?.permissions.includes("workflow:transition"));
  const canUpdate = Boolean(user?.is_superuser || user?.permissions.includes("equipment:update"));
  const canDelete = Boolean(user?.is_superuser || user?.permissions.includes("equipment:delete"));
  const equipment = useQuery({ queryKey: ["equipment", trackingCode], queryFn: () => getEquipmentByCode(accessToken!, trackingCode), enabled: Boolean(accessToken && trackingCode) });
  const timeline = useQuery({ queryKey: ["equipment", equipment.data?.id, "timeline"], queryFn: () => getEquipmentTimeline(accessToken!, equipment.data!.id), enabled: Boolean(accessToken && equipment.data?.id) });
  const triages = useQuery({ queryKey: ["equipment", trackingCode, "triages"], queryFn: () => getEquipmentTriages(accessToken!, trackingCode), enabled: Boolean(accessToken && trackingCode) });
  const options = useQuery({ queryKey: ["equipment", equipment.data?.id, "workflow-options"], queryFn: () => getWorkflowOptions(accessToken!, equipment.data!.id), enabled: Boolean(accessToken && equipment.data?.id) });

  const refreshHistory = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["equipment", trackingCode] }),
      queryClient.invalidateQueries({ queryKey: ["equipment", equipment.data?.id, "timeline"] }),
      queryClient.invalidateQueries({ queryKey: ["equipment", equipment.data?.id, "workflow-options"] }),
      queryClient.invalidateQueries({ queryKey: ["traceability"] }),
      queryClient.invalidateQueries({ queryKey: ["equipments"] }),
    ]);
  };
  const move = useMutation({
    mutationFn: () => transitionEquipment(accessToken!, equipment.data!.id, transition),
    onSuccess: async () => { setTransitionOpen(false); setTransition({ new_status: "", description: "", location: "" }); await refreshHistory(); },
  });
  const addNote = useMutation({
    mutationFn: () => addTimelineNote(accessToken!, equipment.data!.id, note),
    onSuccess: async () => { setNoteOpen(false); setNote({ description: "", location: "" }); await refreshHistory(); },
  });
  const removeEquipment = useMutation({
    mutationFn: () => deleteEquipment(accessToken!, equipment.data!.id, deleteReason.trim()),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["equipments"] });
      navigate("/equipments");
    },
  });

  useEffect(() => {
    if (!accessToken || !equipment.data?.id) return undefined;
    let objectUrl: string | null = null;
    getProtectedFile(accessToken, `/equipments/${equipment.data.id}/qr-code`).then((blob) => { objectUrl = URL.createObjectURL(blob); setQrUrl(objectUrl); }).catch(() => setQrUrl(null));
    return () => { if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [accessToken, equipment.data?.id]);

  async function downloadLabel() {
    if (!accessToken || !equipment.data) return;
    setDownloadError(null);
    try {
      const blob = await getProtectedFile(accessToken, `/equipments/${equipment.data.id}/label`);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `etiqueta-${equipment.data.tracking_code}.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) { setDownloadError(error instanceof Error ? error.message : "Falha ao gerar etiqueta"); }
  }

  if (equipment.isLoading) return <Box py={8} textAlign="center"><CircularProgress /></Box>;
  if (equipment.isError || !equipment.data) return <Box p={4}><Alert severity="error">Equipamento não encontrado ou indisponível.</Alert></Box>;
  const item = equipment.data;
  const actionError = move.error ?? addNote.error;

  return (
    <Box sx={{ px: { xs: 2, md: 4 }, py: 3, maxWidth: 1500, mx: "auto" }}>
      <Button component={RouterLink} to="/equipments" startIcon={<ArrowBackOutlinedIcon />} size="small" sx={{ mb: 2 }}>Voltar ao inventário</Button>
      <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" alignItems={{ md: "start" }} gap={2} mb={3}>
        <Box>
          <Typography variant="overline" color="text.secondary">FICHA PATRIMONIAL</Typography>
          <Typography component="h1" variant="h3" fontFamily="monospace">{item.tracking_code}</Typography>
          <Typography color="text.secondary" mt={0.5}>{item.equipment_type.name} · {item.brand} {item.model}</Typography>
        </Box>
        <Stack direction="row" gap={1} flexWrap="wrap">
          <Chip label={formatStatus(item.current_status)} color="primary" />
          {canUpdate && <Button component={RouterLink} to={`/equipment/${item.tracking_code}/edit`} variant="outlined" startIcon={<EditOutlinedIcon />}>Editar</Button>}
          {canDelete && <Button color="error" variant="outlined" startIcon={<DeleteOutlineIcon />} onClick={() => setDeleteOpen(true)}>Excluir</Button>}
          {canTransition && <Button variant="outlined" startIcon={<EditNoteOutlinedIcon />} onClick={() => setNoteOpen(true)}>Registrar nota</Button>}
          {canTransition && options.data && options.data.length > 0 && <Button variant="contained" startIcon={<SwapHorizOutlinedIcon />} onClick={() => setTransitionOpen(true)}>Atualizar etapa</Button>}
        </Stack>
      </Stack>
      {downloadError && <Alert severity="error" sx={{ mb: 2 }}>{downloadError}</Alert>}
      {actionError && <Alert severity="error" sx={{ mb: 2 }}>{(actionError as Error).message}</Alert>}

      <Grid container spacing={2.5}>
        <Grid size={{ xs: 12, lg: 8 }}>
          <Stack gap={2.5}>
            <Paper variant="outlined">
              <Box px={2.5} py={1.75}><Typography fontWeight={650}>Dados de identificação</Typography></Box><Divider />
              <Grid container>
                {[
                  ["Patrimônio", item.asset_number ?? "Não informado"], ["Número de série", item.serial_number ?? "Não informado"],
                  ["Categoria", item.category.name], ["Setor de origem", item.origin_sector.name],
                  ["Data de recolhimento", formatDate(item.collection_date)], ["Condição inicial", item.initial_condition],
                ].map(([label, value], index) => (
                  <Grid key={String(label)} size={{ xs: 12, sm: 6 }} sx={{ borderRight: { sm: index % 2 === 0 ? "1px solid" : 0 }, borderBottom: "1px solid", borderColor: "divider" }}>
                    <Box px={2.5} py={1.75}><Typography variant="caption" color="text.secondary">{label.toUpperCase()}</Typography><Typography mt={0.4}>{value}</Typography></Box>
                  </Grid>
                ))}
              </Grid>
              {(item.description || item.collection_notes) && <Box p={2.5}><Typography variant="caption" color="text.secondary">OBSERVAÇÕES DE ENTRADA</Typography><Typography mt={0.5}>{item.description}</Typography>{item.collection_notes && <Typography mt={0.5} color="text.secondary">{item.collection_notes}</Typography>}</Box>}
            </Paper>

            <Paper variant="outlined">
              <Box px={2.5} py={1.75}><Typography fontWeight={650}>Avaliações técnicas</Typography></Box><Divider />
              {triages.isLoading && <CircularProgress size={24} sx={{ m: 2.5 }} />}
              {triages.data?.length === 0 && <Typography color="text.secondary" p={2.5}>Nenhuma triagem registrada.</Typography>}
              <Stack divider={<Divider flexItem />}>
                {triages.data?.map((triage) => (
                  <Box key={triage.id} p={2.5}>
                    <Stack direction={{ xs: "column", sm: "row" }} justifyContent="space-between" gap={1}>
                      <Box><Typography fontWeight={650}>{triage.classification?.name ?? "Triagem em andamento"}</Typography><Typography variant="caption" color="text.secondary">{triage.evaluator_name} · {formatDate(triage.started_at)} · {triage.answers.length} critérios</Typography></Box>
                      <Chip size="small" variant="outlined" color={triage.status === "COMPLETED" ? "success" : "warning"} label={triage.status === "COMPLETED" ? "Concluída" : triage.status === "CANCELLED" ? "Cancelada" : "Em andamento"} />
                    </Stack>
                    {triage.technical_opinion && <Typography mt={1.25}>{triage.technical_opinion}</Typography>}
                  </Box>
                ))}
              </Stack>
            </Paper>
          </Stack>
        </Grid>

        <Grid size={{ xs: 12, lg: 4 }}>
          <Stack gap={2.5}>
            <Paper variant="outlined">
              <Box px={2.5} py={1.75}><Typography fontWeight={650}>Identificação física</Typography></Box><Divider />
              <Box p={2.5} textAlign="center">
                {qrUrl ? <Box component="img" src={qrUrl} alt={`QR Code de ${item.tracking_code}`} sx={{ width: 190, maxWidth: "100%", imageRendering: "pixelated" }} /> : <CircularProgress size={28} sx={{ my: 5 }} />}
                <Button fullWidth variant="outlined" startIcon={<DownloadOutlinedIcon />} onClick={() => void downloadLabel()} sx={{ mt: 1.5 }}>Baixar etiqueta PDF</Button>
              </Box>
            </Paper>
            <Paper variant="outlined">
              <Box px={2.5} py={1.75}><Typography fontWeight={650}>Linha do tempo</Typography><Typography variant="caption" color="text.secondary">{timeline.data?.length ?? 0} registros preservados</Typography></Box><Divider />
              {timeline.isLoading && <CircularProgress size={24} sx={{ m: 2.5 }} />}
              <Box px={2.5} py={1}>
                {timeline.data?.slice().reverse().map((event, index) => (
                  <Box key={event.id} display="grid" gridTemplateColumns="16px 1fr" gap={1.5}>
                    <Stack alignItems="center">
                      <Box width={9} height={9} borderRadius="50%" bgcolor={index === 0 ? "secondary.main" : "primary.main"} mt={1.1} />
                      {index < (timeline.data?.length ?? 0) - 1 && <Box width="1px" bgcolor="divider" flexGrow={1} />}
                    </Stack>
                    <Box pb={2.25}>
                      <Typography variant="caption" color="text.secondary">{formatDate(event.timestamp)} · {EVENT_LABELS[event.event_type] ?? event.event_type}</Typography>
                      <Typography variant="body2" mt={0.35}>{event.description}</Typography>
                      {(event.location || event.new_status) && <Typography variant="caption" color="text.secondary">{event.location ?? formatStatus(event.new_status ?? "")}</Typography>}
                    </Box>
                  </Box>
                ))}
              </Box>
            </Paper>
          </Stack>
        </Grid>
      </Grid>

      <Dialog open={transitionOpen} onClose={() => setTransitionOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Atualizar etapa do ciclo</DialogTitle>
        <DialogContent><Stack gap={2} mt={1}>
          <Alert severity="info" icon={false}>Situação atual: <strong>{formatStatus(item.current_status)}</strong>. Somente etapas compatíveis são exibidas.</Alert>
          <TextField select label="Próxima etapa" value={transition.new_status} onChange={(event) => setTransition({ ...transition, new_status: event.target.value })} required>{options.data?.map((option) => <MenuItem key={option.code} value={option.code}>{option.label} · {option.stage}</MenuItem>)}</TextField>
          <TextField label="Justificativa / descrição" multiline minRows={3} value={transition.description} onChange={(event) => setTransition({ ...transition, description: event.target.value })} required helperText="Este texto será preservado no histórico." />
          <TextField label="Local (opcional)" value={transition.location} onChange={(event) => setTransition({ ...transition, location: event.target.value })} />
        </Stack></DialogContent>
        <DialogActions><Button onClick={() => setTransitionOpen(false)}>Cancelar</Button><Button variant="contained" disabled={!transition.new_status || transition.description.trim().length < 5 || move.isPending} onClick={() => move.mutate()}>Confirmar mudança</Button></DialogActions>
      </Dialog>
      <Dialog open={noteOpen} onClose={() => setNoteOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Registrar nota operacional</DialogTitle>
        <DialogContent><Stack gap={2} mt={1}><TextField label="Descrição do registro" multiline minRows={4} value={note.description} onChange={(event) => setNote({ ...note, description: event.target.value })} required helperText="A nota não altera a situação atual do equipamento." /><TextField label="Local (opcional)" value={note.location} onChange={(event) => setNote({ ...note, location: event.target.value })} /></Stack></DialogContent>
        <DialogActions><Button onClick={() => setNoteOpen(false)}>Cancelar</Button><Button variant="contained" disabled={note.description.trim().length < 5 || addNote.isPending} onClick={() => addNote.mutate()}>Registrar nota</Button></DialogActions>
      </Dialog>
      <Dialog open={deleteOpen} onClose={() => setDeleteOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Excluir equipamento do inventário?</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={2}>
            <Alert severity="warning">A ficha deixará o inventário ativo, mas eventos, triagens e auditoria serão preservados.</Alert>
            <TextField fullWidth required multiline minRows={2} label="Motivo da exclusão" value={deleteReason} onChange={(event) => setDeleteReason(event.target.value)} />
            {removeEquipment.isError && <Alert severity="error">{removeEquipment.error instanceof Error ? removeEquipment.error.message : "Falha ao excluir."}</Alert>}
          </Stack>
        </DialogContent>
        <DialogActions><Button onClick={() => setDeleteOpen(false)}>Cancelar</Button><Button color="error" variant="contained" disabled={deleteReason.trim().length < 5 || removeEquipment.isPending} onClick={() => removeEquipment.mutate()}>{removeEquipment.isPending ? "Excluindo..." : "Excluir equipamento"}</Button></DialogActions>
      </Dialog>
    </Box>
  );
}
