"use client";

import { useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";
import { BUDGET_RANGES, SPONSOR_PACKAGES, type SponsorPackageId } from "@/lib/sponsor-packages";
import { captureEvent } from "@/lib/analytics-client";

type FormState = {
  companyName: string;
  contactName: string;
  email: string;
  website: string;
  packages: SponsorPackageId[];
  budgetRange: string;
  message: string;
  logoUrl: string;
  companyFax: string;
};

const initial: FormState = {
  companyName: "",
  contactName: "",
  email: "",
  website: "",
  packages: [],
  budgetRange: "",
  message: "",
  logoUrl: "",
  companyFax: "",
};

export function SponsorInterestForm() {
  const searchParams = useSearchParams();
  const refFromUrl = useMemo(() => searchParams.get("ref")?.trim() ?? "", [searchParams]);
  const [form, setForm] = useState<FormState>(initial);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  function togglePackage(id: SponsorPackageId) {
    setForm((f) => ({
      ...f,
      packages: f.packages.includes(id)
        ? f.packages.filter((p) => p !== id)
        : [...f.packages, id],
    }));
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    if (!form.companyName.trim()) {
      setError("Company name is required");
      return;
    }
    if (!form.contactName.trim()) {
      setError("Contact name is required");
      return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
      setError("Enter a valid work email");
      return;
    }
    if (!form.website.trim()) {
      setError("Website is required");
      return;
    }
    if (form.packages.length === 0) {
      setError("Select at least one package");
      return;
    }
    if (!form.budgetRange) {
      setError("Select a budget range");
      return;
    }
    if (form.message.trim().length < 20) {
      setError("Tell us a bit more (at least 20 characters)");
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch("/api/sponsor", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          companyName: form.companyName.trim(),
          contactName: form.contactName.trim(),
          email: form.email.trim(),
          website: form.website.trim(),
          packages: form.packages,
          budgetRange: form.budgetRange,
          message: form.message.trim(),
          logoUrl: form.logoUrl.trim() || undefined,
          companyFax: form.companyFax,
          ref: refFromUrl || undefined,
        }),
      });
      const data = (await res.json()) as { ok?: boolean; error?: string };
      if (!res.ok || !data.ok) {
        setError(data.error ?? "Something went wrong. Try again.");
        return;
      }
      captureEvent("sponsor_form_submit", {
        package_count: form.packages.length,
        budget_range: form.budgetRange,
        ...(refFromUrl ? { ref: refFromUrl } : {}),
      });
      setSuccess(true);
      setForm(initial);
    } catch {
      setError("Network error — check your connection and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  if (success) {
    return (
      <div
        className="rounded-xl border border-violet-500/30 bg-violet-500/10 p-8 text-center"
        role="status"
      >
        <p className="text-lg font-medium text-zinc-50">Thanks — we&apos;ll reply within 1 business day.</p>
        <p className="mt-2 text-sm text-zinc-400">
          We&apos;ll reach out at the email you provided with next steps and availability.
        </p>
        <button
          type="button"
          className="mt-6 text-sm text-violet-400 hover:text-violet-300"
          onClick={() => setSuccess(false)}
        >
          Submit another inquiry
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="space-y-6" noValidate>
      <div className="absolute -left-[9999px] h-0 w-0 overflow-hidden" aria-hidden="true">
        <label htmlFor="companyFax">Fax</label>
        <input
          id="companyFax"
          name="companyFax"
          type="text"
          tabIndex={-1}
          autoComplete="off"
          value={form.companyFax}
          onChange={(e) => setForm((f) => ({ ...f, companyFax: e.target.value }))}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Company name" required>
          <input
            className={inputClass}
            value={form.companyName}
            onChange={(e) => setForm((f) => ({ ...f, companyName: e.target.value }))}
            required
            autoComplete="organization"
          />
        </Field>
        <Field label="Website" required>
          <input
            type="url"
            className={inputClass}
            placeholder="https://"
            value={form.website}
            onChange={(e) => setForm((f) => ({ ...f, website: e.target.value }))}
            required
          />
        </Field>
        <Field label="Contact name" required>
          <input
            className={inputClass}
            value={form.contactName}
            onChange={(e) => setForm((f) => ({ ...f, contactName: e.target.value }))}
            required
            autoComplete="name"
          />
        </Field>
        <Field label="Work email" required>
          <input
            type="email"
            className={inputClass}
            value={form.email}
            onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
            required
            autoComplete="email"
          />
        </Field>
      </div>

      <fieldset>
        <legend className="mb-3 text-sm font-medium text-zinc-200">
          Package interest <span className="text-violet-400">*</span>
        </legend>
        <div className="grid gap-2 sm:grid-cols-2">
          {SPONSOR_PACKAGES.map((pkg) => {
            const checked = form.packages.includes(pkg.id);
            return (
              <label
                key={pkg.id}
                className={`flex cursor-pointer gap-3 rounded-lg border p-3 text-sm transition-colors ${
                  checked
                    ? "border-violet-500/50 bg-violet-500/10"
                    : "border-zinc-800 bg-zinc-900/40 hover:border-zinc-700"
                }`}
              >
                <input
                  type="checkbox"
                  className="mt-0.5 accent-violet-500"
                  checked={checked}
                  onChange={() => togglePackage(pkg.id)}
                />
                <span>
                  <span className="font-medium text-zinc-100">{pkg.name}</span>
                </span>
              </label>
            );
          })}
        </div>
      </fieldset>

      <Field label="Monthly budget range" required>
        <select
          className={inputClass}
          value={form.budgetRange}
          onChange={(e) => setForm((f) => ({ ...f, budgetRange: e.target.value }))}
          required
        >
          <option value="">Select…</option>
          {BUDGET_RANGES.map((b) => (
            <option key={b.value} value={b.value}>
              {b.label}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Message" required>
        <textarea
          className={`${inputClass} min-h-[120px] resize-y`}
          placeholder="What are you promoting, timeline, and any category or sound brief?"
          value={form.message}
          onChange={(e) => setForm((f) => ({ ...f, message: e.target.value }))}
          required
        />
      </Field>

      <Field label="Logo URL (optional)">
        <input
          type="url"
          className={inputClass}
          placeholder="https://cdn.example.com/logo.svg"
          value={form.logoUrl}
          onChange={(e) => setForm((f) => ({ ...f, logoUrl: e.target.value }))}
        />
      </Field>

      {error && (
        <p className="rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300" role="alert">
          {error}
        </p>
      )}

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-lg bg-violet-600 px-4 py-3 text-sm font-medium text-white transition hover:bg-violet-500 disabled:opacity-50 sm:w-auto sm:px-8"
      >
        {submitting ? "Sending…" : "Send inquiry"}
      </button>
    </form>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-zinc-200">
        {label}
        {required ? <span className="text-violet-400"> *</span> : null}
      </span>
      {children}
    </label>
  );
}

const inputClass =
  "w-full rounded-lg border border-zinc-800 bg-zinc-900/60 px-3 py-2.5 text-sm text-zinc-100 placeholder:text-zinc-600 focus:border-violet-500/50 focus:outline-none focus:ring-1 focus:ring-violet-500/40";
