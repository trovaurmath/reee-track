import AddRoundedIcon from "@mui/icons-material/AddRounded";
import RuleRoundedIcon from "@mui/icons-material/RuleRounded";
import SellOutlinedIcon from "@mui/icons-material/SellOutlined";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControlLabel,
  Grid,
  MenuItem,
  Stack,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import {
  createTriageClassification,
  createTriageCriterion,
  getTriageConfiguration,
} from "../../services/api";
import { useAuth } from "../auth/AuthContext";

const TARGET_STATUSES = [
  "AGUARDANDO_AVALIACAO",
  "AGUARDANDO_DESTINACAO",
  "SEPARADO_REUTILIZACAO",
  "AGUARDANDO_RECICLAGEM",
];

export function TriageConfigPage() {
  const { accessToken } = useAuth();
  const queryClient = useQueryClient();
  const [criterionOpen, setCriterionOpen] = useState(false);
  const [classificationOpen, setClassificationOpen] = useState(false);
  const [criterion, setCriterion] = useState({
    code: "",
    question: "",
    help_text: "",
    answer_type: "BOOLEAN",
    options: "",
    is_required: true,
    display_order: 100,
  });
  const [classification, setClassification] = useState({
    code: "",
    name: "",
    description: "",
    target_status: "AGUARDANDO_AVALIACAO",
    display_order: 100,
  });
  const config = useQuery({
    queryKey: ["triage-configuration", "all"],
    queryFn: () => getTriageConfiguration(accessToken!, true),
    enabled: Boolean(accessToken),
  });
  const createCriterion = useMutation({
    mutationFn: () => createTriageCriterion(accessToken!, {
      ...criterion,
      code: criterion.code.trim().toUpperCase(),
      options: criterion.options.split("\n").map((item) => item.trim()).filter(Boolean),
    }),
    onSuccess: () => {
      setCriterionOpen(false);
      void queryClient.invalidateQueries({ queryKey: ["triage-configuration"] });
    },
  });
  const createClassification = useMutation({
    mutationFn: () => createTriageClassification(accessToken!, {
      ...classification,
      code: classification.code.trim().toUpperCase(),
    }),
    onSuccess: () => {
      setClassificationOpen(false);
      void queryClient.invalidateQueries({ queryKey: ["triage-configuration"] });
    },
  });
  const error = config.error ?? createCriterion.error ?? createClassification.error;

  return (
    <Box p={{ xs: 2, md: 4 }} maxWidth={1300} mx="auto">
      <Typography variant="overline" color="primary.main" fontWeight={700}>Administração</Typography>
      <Typography variant="h3" fontWeight={800}>Modelo de triagem</Typography>
      <Typography color="text.secondary" mt={1} mb={4}>
        Evolua o checklist e as classificações sem alterar o código da aplicação.
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 3 }}>{(error as Error).message}</Alert>}

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 7 }}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Stack direction="row" gap={1.5} alignItems="center">
                  <RuleRoundedIcon color="primary" />
                  <Box><Typography variant="h6" fontWeight={750}>Critérios</Typography><Typography variant="caption" color="text.secondary">{config.data?.criteria.length ?? 0} perguntas cadastradas</Typography></Box>
                </Stack>
                <Button startIcon={<AddRoundedIcon />} variant="contained" onClick={() => setCriterionOpen(true)}>Novo critério</Button>
              </Stack>
              <Divider sx={{ my: 2 }} />
              <Stack divider={<Divider flexItem />}>
                {config.data?.criteria.map((item, index) => (
                  <Stack key={item.id} direction="row" justifyContent="space-between" py={2} gap={2}>
                    <Box><Typography fontWeight={650}>{index + 1}. {item.question}</Typography><Typography variant="caption" color="text.secondary">{item.code} · {item.answer_type}</Typography></Box>
                    <Stack direction="row" gap={1}><Chip size="small" label={item.is_required ? "Obrigatório" : "Opcional"} /><Chip size="small" color={item.is_active ? "success" : "default"} label={item.is_active ? "Ativo" : "Inativo"} /></Stack>
                  </Stack>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, lg: 5 }}>
          <Card>
            <CardContent sx={{ p: 3 }}>
              <Stack direction="row" justifyContent="space-between" alignItems="center">
                <Stack direction="row" gap={1.5} alignItems="center"><SellOutlinedIcon color="secondary" /><Typography variant="h6" fontWeight={750}>Classificações</Typography></Stack>
                <Button startIcon={<AddRoundedIcon />} onClick={() => setClassificationOpen(true)}>Nova</Button>
              </Stack>
              <Divider sx={{ my: 2 }} />
              <Stack gap={2}>
                {config.data?.classifications.map((item) => (
                  <Card key={item.id} variant="outlined"><CardContent><Typography fontWeight={700}>{item.name}</Typography><Typography variant="body2" color="text.secondary">{item.description}</Typography><Chip size="small" sx={{ mt: 1 }} label={`Destino: ${item.target_status.replaceAll("_", " ")}`} /></CardContent></Card>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Dialog open={criterionOpen} onClose={() => setCriterionOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Novo critério de triagem</DialogTitle>
        <DialogContent><Stack gap={2} mt={1}><TextField label="Código" value={criterion.code} onChange={(e) => setCriterion({ ...criterion, code: e.target.value })} required /><TextField label="Pergunta" value={criterion.question} onChange={(e) => setCriterion({ ...criterion, question: e.target.value })} required /><TextField label="Texto de ajuda" value={criterion.help_text} onChange={(e) => setCriterion({ ...criterion, help_text: e.target.value })} /><TextField select label="Tipo de resposta" value={criterion.answer_type} onChange={(e) => setCriterion({ ...criterion, answer_type: e.target.value })}>{["BOOLEAN", "TEXT", "NUMBER", "SINGLE_CHOICE", "MULTIPLE_CHOICE"].map((type) => <MenuItem key={type} value={type}>{type}</MenuItem>)}</TextField>{["SINGLE_CHOICE", "MULTIPLE_CHOICE"].includes(criterion.answer_type) && <TextField label="Opções (uma por linha)" multiline minRows={3} value={criterion.options} onChange={(e) => setCriterion({ ...criterion, options: e.target.value })} />}<FormControlLabel control={<Switch checked={criterion.is_required} onChange={(e) => setCriterion({ ...criterion, is_required: e.target.checked })} />} label="Resposta obrigatória" /></Stack></DialogContent>
        <DialogActions><Button onClick={() => setCriterionOpen(false)}>Cancelar</Button><Button variant="contained" disabled={!criterion.code || !criterion.question || createCriterion.isPending} onClick={() => createCriterion.mutate()}>Criar critério</Button></DialogActions>
      </Dialog>
      <Dialog open={classificationOpen} onClose={() => setClassificationOpen(false)} fullWidth maxWidth="sm">
        <DialogTitle>Nova classificação</DialogTitle>
        <DialogContent><Stack gap={2} mt={1}><TextField label="Código" value={classification.code} onChange={(e) => setClassification({ ...classification, code: e.target.value })} required /><TextField label="Nome" value={classification.name} onChange={(e) => setClassification({ ...classification, name: e.target.value })} required /><TextField label="Descrição" multiline minRows={2} value={classification.description} onChange={(e) => setClassification({ ...classification, description: e.target.value })} /><TextField select label="Status após classificação" value={classification.target_status} onChange={(e) => setClassification({ ...classification, target_status: e.target.value })}>{TARGET_STATUSES.map((status) => <MenuItem key={status} value={status}>{status.replaceAll("_", " ")}</MenuItem>)}</TextField></Stack></DialogContent>
        <DialogActions><Button onClick={() => setClassificationOpen(false)}>Cancelar</Button><Button variant="contained" disabled={!classification.code || !classification.name || createClassification.isPending} onClick={() => createClassification.mutate()}>Criar classificação</Button></DialogActions>
      </Dialog>
    </Box>
  );
}
