import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { Wordmark } from "@/components/brand";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useApp } from "@/lib/app-state";

export const Route = createFileRoute("/signup")({
  head: () => ({
    meta: [
      { title: "Create an account — ChronosGraph" },
      {
        name: "description",
        content: "Request access to ChronosGraph. An admin assigns your role and workspaces.",
      },
      { property: "og:title", content: "Create an account — ChronosGraph" },
      {
        property: "og:description",
        content: "Request access to ChronosGraph. An admin assigns your role and workspaces.",
      },
    ],
  }),
  component: SignupPage,
});

function SignupPage() {
  const { signup } = useApp();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "" });
  const [error, setError] = useState("");

  const set = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((p) => ({ ...p, [k]: e.target.value }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return setError("Please enter your full name.");
    if (!form.email.includes("@")) return setError("Enter a valid work email address.");
    if (form.password.length < 8) return setError("Password must be at least 8 characters.");
    if (form.password !== form.confirm) return setError("Passwords don't match.");
    
    const res = await signup(form.name.trim(), form.email.trim(), form.password);
    if (!res.ok) {
      return setError(res.error ?? "Failed to sign up.");
    }
    navigate({ to: "/" });
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-muted/40 px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex justify-center">
          <Wordmark />
        </div>
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <h1 className="text-lg font-semibold tracking-tight">Create your account</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            New accounts start with limited access. An admin assigns your role and workspaces.
          </p>

          <form onSubmit={submit} className="mt-5 space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="name">Full name</Label>
              <Input id="name" value={form.name} onChange={set("name")} placeholder="Jane Okonjo" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="email">Work email</Label>
              <Input id="email" type="email" value={form.email} onChange={set("email")} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" value={form.password} onChange={set("password")} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="confirm">Confirm password</Label>
              <Input id="confirm" type="password" value={form.confirm} onChange={set("confirm")} />
            </div>
            {error && (
              <p className="rounded-md border border-destructive/30 bg-danger-surface px-3 py-2 text-xs text-destructive">
                {error}
              </p>
            )}
            <Button type="submit" className="w-full">
              Create account
            </Button>
          </form>
        </div>
        <p className="mt-5 text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-primary hover:underline">
            Log in
          </Link>
        </p>
      </div>
    </main>
  );
}
