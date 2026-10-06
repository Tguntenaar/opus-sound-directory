export type SubmitEntryInput = {
  title: string;
  prompt: string;
  email: string;
  category: string;
  mood: string[];
  codeSnippet?: string;
  codeUrl?: string;
};

export type SubmitEntry = SubmitEntryInput & {
  id: string;
  createdAt: string;
};
