import { ALL_BLOG_POSTS } from "./blog.generated";
import type { BlogPost } from "./blog-types";

export type { BlogPost, BlogFaqItem } from "./blog-types";

export function getAllBlogPosts(includeDrafts = false): BlogPost[] {
  const posts = includeDrafts
    ? [...ALL_BLOG_POSTS]
    : ALL_BLOG_POSTS.filter((p) => !p.draft);
  return posts.sort((a, b) => b.date.localeCompare(a.date));
}

export function getBlogPostBySlug(slug: string, includeDrafts = false): BlogPost | undefined {
  const post = ALL_BLOG_POSTS.find((p) => p.slug === slug);
  if (!post) return undefined;
  if (post.draft && !includeDrafts) return undefined;
  return post;
}

export function getPublishedBlogSlugs(): string[] {
  return getAllBlogPosts().map((p) => p.slug);
}
