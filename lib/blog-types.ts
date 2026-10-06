export type BlogFaqItem = {
  q: string;
  a: string;
};

export type BlogPost = {
  title: string;
  slug: string;
  description: string;
  date: string;
  keywords: string[];
  faq: BlogFaqItem[];
  draft: boolean;
  body: string;
};
