import io
import re

from pypdf import PdfReader


def extract_text(filename: str, content: bytes) -> str:
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix in {"txt", "md", "csv"}:
        return content.decode("utf-8", errors="replace")
    if suffix == "pdf":
        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    raise ValueError("Supported prototype formats are PDF, TXT, MD and CSV.")


def propose_events(text: str) -> list[dict]:
    """Return cautious keyword-based candidates for human review; never auto-publish facts."""
    patterns = {
        "mud_loss": r"loss(?:es| circulation)?|lost returns",
        "stuck_pipe": r"stuck pipe|stuck drillstring|overpull",
        "kick": r"kick|well influx|flow check",
        "overpressure": r"overpressure|gas show|high gas",
        "cementing": r"cement(?:ing| job| returns)",
    }
    result = []
    for line_no, line in enumerate(text.splitlines(), 1):
        for event_type, pattern in patterns.items():
            if re.search(pattern, line, flags=re.IGNORECASE):
                result.append({"event_type": event_type, "line": line_no, "excerpt": line.strip()[:400], "review_status": "needs_human_review"})
                break
    return result
