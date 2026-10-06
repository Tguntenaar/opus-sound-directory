import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { ArrowLeft } from "lucide-react";
import { CATEGORY_ORDER, CATEGORIES } from "@/lib/categories";
import { getCategorySeo, isValidCategorySlug } from "@/lib/category-seo";
import { getAllEntriesMerged } from "@/lib/entries";
import { canonicalForPath } from "@/lib/site-metadata";
import { SITE_NAME } from "@/lib/site-url";
import {
  breadcrumbListJsonLd,
  categoryFaqPageJsonLd,
} from "@/lib/structured-data";
import { BrowseGrid } from "@/components/browse-grid";
import { JsonLd } from "@/components/json-ld";

type Props = { params: Promise<{ category: string }> };

export async function generateStaticParams() {
  return CATEGORY_ORDER.map((category) => ({ category }));
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { category } = await params;
  if (!isValidCategorySlug(category)) return { title: "Not found" };
  const seo = getCategorySeo(category)!;
  const path = `/c/${category}`;
  return {
    title: seo.h1,
    description: seo.intro,
    alternates: { canonical: canonicalForPath(path) },
    openGraph: {
      title: `${seo.h1} · ${SITE_NAME}`,
      description: seo.intro,
      url: path,
    },
  };
}

export default async function CategoryPage({ params }: Props) {
  const { category } = await params;
  if (!isValidCategorySlug(category)) notFound();
  const seo = getCategorySeo(category)!;
  const entries = (await getAllEntriesMerged()).filter((e) => e.category === category);
  const catLabel = CATEGORIES[category]?.label ?? category;
  const breadcrumbs = breadcrumbListJsonLd([
    { name: "Browse", path: "/" },
    { name: catLabel, path: `/c/${category}` },
  ]);
  const faqLd = categoryFaqPageJsonLd(category, seo.faq);

  return (
    <div className="flex flex-col gap-10">
      <JsonLd data={[breadcrumbs, faqLd]} />
      <header className="max-w-2xl">
        <Link
          href="/"
          className="inline-flex w-fit items-center gap-1.5 text-sm text-violet-400 transition-colors hover:text-violet-300"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden />
          All sounds
        </Link>
        <h1 className="mt-3 text-2xl font-medium tracking-tight text-zinc-50">{seo.h1}</h1>
        <p className="mt-2 text-sm text-zinc-500">{seo.intro}</p>
      </header>
      <Suspense fallback={<BrowseGrid entries={entries} lockedCategory={category} />}>
        <BrowseGrid entries={entries} lockedCategory={category} />
      </Suspense>
      <section className="max-w-2xl border-t border-zinc-800/80 pt-8">
        <h2 className="text-sm font-medium text-zinc-300">FAQ</h2>
        <dl className="mt-4 flex flex-col gap-4">
          {seo.faq.map((item) => (
            <div key={item.q}>
              <dt className="text-sm font-medium text-zinc-200">{item.q}</dt>
              <dd className="mt-1 text-sm text-zinc-500">{item.a}</dd>
            </div>
          ))}
        </dl>
      </section>
    </div>
  );
}
