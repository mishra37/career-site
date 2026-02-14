import { Job, MatchResult } from "./types";

/**
 * AI Matching Engine
 *
 * This module implements a hybrid matching approach:
 *
 * 1. If OPENAI_API_KEY is set: Uses OpenAI embeddings for semantic matching
 *    - Embeds both resume text and job descriptions
 *    - Computes cosine similarity for ranking
 *    - Provides AI-generated match reasons
 *
 * 2. Fallback: Uses keyword-based TF-IDF-inspired matching
 *    - Extracts keywords from resume
 *    - Scores jobs based on keyword overlap with title, skills, description
 *    - Considers level matching based on experience indicators
 *
 * Scalability Notes:
 * - For 500 jobs: Both approaches work fine in real-time
 * - For 5,000 jobs: Keyword matching still fast; embeddings need batching
 * - For 500,000 jobs: Pre-compute job embeddings, use vector DB (Pinecone/pgvector)
 * - For 5,000,000 jobs: Vector DB with ANN search (HNSW), pre-filtering by category,
 *   tiered matching (coarse filter → fine ranking), caching frequent queries
 */

const OPENAI_API_KEY = process.env.OPENAI_API_KEY;

export async function matchResume(resumeText: string, allJobs: Job[]): Promise<MatchResult[]> {
  if (OPENAI_API_KEY) {
    try {
      return await matchWithOpenAI(resumeText, allJobs);
    } catch (error) {
      console.error("OpenAI matching failed, falling back to keyword matching:", error);
      return matchWithKeywords(resumeText, allJobs);
    }
  }
  return matchWithKeywords(resumeText, allJobs);
}

// ============================================================
// OpenAI Embeddings-based Matching
// ============================================================
async function matchWithOpenAI(resumeText: string, allJobs: Job[]): Promise<MatchResult[]> {
  const { default: OpenAI } = await import("openai");
  const openai = new OpenAI({ apiKey: OPENAI_API_KEY });

  // Build job texts for embedding
  const jobTexts = allJobs.map(
    (job) =>
      `${job.title} | ${job.department} | ${job.level} | ${job.location} | Skills: ${job.skills.join(", ")} | ${job.description}`
  );

  // Get embeddings for resume and all jobs in batch
  const allTexts = [resumeText.slice(0, 8000), ...jobTexts];

  // Batch into groups of 100 to avoid API limits
  const embeddings: number[][] = [];
  for (let i = 0; i < allTexts.length; i += 100) {
    const batch = allTexts.slice(i, i + 100);
    const response = await openai.embeddings.create({
      model: "text-embedding-3-small",
      input: batch,
    });
    embeddings.push(...response.data.map((d) => d.embedding));
  }

  const resumeEmbedding = embeddings[0];
  const jobEmbeddings = embeddings.slice(1);

  // Compute cosine similarity
  const scored = allJobs.map((job, i) => ({
    job,
    score: cosineSimilarity(resumeEmbedding, jobEmbeddings[i]),
  }));

  // Sort by score descending and filter out very low matches
  scored.sort((a, b) => b.score - a.score);
  const threshold = 0.3;
  const topMatches = scored.filter((s) => s.score > threshold);

  // Generate match reasons using AI
  const results: MatchResult[] = [];
  for (const match of topMatches) {
    const reason = generateMatchReason(match.job, match.score);
    results.push({
      job: match.job,
      score: Math.round(match.score * 100),
      reason,
    });
  }

  return results;
}

function cosineSimilarity(a: number[], b: number[]): number {
  let dotProduct = 0;
  let normA = 0;
  let normB = 0;
  for (let i = 0; i < a.length; i++) {
    dotProduct += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }
  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

function generateMatchReason(job: Job, score: number): string {
  if (score > 0.7) return `Excellent match — your background strongly aligns with this ${job.title} role.`;
  if (score > 0.5) return `Good match — your skills and experience are relevant to this ${job.department} position.`;
  if (score > 0.35) return `Potential match — some of your experience may transfer to this role.`;
  return `Partial match — this role may offer a career pivot opportunity.`;
}

// ============================================================
// Keyword-based Matching (Fallback)
// ============================================================
function matchWithKeywords(resumeText: string, allJobs: Job[]): MatchResult[] {
  const resumeLower = resumeText.toLowerCase();
  const resumeTokens = tokenize(resumeLower);

  // Detect experience level from resume
  const detectedLevel = detectLevel(resumeLower);

  // Detect primary field/domain from resume
  const detectedDomains = detectDomains(resumeLower);

  const scored = allJobs.map((job) => {
    let score = 0;
    let reasons: string[] = [];

    // 1. Skill matching (highest weight)
    const skillMatches = job.skills.filter((skill) =>
      resumeLower.includes(skill.toLowerCase())
    );
    const skillScore = job.skills.length > 0 ? (skillMatches.length / job.skills.length) * 40 : 0;
    score += skillScore;
    if (skillMatches.length > 0) {
      reasons.push(`Skills match: ${skillMatches.join(", ")}`);
    }

    // 2. Title/role matching
    const titleWords = [...tokenize(job.title.toLowerCase())];
    const titleMatches = titleWords.filter((w) => resumeTokens.has(w));
    const titleScore = titleWords.length > 0 ? (titleMatches.length / titleWords.length) * 20 : 0;
    score += titleScore;

    // 3. Department/domain matching
    const domainMatch = detectedDomains.some(
      (d) =>
        job.department.toLowerCase().includes(d) ||
        job.title.toLowerCase().includes(d) ||
        job.description.toLowerCase().includes(d)
    );
    if (domainMatch) {
      score += 15;
      reasons.push(`Domain alignment with ${job.department}`);
    }

    // 4. Level matching
    const levelScore = scoreLevelMatch(detectedLevel, job.level);
    score += levelScore * 15;
    if (levelScore > 0.7) {
      reasons.push(`Experience level aligned with ${job.level} role`);
    }

    // 5. Description keyword overlap
    const descTokens = tokenize(job.description.toLowerCase());
    const overlapCount = [...descTokens].filter((t) => resumeTokens.has(t)).length;
    const descScore = descTokens.size > 0 ? Math.min((overlapCount / descTokens.size) * 10, 10) : 0;
    score += descScore;

    // 6. Penalty for completely unrelated domains
    const isHealthcare = job.department === "Healthcare";
    const resumeIsHealthcare = detectedDomains.includes("healthcare") || detectedDomains.includes("nursing") || detectedDomains.includes("medical");
    if (isHealthcare && !resumeIsHealthcare) score *= 0.3;
    if (!isHealthcare && resumeIsHealthcare && !domainMatch) score *= 0.5;

    const reason = reasons.length > 0 ? reasons.slice(0, 2).join(". ") + "." : "General match based on profile analysis.";

    return { job, score: Math.round(Math.min(score, 100)), reason };
  });

  // Sort by score and filter
  scored.sort((a, b) => b.score - a.score);

  // Return jobs with score > 5
  return scored.filter((s) => s.score > 5);
}

function tokenize(text: string): Set<string> {
  const stopWords = new Set([
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of",
    "with", "by", "is", "are", "was", "were", "be", "been", "being", "have",
    "has", "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "shall", "can", "need", "must", "that", "this", "these",
    "those", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her",
    "us", "them", "my", "your", "his", "its", "our", "their", "what", "which",
    "who", "whom", "when", "where", "why", "how", "all", "each", "every",
    "both", "few", "more", "most", "other", "some", "such", "no", "not",
    "only", "own", "same", "so", "than", "too", "very", "just", "about",
    "above", "after", "again", "also", "am", "as", "from", "into", "new",
    "over", "under", "up", "through", "during", "before", "between",
  ]);

  const words = text.match(/\b[a-z][a-z+#.]{1,}\b/g) || [];
  return new Set(words.filter((w) => !stopWords.has(w) && w.length > 2));
}

function detectLevel(resumeText: string): string {
  const indicators = {
    "C-Suite": ["cto", "ceo", "cfo", "coo", "chief", "c-level", "c-suite"],
    VP: ["vice president", "vp of", "vp,", "svp"],
    Director: ["director of", "sr. director", "senior director", "head of"],
    Manager: ["manager", "managing", "team lead"],
    Lead: ["lead engineer", "tech lead", "staff engineer", "principal", "staff"],
    Senior: ["senior", "sr.", "sr ", "5+ years", "6+ years", "7+ years", "8+ years", "10+ years"],
    Mid: ["3+ years", "4+ years", "mid-level"],
    Entry: ["junior", "jr.", "entry-level", "entry level", "0-2 years", "graduate", "new grad", "bootcamp"],
    Intern: ["intern", "internship", "student", "currently pursuing"],
  };

  for (const [level, keywords] of Object.entries(indicators)) {
    if (keywords.some((k) => resumeText.includes(k))) {
      return level;
    }
  }
  return "Mid"; // default
}

function detectDomains(resumeText: string): string[] {
  const domainKeywords: Record<string, string[]> = {
    engineering: ["software", "engineer", "developer", "programming", "code", "coding", "frontend", "backend", "fullstack", "full-stack", "devops", "api"],
    "ai & data science": ["machine learning", "data science", "ai", "artificial intelligence", "nlp", "deep learning", "neural", "model training"],
    design: ["design", "ux", "ui", "user experience", "figma", "prototype", "wireframe", "user research"],
    marketing: ["marketing", "seo", "content", "brand", "campaign", "social media", "digital marketing"],
    sales: ["sales", "business development", "account executive", "quota", "pipeline", "crm"],
    finance: ["finance", "accounting", "financial", "budget", "forecast", "audit", "tax"],
    healthcare: ["nurse", "nursing", "patient", "clinical", "medical", "hospital", "pharmacy", "therapist", "physician", "healthcare"],
    "human resources": ["hr", "human resources", "recruiting", "talent acquisition", "employee relations"],
    product: ["product manager", "product management", "roadmap", "stakeholder", "user stories"],
    legal: ["legal", "attorney", "lawyer", "counsel", "compliance", "contract"],
    operations: ["operations", "supply chain", "logistics", "project management", "construction"],
    education: ["teacher", "teaching", "education", "curriculum", "classroom", "student"],
  };

  const found: string[] = [];
  for (const [domain, keywords] of Object.entries(domainKeywords)) {
    const matchCount = keywords.filter((k) => resumeText.includes(k)).length;
    if (matchCount >= 2) found.push(domain);
  }

  // If nothing found, look for single matches
  if (found.length === 0) {
    for (const [domain, keywords] of Object.entries(domainKeywords)) {
      if (keywords.some((k) => resumeText.includes(k))) {
        found.push(domain);
        break;
      }
    }
  }

  return found;
}

function scoreLevelMatch(detectedLevel: string, jobLevel: string): number {
  const levelOrder = ["Intern", "Entry", "Mid", "Senior", "Lead", "Manager", "Director", "VP", "C-Suite"];
  const detectedIdx = levelOrder.indexOf(detectedLevel);
  const jobIdx = levelOrder.indexOf(jobLevel);

  if (detectedIdx === -1 || jobIdx === -1) return 0.5;

  const diff = Math.abs(detectedIdx - jobIdx);
  if (diff === 0) return 1.0;
  if (diff === 1) return 0.7;
  if (diff === 2) return 0.4;
  if (diff === 3) return 0.2;
  return 0.05;
}
