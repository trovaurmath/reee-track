import FilterAltOutlinedIcon from "@mui/icons-material/FilterAltOutlined";
import HistoryOutlinedIcon from "@mui/icons-material/HistoryOutlined";
import SearchOutlinedIcon from "@mui/icons-material/SearchOutlined";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  InputAdornment,
  MenuItem,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { useQuery } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";
import { Link as RouterLink } from "react-router-dom";

import { getTraceabilityFeed } from "../../services/api";
import { useAuth } from "../auth/AuthContext";

const EVENT_TYPES = [
  ["", "Todos os eventos"],
  ["STATUS_CHANGED", "Mudanças de status"],
  ["OPERATIONAL_NOTE", "Notas operacionais"],
  ["CLASSIFIED", "Classificações"],
  ["TRIAGE_STARTED", "Triagens iniciadas"],
  ["TRIAGE_COMPLETED", "Triagens concluídas"],
];

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
};

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

export function TraceabilityPage() {
  const { accessToken } = useAuth();
  const [searchInput, setSearchInput] = useState("");
  const [query, setQuery] = useState("");
  const [eventType, setEventType] = useState("");
  const [offset, setOffset] = useState(0);
  const pageSize = 30;
  const feed = useQuery({
    queryKey: ["traceability", query, eventType, offset],
    queryFn: () => getTraceabilityFeed(accessToken!, {
      query,
      eventType,
      limit: pageSize,
      offset,
    }),
    enabled: Boolean(accessToken),
  });

  function applyFilters(event: FormEvent) {
    event.preventDefault();
    setOffset(0);
    setQuery(searchInput.trim());
  }

  return (
    <Box sx={{ px: { xs: 2, md: 4 }, py: 3, maxWidth: 1500, mx: "auto" }}>
      <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" gap={2} mb={3}>
        <Box>
          <Typography variant="overline" color="text.secondary">Controle do ciclo</Typography>
          <Typography component="h1" variant="h3">Rastreabilidade</Typography>
          <Typography color="text.secondary" mt={0.75}>
            Registro cronológico consolidado de todos os equipamentos.
          </Typography>
        </Box>
        <Stack direction="row" alignItems="center" gap={1.25} color="text.secondary">
          <HistoryOutlinedIcon />
          <Box>
            <Typography variant="caption" display="block">EVENTOS LOCALIZADOS</Typography>
            <Typography variant="h5" color="text.primary">{feed.data?.total ?? "—"}</Typography>
          </Box>
        </Stack>
      </Stack>

      <Paper component="form" variant="outlined" onSubmit={applyFilters} sx={{ mb: 2 }}>
        <Stack direction={{ xs: "column", md: "row" }} gap={1.5} p={2}>
          <TextField
            fullWidth
            size="small"
            placeholder="Código REEE, patrimônio, marca, modelo ou descrição"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            slotProps={{
              input: {
                startAdornment: <InputAdornment position="start"><SearchOutlinedIcon /></InputAdornment>,
              },
            }}
          />
          <TextField
            select
            size="small"
            label="Tipo de evento"
            value={eventType}
            onChange={(event) => { setEventType(event.target.value); setOffset(0); }}
            sx={{ minWidth: 220 }}
          >
            {EVENT_TYPES.map(([value, label]) => <MenuItem key={value || "all"} value={value}>{label}</MenuItem>)}
          </TextField>
          <Button type="submit" variant="contained" startIcon={<FilterAltOutlinedIcon />}>Aplicar</Button>
        </Stack>
      </Paper>

      {feed.isLoading && <Box py={8} textAlign="center"><CircularProgress /></Box>}
      {feed.isError && <Alert severity="error">{(feed.error as Error).message}</Alert>}
      {feed.data && (
        <Paper variant="outlined">
          <Box px={2.5} py={1.75}>
            <Typography fontWeight={650}>Livro de eventos</Typography>
          </Box>
          <Divider />
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ width: 145 }}>Data e hora</TableCell>
                  <TableCell sx={{ width: 175 }}>Equipamento</TableCell>
                  <TableCell sx={{ width: 170 }}>Evento</TableCell>
                  <TableCell>Registro</TableCell>
                  <TableCell sx={{ width: 180 }}>Local / situação</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {feed.data.items.map((event) => (
                  <TableRow key={event.id} hover>
                    <TableCell sx={{ whiteSpace: "nowrap", color: "text.secondary" }}>{formatDate(event.timestamp)}</TableCell>
                    <TableCell>
                      <Button component={RouterLink} to={`/equipment/${event.tracking_code}`} size="small" sx={{ fontFamily: "monospace", px: 0 }}>
                        {event.tracking_code}
                      </Button>
                      <Typography variant="caption" color="text.secondary" display="block" noWrap maxWidth={230}>
                        {event.equipment_description}
                      </Typography>
                    </TableCell>
                    <TableCell><Chip size="small" variant="outlined" label={EVENT_LABELS[event.event_type] ?? event.event_type} /></TableCell>
                    <TableCell>{event.description}</TableCell>
                    <TableCell>
                      {event.location && <Typography variant="body2">{event.location}</Typography>}
                      {event.status_label && <Typography variant="caption" color="text.secondary">{event.status_label}</Typography>}
                    </TableCell>
                  </TableRow>
                ))}
                {feed.data.items.length === 0 && (
                  <TableRow><TableCell colSpan={5} align="center" sx={{ py: 7 }}>Nenhum evento corresponde aos filtros.</TableCell></TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
          <Divider />
          <Stack direction="row" justifyContent="space-between" alignItems="center" p={1.5}>
            <Typography variant="caption" color="text.secondary">
              Exibindo {offset + 1}–{Math.min(offset + pageSize, feed.data.total)} de {feed.data.total}
            </Typography>
            <Stack direction="row" gap={1}>
              <Button size="small" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - pageSize))}>Anterior</Button>
              <Button size="small" disabled={offset + pageSize >= feed.data.total} onClick={() => setOffset(offset + pageSize)}>Próxima</Button>
            </Stack>
          </Stack>
        </Paper>
      )}
    </Box>
  );
}
