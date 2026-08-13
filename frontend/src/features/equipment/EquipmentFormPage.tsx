import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import SaveIcon from "@mui/icons-material/Save";
import {
  Alert,
  Button,
  CircularProgress,
  Container,
  Grid,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type FormEvent, useEffect, useState } from "react";
import { Link as RouterLink, useNavigate, useParams } from "react-router-dom";

import {
  createEquipment,
  getCatalogs,
  getEquipmentByCode,
  updateEquipment,
} from "../../services/api";
import type { EquipmentCreatePayload } from "../../types/equipment";
import { useAuth } from "../auth/AuthContext";


function defaultLocalDateTime(): string {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60_000);
  return local.toISOString().slice(0, 16);
}

export function EquipmentFormPage() {
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const { trackingCode } = useParams();
  const isEditing = Boolean(trackingCode);
  const queryClient = useQueryClient();
  const catalogs = useQuery({
    queryKey: ["catalogs", "equipment"],
    queryFn: () => getCatalogs(accessToken!),
    enabled: Boolean(accessToken),
  });
  const equipment = useQuery({
    queryKey: ["equipment", trackingCode],
    queryFn: () => getEquipmentByCode(accessToken!, trackingCode!),
    enabled: Boolean(accessToken && trackingCode),
  });
  const [form, setForm] = useState({
    asset_number: "",
    serial_number: "",
    equipment_type_id: "",
    category_id: "",
    origin_sector_id: "",
    brand: "",
    model: "",
    description: "",
    initial_condition: "",
    collection_date: defaultLocalDateTime(),
    collection_notes: "",
  });

  useEffect(() => {
    if (!equipment.data) return;
    const item = equipment.data;
    const collectionDate = new Date(item.collection_date);
    const localCollectionDate = new Date(
      collectionDate.getTime() - collectionDate.getTimezoneOffset() * 60_000,
    ).toISOString().slice(0, 16);
    setForm({
      asset_number: item.asset_number ?? "",
      serial_number: item.serial_number ?? "",
      equipment_type_id: item.equipment_type.id,
      category_id: item.category.id,
      origin_sector_id: item.origin_sector.id,
      brand: item.brand,
      model: item.model,
      description: item.description ?? "",
      initial_condition: item.initial_condition,
      collection_date: localCollectionDate,
      collection_notes: item.collection_notes ?? "",
    });
  }, [equipment.data]);

  const mutation = useMutation({
    mutationFn: (payload: EquipmentCreatePayload) => {
      if (isEditing && equipment.data) {
        const { collection_date, ...updatePayload } = payload;
        void collection_date;
        return updateEquipment(accessToken!, equipment.data.id, updatePayload);
      }
      return createEquipment(accessToken!, payload);
    },
    onSuccess: async (equipment) => {
      await queryClient.invalidateQueries({ queryKey: ["equipments"] });
      navigate(`/equipment/${equipment.tracking_code}`);
    },
  });

  function setField(field: keyof typeof form, value: string) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate({
      asset_number: form.asset_number.trim() || null,
      serial_number: form.serial_number.trim() || null,
      equipment_type_id: form.equipment_type_id,
      category_id: form.category_id,
      origin_sector_id: form.origin_sector_id,
      brand: form.brand.trim(),
      model: form.model.trim(),
      description: form.description.trim() || null,
      initial_condition: form.initial_condition.trim(),
      collection_date: new Date(form.collection_date).toISOString(),
      collection_notes: form.collection_notes.trim() || null,
    });
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Stack spacing={3}>
        <Stack direction="row" spacing={2} alignItems="center">
          <Button component={RouterLink} to={trackingCode ? `/equipment/${trackingCode}` : "/equipments"} startIcon={<ArrowBackIcon />}>Voltar</Button>
          <div>
            <Typography component="h1" variant="h4">{isEditing ? "Editar equipamento" : "Nova entrada"}</Typography>
            <Typography color="text.secondary">{isEditing ? `Atualize os dados cadastrais de ${trackingCode}.` : "Cadastre o recolhimento de um equipamento."}</Typography>
          </div>
        </Stack>

        {catalogs.isLoading && <CircularProgress aria-label="Carregando catálogos" />}
        {equipment.isLoading && <CircularProgress aria-label="Carregando equipamento" />}
        {catalogs.isError && <Alert severity="error">Não foi possível carregar os catálogos.</Alert>}
        {equipment.isError && <Alert severity="error">Não foi possível carregar o equipamento.</Alert>}
        {mutation.isError && (
          <Alert severity="error">
            {mutation.error instanceof Error ? mutation.error.message : "Falha no cadastro"}
          </Alert>
        )}

        {catalogs.data && (!isEditing || equipment.data) && (
          <Paper component="form" variant="outlined" sx={{ p: { xs: 2, md: 4 } }} onSubmit={handleSubmit}>
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 4 }}>
                <TextField
                  select fullWidth required label="Categoria"
                  value={form.category_id}
                  onChange={(event) => setField("category_id", event.target.value)}
                >
                  {catalogs.data.categories.map((item) => (
                    <MenuItem key={item.id} value={item.id}>{item.name}</MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <TextField
                  select fullWidth required label="Tipo"
                  value={form.equipment_type_id}
                  onChange={(event) => setField("equipment_type_id", event.target.value)}
                >
                  {catalogs.data.equipmentTypes.map((item) => (
                    <MenuItem key={item.id} value={item.id}>{item.name}</MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid size={{ xs: 12, md: 4 }}>
                <TextField
                  select fullWidth required label="Setor de origem"
                  value={form.origin_sector_id}
                  onChange={(event) => setField("origin_sector_id", event.target.value)}
                >
                  {catalogs.data.sectors.map((item) => (
                    <MenuItem key={item.id} value={item.id}>{item.name}</MenuItem>
                  ))}
                </TextField>
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth required label="Marca" value={form.brand}
                  onChange={(event) => setField("brand", event.target.value)}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth required label="Modelo" value={form.model}
                  onChange={(event) => setField("model", event.target.value)}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth label="Número patrimonial" value={form.asset_number}
                  onChange={(event) => setField("asset_number", event.target.value)}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth label="Número de série" value={form.serial_number}
                  onChange={(event) => setField("serial_number", event.target.value)}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth required disabled={isEditing} type="datetime-local" label="Data do recolhimento"
                  value={form.collection_date}
                  onChange={(event) => setField("collection_date", event.target.value)}
                  slotProps={{ inputLabel: { shrink: true } }}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth required label="Condição inicial" value={form.initial_condition}
                  onChange={(event) => setField("initial_condition", event.target.value)}
                />
              </Grid>
              <Grid size={12}>
                <TextField
                  fullWidth multiline minRows={2} label="Descrição" value={form.description}
                  onChange={(event) => setField("description", event.target.value)}
                />
              </Grid>
              <Grid size={12}>
                <TextField
                  fullWidth multiline minRows={2} label="Observações do recolhimento"
                  value={form.collection_notes}
                  onChange={(event) => setField("collection_notes", event.target.value)}
                />
              </Grid>
              <Grid size={12}>
                <Stack direction="row" justifyContent="flex-end">
                  <Button
                    type="submit" variant="contained" size="large" startIcon={<SaveIcon />}
                    disabled={mutation.isPending}
                  >
                    {mutation.isPending ? "Salvando..." : isEditing ? "Salvar alterações" : "Cadastrar equipamento"}
                  </Button>
                </Stack>
              </Grid>
            </Grid>
          </Paper>
        )}
      </Stack>
    </Container>
  );
}
