import ArrowForwardOutlinedIcon from "@mui/icons-material/ArrowForwardOutlined";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Divider,
  Grid,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { type FormEvent, useState } from "react";

import { useAuth } from "./AuthContext";

export function LoginPage() {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try { await login(username, password); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Não foi possível autenticar"); }
    finally { setSubmitting(false); }
  }

  return (
    <Grid container minHeight="100vh">
      <Grid size={{ xs: 12, md: 5 }} sx={{ display: { xs: "none", md: "flex" }, bgcolor: "#173D34", color: "white", p: 6, flexDirection: "column" }}>
        <Stack direction="row" alignItems="center" gap={1.5}>
          <Box width={34} height={34} display="grid" gridTemplateColumns="repeat(2,1fr)" gap="3px">{[0, 1, 2, 3].map((item) => <Box key={item} bgcolor={item === 3 ? "#C18435" : "#F4F1E8"} />)}</Box>
          <Typography variant="h5" color="white">REEE-Track</Typography>
        </Stack>
        <Box flexGrow={1} display="flex" flexDirection="column" justifyContent="center" maxWidth={520}>
          <Typography variant="overline" sx={{ color: "rgba(255,255,255,.58)" }}>GESTÃO E RASTREABILIDADE</Typography>
          <Typography sx={{ fontSize: "2.7rem", lineHeight: 1.15, fontWeight: 600, letterSpacing: "-.035em", mt: 1 }}>
            Cada equipamento tem uma história que precisa ser preservada.
          </Typography>
          <Typography sx={{ color: "rgba(255,255,255,.65)", mt: 2, maxWidth: 450 }}>
            Controle institucional do recolhimento à destinação final de resíduos eletroeletrônicos.
          </Typography>
        </Box>
        <Typography variant="caption" sx={{ color: "rgba(255,255,255,.48)" }}>VERSÃO 0.5 · AMBIENTE LOCAL</Typography>
      </Grid>
      <Grid size={{ xs: 12, md: 7 }} display="flex" alignItems="center" justifyContent="center" bgcolor="background.paper">
        <Box width="100%" maxWidth={430} px={3} py={5}>
          <Typography variant="overline" color="text.secondary">ACESSO RESTRITO</Typography>
          <Typography component="h1" variant="h2" mt={0.5}>Entrar no sistema</Typography>
          <Typography color="text.secondary" mt={1}>Use as credenciais fornecidas pelo administrador.</Typography>
          <Divider sx={{ my: 3 }} />
          <Stack component="form" spacing={2.25} onSubmit={handleSubmit}>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField label="Usuário" autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} required autoFocus />
            <TextField label="Senha" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} required />
            <Button type="submit" size="large" variant="contained" endIcon={!submitting && <ArrowForwardOutlinedIcon />} disabled={submitting} sx={{ alignSelf: "stretch" }}>
              {submitting ? <CircularProgress size={24} color="inherit" /> : "Acessar REEE-Track"}
            </Button>
          </Stack>
        </Box>
      </Grid>
    </Grid>
  );
}
