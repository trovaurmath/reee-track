import { createTheme } from "@mui/material/styles";

export const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#185544", dark: "#103A30", light: "#DCEAE4" },
    secondary: { main: "#A96619", dark: "#74440C", light: "#F5E7D2" },
    background: { default: "#F3F2ED", paper: "#FCFCF9" },
    text: { primary: "#202824", secondary: "#68716C" },
    divider: "#D9DDD8",
    success: { main: "#34714F" },
    warning: { main: "#A96619" },
  },
  typography: {
    fontFamily: '"Segoe UI Variable", "Segoe UI", Arial, sans-serif',
    h1: { fontSize: "2rem", fontWeight: 650, lineHeight: 1.18 },
    h2: { fontSize: "1.75rem", fontWeight: 650, lineHeight: 1.2 },
    h3: { fontSize: "1.625rem", fontWeight: 650, lineHeight: 1.25, letterSpacing: "-0.015em" },
    h4: { fontSize: "1.35rem", fontWeight: 650, lineHeight: 1.3 },
    h5: { fontSize: "1.1rem", fontWeight: 650 },
    h6: { fontSize: "1rem", fontWeight: 650 },
    overline: { fontSize: "0.68rem", letterSpacing: "0.09em", fontWeight: 700 },
    button: { fontWeight: 650 },
  },
  shape: { borderRadius: 4 },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: { scrollbarColor: "#AEB6B1 #EEEDE8" },
        "::selection": { background: "#C8DDD4" },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: { textTransform: "none", borderRadius: 1, minHeight: 36 },
      },
    },
    MuiCard: { styleOverrides: { root: { boxShadow: "none", border: "1px solid #D9DDD8" } } },
    MuiPaper: { styleOverrides: { root: { backgroundImage: "none", boxShadow: "none" } } },
    MuiChip: { styleOverrides: { root: { borderRadius: 0.75, fontWeight: 600 } } },
    MuiTableHead: {
      styleOverrides: {
        root: { background: "#ECEDE8", "& th": { color: "#4E5853", fontSize: "0.72rem", fontWeight: 700, letterSpacing: "0.04em", textTransform: "uppercase" } },
      },
    },
    MuiTableCell: { styleOverrides: { root: { borderColor: "#E1E3DF" } } },
    MuiOutlinedInput: { styleOverrides: { root: { borderRadius: 1, background: "#FFFFFF" } } },
    MuiAlert: { styleOverrides: { root: { borderRadius: 1 } } },
  },
});
