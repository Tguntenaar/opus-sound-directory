import type { SubmitEntryInput } from "./submit-types.ts";

export type SubmissionOwner = { id: string; email: string; emailVerified: boolean };

/** Only a server-resolved principal may supply ownership/contact details. */
export function ownedSubmissionInput(input: SubmitEntryInput, owner: SubmissionOwner): SubmitEntryInput {
  if (!owner.id || !owner.emailVerified) throw new Error("A verified account is required");
  return { ...input, email: owner.email };
}

export function ownsSubmission(ownerId: string | undefined, userId: string): boolean {
  return !!ownerId && ownerId === userId;
}
