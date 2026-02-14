import { NextRequest, NextResponse } from "next/server";
import { jobs } from "@/lib/jobs-data";
import { matchResume } from "@/lib/ai-matching";

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get("resume") as File | null;

    if (!file) {
      return NextResponse.json({ error: "No resume file provided" }, { status: 400 });
    }

    // Extract text from the uploaded file
    let resumeText = "";

    if (file.type === "application/pdf") {
      const buffer = Buffer.from(await file.arrayBuffer());
      // Dynamic import to avoid issues with pdf-parse in edge runtime
      const { PDFParse } = await import("pdf-parse");
      const parser = new PDFParse({ data: buffer });
      const pdfData = await parser.getText();
      resumeText = pdfData.text;
    } else if (file.type === "text/plain" || file.name.endsWith(".txt")) {
      resumeText = await file.text();
    } else {
      return NextResponse.json(
        { error: "Unsupported file type. Please upload a PDF or TXT file." },
        { status: 400 }
      );
    }

    if (!resumeText.trim()) {
      return NextResponse.json(
        { error: "Could not extract text from resume. Please try a different file." },
        { status: 400 }
      );
    }

    // Match resume against jobs
    const matches = await matchResume(resumeText, jobs);

    return NextResponse.json({
      matches,
      resumeSummary: resumeText.slice(0, 500),
      totalMatched: matches.length,
    });
  } catch (error) {
    console.error("Error processing resume:", error);
    return NextResponse.json(
      { error: "Failed to process resume. Please try again." },
      { status: 500 }
    );
  }
}
