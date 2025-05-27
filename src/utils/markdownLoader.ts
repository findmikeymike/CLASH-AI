import fs from 'fs';
import path from 'path';
import matter from 'gray-matter';
import { remark } from 'remark';
import html from 'remark-html';

// Define the path to the blog articles
const articlesDirectory = path.join(process.cwd(), 'src/data/blogArticles');

export interface MarkdownArticle {
  id: string;
  slug: string;
  title: string;
  date: string;
  author: string;
  readTime: number;
  excerpt: string;
  content: string;
  imageUrl: string;
  categories: string[];
}

// Get all markdown files from the articles directory
export function getArticleFiles(): string[] {
  try {
    return fs.readdirSync(articlesDirectory).filter(file => file.endsWith('.md'));
  } catch (error) {
    console.error('Error reading article directory:', error);
    return [];
  }
}

// Parse markdown file and extract metadata and content
export async function getArticleData(filename: string): Promise<MarkdownArticle | null> {
  try {
    const slug = filename.replace(/\.md$/, '');
    const fullPath = path.join(articlesDirectory, filename);
    const fileContents = fs.readFileSync(fullPath, 'utf8');
    
    // Use gray-matter to parse the post metadata section
    const matterResult = matter(fileContents);
    
    // Extract metadata from the first few lines if not in frontmatter
    const lines = matterResult.content.split('\n');
    const titleLine = lines[0].startsWith('# ') ? lines[0].substring(2) : '';
    
    // Look for date and read time in the format *May 23, 2025 • 6 min read • CLASH Team*
    const metaLine = lines.find(line => line.startsWith('*') && line.includes('min read'))?.slice(1, -1) || '';
    const metaParts = metaLine.split('•').map(part => part.trim());
    
    const date = metaParts[0] || '';
    const readTimeStr = metaParts[1] || '';
    const readTime = readTimeStr ? parseInt(readTimeStr.match(/(\d+)/)?.[1] || '8') : 8;
    const author = metaParts[2] || 'CLASH Team';
    
    // Extract image URL from markdown
    const imageMatch = matterResult.content.match(/!\[.*?\]\((.*?)\)/);
    const imageUrl = imageMatch ? imageMatch[1] : 'https://images.unsplash.com/photo-1557804506-669a67965ba0';
    
    // Extract excerpt from the first paragraph after the image
    const contentAfterImage = matterResult.content.split(/!\[.*?\]\(.*?\)/)[1] || '';
    const excerptMatch = contentAfterImage.match(/\n([^\n#]+)\n/);
    const excerpt = excerptMatch ? excerptMatch[1].trim() : '';
    
    // Extract tags from the bottom of the article
    const tagsMatch = matterResult.content.match(/\*Tags:(.*?)\*/);
    const tagsString = tagsMatch ? tagsMatch[1] : '';
    const categories = tagsString.split(',').map(tag => tag.trim()).filter(Boolean);
    
    // Use remark to convert markdown into HTML string
    const processedContent = await remark()
      .use(html)
      .process(matterResult.content);
    const contentHtml = processedContent.toString();
    
    // Generate a unique ID
    const id = slug;
    
    return {
      id,
      slug,
      title: titleLine,
      date,
      author,
      readTime,
      excerpt,
      content: contentHtml,
      imageUrl,
      categories: categories.length > 0 ? categories : ['Debate', 'AI', 'CLASH']
    };
  } catch (error) {
    console.error(`Error processing article ${filename}:`, error);
    return null;
  }
}

// Get all articles data
export async function getAllArticles(): Promise<MarkdownArticle[]> {
  const filenames = getArticleFiles();
  const allArticlesData = await Promise.all(
    filenames.map(async filename => {
      return await getArticleData(filename);
    })
  );
  
  // Filter out null values and sort by date
  return allArticlesData
    .filter((article): article is MarkdownArticle => article !== null)
    .sort((a, b) => {
      // Parse dates and sort in descending order (newest first)
      const dateA = new Date(a.date);
      const dateB = new Date(b.date);
      return dateB.getTime() - dateA.getTime();
    });
}
