import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Wordmark } from "@/components/brand";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useApp } from "@/lib/app-state";

export const Route = createFileRoute("/login")({
  head: () => ({
    meta: [
      { title: "Log in — ChronosGraph" },
      { name: "description", content: "Sign in to your ChronosGraph workspace." },
      { property: "og:title", content: "Log in — ChronosGraph" },
      { property: "og:description", content: "Sign in to your ChronosGraph workspace." },
    ],
  }),
  component: LoginPage,
});

function LoginPage() {
  const { login } = useApp();
  const navigate = useNavigate();
  const [email, setEmail] = useState("keerthana@chronosgraph.io");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.includes("@") || password.length < 4) {
      setError("Those credentials didn't match an account. Check your email and password.");
      return;
    }
    const res = await login(email, password);
    if (!res.ok) {
      setError(res.error ?? "Unable to sign in.");
      return;
    }
    navigate({ to: "/" });
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-muted/40 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex justify-center">
          <Wordmark />
        </div>
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <h1 className="text-lg font-semibold tracking-tight">Log in</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Access your temporal knowledge graph workspaces.
          </p>

          <Button variant="outline" className="mt-5 w-full gap-2" type="button">
            <GoogleMark /> Continue with Google
          </Button>
          <div className="my-5 flex items-center gap-3 text-[11px] uppercase tracking-wide text-muted-foreground">
            <span className="h-px flex-1 bg-border" /> or <span className="h-px flex-1 bg-border" />
          </div>

          <form onSubmit={submit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email">Work email</Label>
              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <button type="button" className="text-xs text-primary hover:underline">
                  Forgot password?
                </button>
              </div>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>
            {error && (
              <p className="rounded-md border border-destructive/30 bg-danger-surface px-3 py-2 text-xs text-destructive">
                {error}
              </p>
            )}
            <Button type="submit" className="w-full">
              Log in
            </Button>
          </form>
        </div>
        <p className="mt-5 text-center text-sm text-muted-foreground">
          Don&apos;t have an account?{" "}
          <Link to="/signup" className="font-medium text-primary hover:underline">
            Sign up
          </Link>
        </p>
      </div>
    </main>
  );
}

function GoogleMark() {
  return (
    <svg viewBox="0 0 24 24" className="size-4" aria-hidden="true">
      <path fill="#4285F4" d="M23 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.2a5.3 5.3 0 0 1-2.3 3.5v2.9h3.7c2.2-2 3.4-5 3.4-8.6z" />
      <path fill="#34A853" d="M12 24c3.1 0 5.7-1 7.6-2.8l-3.7-2.9c-1 .7-2.3 1.1-3.9 1.1-3 0-5.5-2-6.4-4.7H1.8v3A12 12 0 0 0 12 24z" />
      <path fill="#FBBC05" d="M5.6 14.7a7.2 7.2 0 0 1 0-4.6v-3H1.8a12 12 0 0 0 0 10.6l3.8-3z" />
      <path fill="#EA4335" d="M12 4.8c1.7 0 3.2.6 4.4 1.7l3.2-3.2A11.5 11.5 0 0 0 12 0 12 12 0 0 0 1.8 7.1l3.8 3C6.5 7.4 9 4.8 12 4.8z" />
    </svg>
  );
}
