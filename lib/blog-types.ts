export type BlogFaqItem = {
  q: string;
  a: string;
};

export type BlogPost = {
  title: string;
  /** Short document `<title>` segment (H1 and slug stay unchanged). */
  seoTitle?: string;
  slug: string;
  description: string;
  date: string;
  keywords: string[];
  faq: BlogFaqItem[];
  draft: boolean;
  body: string;
};
