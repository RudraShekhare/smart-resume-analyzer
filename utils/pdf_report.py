from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


def generate_resume_report(path, data):
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Resume Analysis Report", styles["Title"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph(f"ATS Score: {data.get('ats')}%", styles["Heading2"]))
    story.append(Spacer(1, 8))

    if data.get("skill_match") is not None:
        story.append(Paragraph(f"Skill Match: {data.get('skill_match')}%", styles["Heading2"]))
        story.append(Spacer(1, 8))

    story.append(Paragraph("Predicted Roles:", styles["Heading2"]))
    for r in data.get("roles", []):
        story.append(Paragraph(f"- {r}", styles["Normal"]))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Summary:", styles["Heading2"]))
    story.append(Paragraph(data.get("summary", ""), styles["Normal"]))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Suggestions:", styles["Heading2"]))
    for s in data.get("suggestions", []):
        story.append(Paragraph(f"- {s}", styles["Normal"]))

    doc = SimpleDocTemplate(path)
    doc.build(story)