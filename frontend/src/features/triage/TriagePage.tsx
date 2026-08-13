import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import CheckCircleRoundedIcon from "@mui/icons-material/CheckCircleRounded";
import SaveRoundedIcon from "@mui/icons-material/SaveRounded";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  FormControl,
  FormControlLabel,
  FormHelperText,
  FormLabel,
  LinearProgress,
  MenuItem,
  Radio,
  RadioGroup,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
  completeTriage,
  getTriage,
  getTriageConfiguration,
  saveTriageAnswers,
} from "../../services/api";
import type { AnswerValue, TriageCompletePayload, TriageCriterion } from "../../types/triage";
import { useAuth } from "../auth/AuthContext";

function CriterionInput({
  criterion,
  value,
  onChange,
}: {
  criterion: TriageCriterion;
  value: AnswerValue | undefined;
  onChange: (value: AnswerValue) => void;
}) {
  if (criterion.answer_type === "BOOLEAN") {
    return (
      <RadioGroup row value={value === undefined ? "" : String(value)} onChange={(event) => onChange(event.target.value === "true")}>
        <FormControlLabel value="true" control={<Radio />} label="Sim" />
        <FormControlLabel value="false" control={<Radio />} label="Não" />
      </RadioGroup>
    );
  }
  if (criterion.answer_type === "SINGLE_CHOICE") {
    return (
      <Select fullWidth size="small" value={typeof value === "string" ? value : ""} onChange={(event) => onChange(event.target.value)}>
        {criterion.options.map((option) => <MenuItem key={option} value={option}>{option}</MenuItem>)}
      </Select>
    );
  }
  if (criterion.answer_type === "MULTIPLE_CHOICE") {
    return (
      <Select
        fullWidth
        multiple
        size="small"
        value={Array.isArray(value) ? value : []}
        onChange={(event) => onChange(event.target.value as string[])}
      >
        {criterion.options.map((option) => <MenuItem key={option} value={option}>{option}</MenuItem>)}
      </Select>
    );
  }
  return (
    <TextField
      fullWidth
      size="small"
      type={criterion.answer_type === "NUMBER" ? "number" : "text"}
      value={typeof value === "string" || typeof value === "number" ? value : ""}
      onChange={(event) => onChange(
        criterion.answer_type === "NUMBER" ? Number(event.target.value) : event.target.value,
      )}
    />
  );
}

export function TriagePage() {
  const { triageId } = useParams();
  const { accessToken } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [answers, setAnswers] = useState<Record<string, AnswerValue>>({});
  const [classificationId, setClassificationId] = useState("");
  const [opinion, setOpinion] = useState("");
  const [observations, setObservations] = useState("");
  const [defects, setDefects] = useState("");
  const [components, setComponents] = useState("");

  const triage = useQuery({
    queryKey: ["triage", triageId],
    queryFn: () => getTriage(accessToken!, triageId!),
    enabled: Boolean(accessToken && triageId),
  });
  const config = useQuery({
    queryKey: ["triage-configuration"],
    queryFn: () => getTriageConfiguration(accessToken!),
    enabled: Boolean(accessToken),
  });

  useEffect(() => {
    if (!triage.data) return;
    setAnswers(Object.fromEntries(triage.data.answers.map((answer) => [answer.criterion_id, answer.value])));
    setClassificationId(triage.data.classification?.id ?? "");
    setOpinion(triage.data.technical_opinion ?? "");
    setObservations(triage.data.observations ?? "");
    setDefects(triage.data.defects ?? "");
    setComponents(triage.data.reusable_components ?? "");
  }, [triage.data]);

  const required = config.data?.criteria.filter((criterion) => criterion.is_required) ?? [];
  const answeredRequired = required.filter((criterion) => answers[criterion.id] !== undefined).length;
  const progress = required.length ? Math.round((answeredRequired / required.length) * 100) : 0;

  const answerPayload = useMemo(
    () => Object.entries(answers).map(([criterion_id, value]) => ({ criterion_id, value })),
    [answers],
  );
  const save = useMutation({
    mutationFn: () => saveTriageAnswers(accessToken!, triageId!, answerPayload),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["triage", triageId] }),
  });
  const finish = useMutation({
    mutationFn: async () => {
      await saveTriageAnswers(accessToken!, triageId!, answerPayload);
      const payload: TriageCompletePayload = {
        classification_id: classificationId,
        technical_opinion: opinion,
        observations,
        defects,
        reusable_components: components,
      };
      return completeTriage(accessToken!, triageId!, payload);
    },
    onSuccess: (completed) => {
      void queryClient.invalidateQueries({ queryKey: ["triage-queue"] });
      navigate(`/equipment/${completed.tracking_code}`);
    },
  });
  const error = save.error ?? finish.error ?? triage.error ?? config.error;
  const locked = triage.data?.status !== "IN_PROGRESS";

  if (triage.isLoading || config.isLoading) {
    return <Box minHeight="70vh" display="grid" sx={{ placeItems: "center" }}><CircularProgress /></Box>;
  }

  return (
    <Box p={{ xs: 2, md: 4 }} maxWidth={1100} mx="auto">
      <Button startIcon={<ArrowBackRoundedIcon />} onClick={() => navigate("/triages")} sx={{ mb: 2 }}>
        Voltar à fila
      </Button>
      <Card sx={{ overflow: "hidden" }}>
        <Box sx={{ p: { xs: 3, md: 4 }, background: "#173D34", color: "white" }}>
          <Stack direction={{ xs: "column", sm: "row" }} justifyContent="space-between" gap={2}>
            <Box>
              <Typography variant="overline" sx={{ opacity: 0.75 }}>Avaliação técnica</Typography>
              <Typography variant="h4" fontWeight={800}>{triage.data?.equipment_description}</Typography>
              <Typography sx={{ opacity: 0.8 }}>{triage.data?.tracking_code}</Typography>
            </Box>
            <Chip label={locked ? "Concluída" : "Em andamento"} color={locked ? "success" : "warning"} />
          </Stack>
          {!locked && (
            <Box mt={3}>
              <Stack direction="row" justifyContent="space-between" mb={0.8}>
                <Typography variant="caption">Critérios obrigatórios</Typography>
                <Typography variant="caption">{answeredRequired}/{required.length}</Typography>
              </Stack>
              <LinearProgress variant="determinate" value={progress} sx={{ height: 8, borderRadius: 5 }} />
            </Box>
          )}
        </Box>
        <CardContent sx={{ p: { xs: 2.5, md: 4 } }}>
          {error && <Alert severity="error" sx={{ mb: 3 }}>{(error as Error).message}</Alert>}
          <Typography variant="h6" fontWeight={750}>Checklist configurável</Typography>
          <Typography color="text.secondary" mb={3}>Responda conforme a inspeção física do equipamento.</Typography>
          <Stack gap={2}>
            {config.data?.criteria.map((criterion, index) => (
              <FormControl key={criterion.id} disabled={locked} component="fieldset">
                <Card variant="outlined" sx={{ bgcolor: "background.default" }}>
                  <CardContent>
                    <FormLabel sx={{ color: "text.primary", fontWeight: 650 }}>
                      {index + 1}. {criterion.question} {criterion.is_required && "*"}
                    </FormLabel>
                    {criterion.help_text && <FormHelperText>{criterion.help_text}</FormHelperText>}
                    <Box mt={1}>
                      <CriterionInput
                        criterion={criterion}
                        value={answers[criterion.id]}
                        onChange={(value) => setAnswers((current) => ({ ...current, [criterion.id]: value }))}
                      />
                    </Box>
                  </CardContent>
                </Card>
              </FormControl>
            ))}
          </Stack>

          <Divider sx={{ my: 4 }} />
          <Typography variant="h6" fontWeight={750}>Conclusão técnica</Typography>
          <Stack gap={2.5} mt={2}>
            <TextField
              select
              label="Classificação final"
              value={classificationId}
              onChange={(event) => setClassificationId(event.target.value)}
              disabled={locked}
              required
            >
              {config.data?.classifications.map((classification) => (
                <MenuItem key={classification.id} value={classification.id}>
                  {classification.name} → {classification.target_status.replaceAll("_", " ")}
                </MenuItem>
              ))}
            </TextField>
            <TextField label="Parecer técnico" value={opinion} onChange={(event) => setOpinion(event.target.value)} multiline minRows={3} disabled={locked} required />
            <Stack direction={{ xs: "column", md: "row" }} gap={2}>
              <TextField fullWidth label="Defeitos encontrados" value={defects} onChange={(event) => setDefects(event.target.value)} multiline minRows={2} disabled={locked} />
              <TextField fullWidth label="Componentes aproveitáveis" value={components} onChange={(event) => setComponents(event.target.value)} multiline minRows={2} disabled={locked} />
            </Stack>
            <TextField label="Observações" value={observations} onChange={(event) => setObservations(event.target.value)} multiline minRows={2} disabled={locked} />
          </Stack>

          {!locked && (
            <Stack direction={{ xs: "column", sm: "row" }} justifyContent="flex-end" gap={2} mt={4}>
              <Button variant="outlined" startIcon={<SaveRoundedIcon />} disabled={!answerPayload.length || save.isPending} onClick={() => save.mutate()}>
                Salvar progresso
              </Button>
              <Button
                variant="contained"
                size="large"
                startIcon={<CheckCircleRoundedIcon />}
                disabled={progress < 100 || !classificationId || opinion.trim().length < 3 || finish.isPending}
                onClick={() => finish.mutate()}
              >
                Concluir e classificar
              </Button>
            </Stack>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
