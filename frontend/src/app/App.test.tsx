import { CssBaseline, ThemeProvider } from "@mui/material";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import { AuthProvider } from "../features/auth/AuthContext";
import { App } from "./App";
import { theme } from "./theme";


describe("App", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("exibe o login quando não há sessão", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(JSON.stringify({ message: "Sem sessão" }), { status: 401 })),
    );
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

    render(
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <QueryClientProvider client={queryClient}>
          <MemoryRouter initialEntries={["/"]}>
            <AuthProvider>
              <App />
            </AuthProvider>
          </MemoryRouter>
        </QueryClientProvider>
      </ThemeProvider>,
    );

    expect(await screen.findByRole("heading", { name: "REEE-Track" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Acessar REEE-Track" })).toBeInTheDocument();
  });
});
