import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import SearchIcon from "@mui/icons-material/Search";
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
  IconButton,
  InputAdornment,
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
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useState } from "react";
import { Link as RouterLink } from "react-router-dom";

import { deleteEquipment, getEquipments } from "../../services/api";
import type { Equipment } from "../../types/equipment";
import { useAuth } from "../auth/AuthContext";

const pageSize = 20;

const STATUS_LABELS: Record<string, string> = {
  RECOLHIDO: "Recolhido",
  CADASTRADO: "Cadastrado",
  AGUARDANDO_TRIAGEM: "Aguardando triagem",
  EM_TRIAGEM: "Em triagem",
  AGUARDANDO_AVALIACAO: "Aguardando avaliação",
  AGUARDANDO_DESTINACAO: "Aguardando destinação",
  ARMAZENADO: "Armazenado",
  SEPARADO_REUTILIZACAO: "Separado para reutilização",
  PREPARANDO_REINTRODUCAO: "Preparando reintrodução",
  REINTRODUZIDO: "Reintroduzido",
  SEPARADO_LEILAO: "Separado para leilão",
  EM_LEILAO: "Em leilão",
  LEILOADO: "Leiloado",
  AGUARDANDO_RECICLAGEM: "Aguardando reciclagem",
  ENVIADO_RECICLAGEM: "Enviado para reciclagem",
  RECICLADO: "Reciclado",
  DESCARTADO: "Descartado",
  FINALIZADO: "Finalizado",
};

export function formatStatus(status: string): string {
  return STATUS_LABELS[status] ?? status.replaceAll("_", " ");
}

export function EquipmentListPage() {
  const { accessToken, user } = useAuth();
  const queryClient = useQueryClient();
  const [searchInput, setSearchInput] = useState("");
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [deleteTarget, setDeleteTarget] = useState<Equipment | null>(null);
  const [deleteReason, setDeleteReason] = useState("");
  const canCreate = user?.is_superuser || user?.permissions.includes("equipment:create");
  const canUpdate = user?.is_superuser || user?.permissions.includes("equipment:update");
  const canDelete = user?.is_superuser || user?.permissions.includes("equipment:delete");
  const equipments = useQuery({
    queryKey: ["equipments", query, offset],
    queryFn: () => getEquipments(accessToken!, { query, limit: pageSize, offset }),
    enabled: Boolean(accessToken),
  });
  const deleteMutation = useMutation({
    mutationFn: () => deleteEquipment(accessToken!, deleteTarget!.id, deleteReason.trim()),
    onSuccess: async () => {
      setDeleteTarget(null);
      setDeleteReason("");
      await queryClient.invalidateQueries({ queryKey: ["equipments"] });
    },
  });

  function handleSearch(event: FormEvent) {
    event.preventDefault();
    setOffset(0);
    setQuery(searchInput.trim());
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Stack spacing={3}>
        <Stack direction={{ xs: "column", sm: "row" }} justifyContent="space-between" gap={2}>
          <Box>
            <Typography component="h1" variant="h4">Equipamentos</Typography>
            <Typography color="text.secondary">
              Consulte pelo código REEE, patrimônio, série, marca ou modelo.
            </Typography>
          </Box>
          {canCreate && (
            <Button component={RouterLink} to="/equipments/new" variant="contained" startIcon={<AddIcon />}>
              Nova entrada
            </Button>
          )}
        </Stack>

        <Paper component="form" variant="outlined" sx={{ p: 2 }} onSubmit={handleSearch}>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <TextField
              fullWidth
              label="Buscar equipamentos"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              slotProps={{
                input: {
                  startAdornment: (
                    <InputAdornment position="start"><SearchIcon /></InputAdornment>
                  ),
                },
              }}
            />
            <Button type="submit" variant="contained">Buscar</Button>
          </Stack>
        </Paper>

        {equipments.isError && (
          <Alert severity="error">
            {equipments.error instanceof Error ? equipments.error.message : "Falha na consulta"}
          </Alert>
        )}
        {equipments.isLoading && <CircularProgress aria-label="Carregando equipamentos" />}
        {equipments.data && (
          <>
            <Typography color="text.secondary">
              {equipments.data.total} registro(s) encontrado(s)
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Código</TableCell>
                    <TableCell>Equipamento</TableCell>
                    <TableCell>Patrimônio</TableCell>
                    <TableCell>Setor</TableCell>
                    <TableCell>Status</TableCell>
                    {(canUpdate || canDelete) && <TableCell align="right">Ações</TableCell>}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {equipments.data.items.map((equipment) => (
                    <TableRow hover key={equipment.id}>
                      <TableCell>
                        <Button
                          component={RouterLink}
                          to={`/equipment/${equipment.tracking_code}`}
                          size="small"
                        >
                          {equipment.tracking_code}
                        </Button>
                      </TableCell>
                      <TableCell>
                        <Typography fontWeight={500}>{equipment.equipment_type.name}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {equipment.brand} {equipment.model}
                        </Typography>
                      </TableCell>
                      <TableCell>{equipment.asset_number ?? "—"}</TableCell>
                      <TableCell>{equipment.origin_sector.name}</TableCell>
                      <TableCell><Chip size="small" label={formatStatus(equipment.current_status)} /></TableCell>
                      {(canUpdate || canDelete) && (
                        <TableCell align="right">
                          {canUpdate && (
                            <IconButton
                              component={RouterLink}
                              to={`/equipment/${equipment.tracking_code}/edit`}
                              size="small"
                              aria-label={`Editar ${equipment.tracking_code}`}
                            >
                              <EditOutlinedIcon fontSize="small" />
                            </IconButton>
                          )}
                          {canDelete && (
                            <IconButton
                              size="small"
                              color="error"
                              aria-label={`Excluir ${equipment.tracking_code}`}
                              onClick={() => {
                                deleteMutation.reset();
                                setDeleteTarget(equipment);
                              }}
                            >
                              <DeleteOutlineIcon fontSize="small" />
                            </IconButton>
                          )}
                        </TableCell>
                      )}
                    </TableRow>
                  ))}
                  {equipments.data.items.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={canUpdate || canDelete ? 6 : 5} align="center">Nenhum equipamento encontrado.</TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </TableContainer>
            <Stack direction="row" justifyContent="flex-end" spacing={1}>
              <Button disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - pageSize))}>
                Anterior
              </Button>
              <Button
                disabled={offset + pageSize >= equipments.data.total}
                onClick={() => setOffset(offset + pageSize)}
              >
                Próxima
              </Button>
            </Stack>
          </>
        )}
      </Stack>
      <Dialog open={Boolean(deleteTarget)} onClose={() => setDeleteTarget(null)} fullWidth maxWidth="sm">
        <DialogTitle>Excluir equipamento do inventário?</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={2}>
            <Alert severity="warning">
              O registro {deleteTarget?.tracking_code} será retirado das consultas ativas, mas sua linha do tempo e auditoria serão preservadas.
            </Alert>
            <TextField
              required
              fullWidth
              multiline
              minRows={2}
              label="Motivo da exclusão"
              value={deleteReason}
              onChange={(event) => setDeleteReason(event.target.value)}
            />
            {deleteMutation.isError && (
              <Alert severity="error">{deleteMutation.error instanceof Error ? deleteMutation.error.message : "Falha ao excluir."}</Alert>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Cancelar</Button>
          <Button
            color="error"
            variant="contained"
            disabled={deleteReason.trim().length < 5 || deleteMutation.isPending}
            onClick={() => deleteMutation.mutate()}
          >
            {deleteMutation.isPending ? "Excluindo..." : "Excluir equipamento"}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
}
