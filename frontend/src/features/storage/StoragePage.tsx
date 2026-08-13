import AddLocationAltOutlinedIcon from "@mui/icons-material/AddLocationAltOutlined";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import MoveDownOutlinedIcon from "@mui/icons-material/MoveDownOutlined";
import WarningAmberOutlinedIcon from "@mui/icons-material/WarningAmberOutlined";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControlLabel,
  Grid,
  IconButton,
  MenuItem,
  Paper,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useMemo, useState } from "react";
import { Link as RouterLink } from "react-router-dom";

import {
  createStorageLocation,
  deleteStorageLocation,
  getEquipments,
  getStorageDashboard,
  getStorageLocations,
  getStorageMovements,
  getStorageOccupancies,
  moveEquipment,
  updateStorageLocation,
} from "../../services/api";
import type { StorageLocation, StorageLocationPayload } from "../../types/storage";
import { useAuth } from "../auth/AuthContext";

const emptyLocationForm: StorageLocationPayload = {
  code: "",
  warehouse: "",
  aisle: "",
  rack: "",
  shelf: "",
  position: "",
  capacity: 1,
  notes: "",
};

const movementLabels = {
  ENTRY: "Entrada",
  TRANSFER: "Transferência",
  EXIT: "Saída",
};

function formatDate(value: string): string {
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

export function StoragePage() {
  const { accessToken, user } = useAuth();
  const queryClient = useQueryClient();
  const canManage = Boolean(
    user?.is_superuser || user?.permissions.includes("storage:manage"),
  );
  const [includeInactive, setIncludeInactive] = useState(false);
  const [locationDialogOpen, setLocationDialogOpen] = useState(false);
  const [editingLocation, setEditingLocation] = useState<StorageLocation | null>(null);
  const [locationForm, setLocationForm] = useState<StorageLocationPayload>(emptyLocationForm);
  const [deleteTarget, setDeleteTarget] = useState<StorageLocation | null>(null);
  const [movementDialogOpen, setMovementDialogOpen] = useState(false);
  const [movementForm, setMovementForm] = useState({
    equipment_id: "",
    to_location_id: "",
    notes: "",
  });

  const dashboard = useQuery({
    queryKey: ["storage", "dashboard"],
    queryFn: () => getStorageDashboard(accessToken!),
    enabled: Boolean(accessToken),
  });
  const locations = useQuery({
    queryKey: ["storage", "locations", includeInactive],
    queryFn: () => getStorageLocations(accessToken!, includeInactive),
    enabled: Boolean(accessToken),
  });
  const occupancies = useQuery({
    queryKey: ["storage", "occupancies"],
    queryFn: () => getStorageOccupancies(accessToken!),
    enabled: Boolean(accessToken),
  });
  const movements = useQuery({
    queryKey: ["storage", "movements"],
    queryFn: () => getStorageMovements(accessToken!),
    enabled: Boolean(accessToken),
  });
  const equipments = useQuery({
    queryKey: ["equipments", "storage-selector"],
    queryFn: () => getEquipments(accessToken!, { limit: 200 }),
    enabled: Boolean(accessToken) && movementDialogOpen,
  });

  const occupancyByEquipment = useMemo(
    () => new Map(occupancies.data?.map((item) => [item.equipment_id, item]) ?? []),
    [occupancies.data],
  );
  const selectedOccupancy = occupancyByEquipment.get(movementForm.equipment_id);

  async function refreshStorage() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["storage"] }),
      queryClient.invalidateQueries({ queryKey: ["equipments"] }),
      queryClient.invalidateQueries({ queryKey: ["traceability"] }),
    ]);
  }

  const saveLocation = useMutation({
    mutationFn: (payload: StorageLocationPayload) =>
      editingLocation
        ? updateStorageLocation(accessToken!, editingLocation.id, payload)
        : createStorageLocation(accessToken!, payload),
    onSuccess: async () => {
      setLocationDialogOpen(false);
      await refreshStorage();
    },
  });
  const removeLocation = useMutation({
    mutationFn: (locationId: string) => deleteStorageLocation(accessToken!, locationId),
    onSuccess: async () => {
      setDeleteTarget(null);
      await refreshStorage();
    },
  });
  const saveMovement = useMutation({
    mutationFn: () =>
      moveEquipment(accessToken!, {
        equipment_id: movementForm.equipment_id,
        to_location_id: movementForm.to_location_id || null,
        notes: movementForm.notes.trim() || undefined,
      }),
    onSuccess: async () => {
      setMovementDialogOpen(false);
      await refreshStorage();
    },
  });

  function openNewLocation() {
    setEditingLocation(null);
    setLocationForm(emptyLocationForm);
    saveLocation.reset();
    setLocationDialogOpen(true);
  }

  function openEditLocation(location: StorageLocation) {
    setEditingLocation(location);
    setLocationForm({
      code: location.code,
      warehouse: location.warehouse,
      aisle: location.aisle ?? "",
      rack: location.rack ?? "",
      shelf: location.shelf ?? "",
      position: location.position ?? "",
      capacity: location.capacity,
      notes: location.notes ?? "",
    });
    saveLocation.reset();
    setLocationDialogOpen(true);
  }

  function openMovement(equipmentId = "") {
    setMovementForm({ equipment_id: equipmentId, to_location_id: "", notes: "" });
    saveMovement.reset();
    setMovementDialogOpen(true);
  }

  function submitLocation(event: FormEvent) {
    event.preventDefault();
    saveLocation.mutate({
      ...locationForm,
      code: locationForm.code.trim().toUpperCase(),
      warehouse: locationForm.warehouse.trim(),
    });
  }

  const loading = dashboard.isLoading || locations.isLoading || occupancies.isLoading;
  const queryError = dashboard.error ?? locations.error ?? occupancies.error ?? movements.error;

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Stack spacing={3}>
        <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" gap={2}>
          <Box>
            <Typography component="h1" variant="h4">Armazenamento temporário</Typography>
            <Typography color="text.secondary">
              Controle posições, capacidade, permanência e movimentações físicas.
            </Typography>
          </Box>
          {canManage && (
            <Stack direction="row" spacing={1}>
              <Button variant="outlined" startIcon={<AddLocationAltOutlinedIcon />} onClick={openNewLocation}>
                Nova posição
              </Button>
              <Button variant="contained" startIcon={<MoveDownOutlinedIcon />} onClick={() => openMovement()}>
                Movimentar equipamento
              </Button>
            </Stack>
          )}
        </Stack>

        {queryError && <Alert severity="error">{queryError instanceof Error ? queryError.message : "Falha ao carregar o armazenamento."}</Alert>}
        {loading && <CircularProgress aria-label="Carregando armazenamento" />}

        {dashboard.data && (
          <Paper variant="outlined">
            <Grid container>
              {[
                ["Posições ativas", dashboard.data.locations_active],
                ["Capacidade total", dashboard.data.capacity_total],
                ["Itens armazenados", dashboard.data.occupied_total],
                ["Vagas disponíveis", dashboard.data.available_total],
                ["Alertas de permanência", dashboard.data.dwell_alerts],
              ].map(([label, value], index) => (
                <Grid key={label} size={{ xs: 6, md: 2.4 }} sx={{ p: 2.25, borderRight: { md: index < 4 ? "1px solid" : 0 }, borderBottom: { xs: "1px solid", md: 0 }, borderColor: "divider" }}>
                  <Typography variant="overline" color="text.secondary">{label}</Typography>
                  <Typography variant="h4" mt={0.5}>{value}</Typography>
                </Grid>
              ))}
            </Grid>
          </Paper>
        )}

        <Paper variant="outlined">
          <Stack direction={{ xs: "column", sm: "row" }} justifyContent="space-between" alignItems={{ sm: "center" }} px={2.5} py={2} gap={1}>
            <Box>
              <Typography variant="h6">Mapa de posições</Typography>
              <Typography variant="body2" color="text.secondary">Depósitos, estantes, prateleiras e posições cadastradas.</Typography>
            </Box>
            <FormControlLabel control={<Switch checked={includeInactive} onChange={(event) => setIncludeInactive(event.target.checked)} />} label="Mostrar excluídas" />
          </Stack>
          <Divider />
          <TableContainer>
            <Table size="small">
              <TableHead><TableRow>
                <TableCell>Código</TableCell><TableCell>Depósito</TableCell><TableCell>Endereço físico</TableCell><TableCell>Ocupação</TableCell><TableCell>Situação</TableCell>{canManage && <TableCell align="right">Ações</TableCell>}
              </TableRow></TableHead>
              <TableBody>
                {locations.data?.map((location) => (
                  <TableRow key={location.id} hover>
                    <TableCell><Typography fontFamily="monospace" fontWeight={700}>{location.code}</Typography></TableCell>
                    <TableCell>{location.warehouse}</TableCell>
                    <TableCell>{[location.aisle && `Corredor ${location.aisle}`, location.rack && `Estante ${location.rack}`, location.shelf && `Prateleira ${location.shelf}`, location.position && `Posição ${location.position}`].filter(Boolean).join(" · ") || "—"}</TableCell>
                    <TableCell>{location.occupied} / {location.capacity}</TableCell>
                    <TableCell><Chip size="small" color={location.is_active ? (location.available ? "success" : "warning") : "default"} label={location.is_active ? (location.available ? "Disponível" : "Lotada") : "Excluída"} /></TableCell>
                    {canManage && <TableCell align="right">
                      <IconButton aria-label={`Editar ${location.code}`} size="small" onClick={() => openEditLocation(location)}><EditOutlinedIcon fontSize="small" /></IconButton>
                      <IconButton aria-label={`Excluir ${location.code}`} size="small" color="error" disabled={!location.is_active} onClick={() => { removeLocation.reset(); setDeleteTarget(location); }}><DeleteOutlineIcon fontSize="small" /></IconButton>
                    </TableCell>}
                  </TableRow>
                ))}
                {locations.data?.length === 0 && <TableRow><TableCell colSpan={6} align="center">Nenhuma posição cadastrada.</TableCell></TableRow>}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        <Paper variant="outlined">
          <Box px={2.5} py={2}>
            <Typography variant="h6">Ocupação atual</Typography>
            <Typography variant="body2" color="text.secondary">Alertas indicam permanência igual ou superior a 30 dias.</Typography>
          </Box>
          <Divider />
          <TableContainer>
            <Table size="small">
              <TableHead><TableRow><TableCell>Equipamento</TableCell><TableCell>Posição</TableCell><TableCell>Entrada</TableCell><TableCell>Permanência</TableCell>{canManage && <TableCell align="right">Ação</TableCell>}</TableRow></TableHead>
              <TableBody>
                {occupancies.data?.map((item) => (
                  <TableRow key={item.assignment_id} hover>
                    <TableCell><Button component={RouterLink} to={`/equipment/${item.tracking_code}`} size="small">{item.tracking_code}</Button><Typography variant="body2" color="text.secondary">{item.equipment_description}</Typography></TableCell>
                    <TableCell>{item.location.code}</TableCell>
                    <TableCell>{formatDate(item.entered_at)}</TableCell>
                    <TableCell><Stack direction="row" alignItems="center" spacing={0.75}>{item.alert && <WarningAmberOutlinedIcon color="warning" fontSize="small" />}<span>{item.dwell_days} dia(s)</span></Stack></TableCell>
                    {canManage && <TableCell align="right"><Button size="small" startIcon={<MoveDownOutlinedIcon />} onClick={() => openMovement(item.equipment_id)}>Transferir ou retirar</Button></TableCell>}
                  </TableRow>
                ))}
                {occupancies.data?.length === 0 && <TableRow><TableCell colSpan={5} align="center">Nenhum equipamento armazenado.</TableCell></TableRow>}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>

        <Paper variant="outlined">
          <Box px={2.5} py={2}><Typography variant="h6">Movimentações recentes</Typography></Box>
          <Divider />
          <TableContainer><Table size="small"><TableHead><TableRow><TableCell>Data</TableCell><TableCell>Equipamento</TableCell><TableCell>Operação</TableCell><TableCell>Origem</TableCell><TableCell>Destino</TableCell><TableCell>Observação</TableCell></TableRow></TableHead><TableBody>
            {movements.data?.map((item) => <TableRow key={item.id}><TableCell>{formatDate(item.occurred_at)}</TableCell><TableCell>{item.tracking_code}</TableCell><TableCell>{movementLabels[item.movement_type]}</TableCell><TableCell>{item.from_location_code ?? "—"}</TableCell><TableCell>{item.to_location_code ?? "—"}</TableCell><TableCell>{item.notes ?? "—"}</TableCell></TableRow>)}
            {movements.data?.length === 0 && <TableRow><TableCell colSpan={6} align="center">Nenhuma movimentação registrada.</TableCell></TableRow>}
          </TableBody></Table></TableContainer>
        </Paper>
      </Stack>

      <Dialog open={locationDialogOpen} onClose={() => setLocationDialogOpen(false)} fullWidth maxWidth="md">
        <Box component="form" onSubmit={submitLocation}>
          <DialogTitle>{editingLocation ? "Editar posição" : "Adicionar posição"}</DialogTitle>
          <DialogContent dividers>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 4 }}><TextField fullWidth required label="Código" disabled={Boolean(editingLocation)} value={locationForm.code} onChange={(event) => setLocationForm({ ...locationForm, code: event.target.value })} /></Grid>
              <Grid size={{ xs: 12, md: 8 }}><TextField fullWidth required label="Depósito" value={locationForm.warehouse} onChange={(event) => setLocationForm({ ...locationForm, warehouse: event.target.value })} /></Grid>
              <Grid size={{ xs: 6, md: 3 }}><TextField fullWidth label="Corredor" value={locationForm.aisle} onChange={(event) => setLocationForm({ ...locationForm, aisle: event.target.value })} /></Grid>
              <Grid size={{ xs: 6, md: 3 }}><TextField fullWidth label="Estante" value={locationForm.rack} onChange={(event) => setLocationForm({ ...locationForm, rack: event.target.value })} /></Grid>
              <Grid size={{ xs: 6, md: 3 }}><TextField fullWidth label="Prateleira" value={locationForm.shelf} onChange={(event) => setLocationForm({ ...locationForm, shelf: event.target.value })} /></Grid>
              <Grid size={{ xs: 6, md: 3 }}><TextField fullWidth label="Posição" value={locationForm.position} onChange={(event) => setLocationForm({ ...locationForm, position: event.target.value })} /></Grid>
              <Grid size={{ xs: 12, md: 3 }}><TextField fullWidth required type="number" label="Capacidade" value={locationForm.capacity} onChange={(event) => setLocationForm({ ...locationForm, capacity: Number(event.target.value) })} slotProps={{ htmlInput: { min: 1 } }} /></Grid>
              <Grid size={{ xs: 12, md: 9 }}><TextField fullWidth label="Observações" value={locationForm.notes} onChange={(event) => setLocationForm({ ...locationForm, notes: event.target.value })} /></Grid>
            </Grid>
            {saveLocation.isError && <Alert severity="error" sx={{ mt: 2 }}>{saveLocation.error instanceof Error ? saveLocation.error.message : "Falha ao salvar."}</Alert>}
          </DialogContent>
          <DialogActions><Button onClick={() => setLocationDialogOpen(false)}>Cancelar</Button><Button type="submit" variant="contained" disabled={saveLocation.isPending}>{saveLocation.isPending ? "Salvando..." : "Salvar posição"}</Button></DialogActions>
        </Box>
      </Dialog>

      <Dialog open={movementDialogOpen} onClose={() => setMovementDialogOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Movimentar equipamento</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={2}>
            <TextField select fullWidth required label="Equipamento" value={movementForm.equipment_id} onChange={(event) => setMovementForm({ ...movementForm, equipment_id: event.target.value, to_location_id: "" })}>
              {equipments.data?.items.map((item) => <MenuItem key={item.id} value={item.id}>{item.tracking_code} — {item.brand} {item.model}</MenuItem>)}
            </TextField>
            {selectedOccupancy && <Alert severity="info">Posição atual: <strong>{selectedOccupancy.location.code}</strong>. Selecione uma nova posição para transferir ou “Saída” para retirar.</Alert>}
            <TextField select fullWidth required={Boolean(!selectedOccupancy)} label="Destino" value={movementForm.to_location_id} onChange={(event) => setMovementForm({ ...movementForm, to_location_id: event.target.value })}>
              {selectedOccupancy && <MenuItem value="">Saída do armazenamento</MenuItem>}
              {locations.data?.filter((item) => item.is_active && item.available > 0 && item.id !== selectedOccupancy?.location.id).map((item) => <MenuItem key={item.id} value={item.id}>{item.code} — {item.warehouse} ({item.available} vaga(s))</MenuItem>)}
            </TextField>
            <TextField fullWidth multiline minRows={2} label="Observação" value={movementForm.notes} onChange={(event) => setMovementForm({ ...movementForm, notes: event.target.value })} />
            {saveMovement.isError && <Alert severity="error">{saveMovement.error instanceof Error ? saveMovement.error.message : "Falha ao movimentar."}</Alert>}
          </Stack>
        </DialogContent>
        <DialogActions><Button onClick={() => setMovementDialogOpen(false)}>Cancelar</Button><Button variant="contained" disabled={saveMovement.isPending || !movementForm.equipment_id || (!selectedOccupancy && !movementForm.to_location_id)} onClick={() => saveMovement.mutate()}>{saveMovement.isPending ? "Registrando..." : selectedOccupancy ? (movementForm.to_location_id ? "Transferir" : "Registrar saída") : "Registrar entrada"}</Button></DialogActions>
      </Dialog>

      <Dialog open={Boolean(deleteTarget)} onClose={() => setDeleteTarget(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Excluir posição?</DialogTitle>
        <DialogContent dividers><Typography>A posição <strong>{deleteTarget?.code}</strong> deixará de aparecer nas opções de movimentação. O histórico será preservado.</Typography>{removeLocation.isError && <Alert severity="error" sx={{ mt: 2 }}>{removeLocation.error instanceof Error ? removeLocation.error.message : "Falha ao excluir."}</Alert>}</DialogContent>
        <DialogActions><Button onClick={() => setDeleteTarget(null)}>Cancelar</Button><Button color="error" variant="contained" disabled={removeLocation.isPending} onClick={() => deleteTarget && removeLocation.mutate(deleteTarget.id)}>Excluir posição</Button></DialogActions>
      </Dialog>
    </Container>
  );
}
