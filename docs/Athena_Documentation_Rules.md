### 1. File Naming Rules

Avoid generic names like "Report1" or "Project_Update." Use the **Project-Doc-Description-Version** structure.

* **Rule:** Use **Kebab-case** or **Snake_case** (no spaces).
* **Rule:** Use **ISO 8601 Date format** (YYYY-MM-DD) for sorting.
* **Examples:**
* `Athena_Project-Report_Initial-Phase_v1.0.pdf`
* `Athena_Presentation_Technical-Overview_2026-02-05.pptx`
* `Athena_TDD_Architecture-Design_v0.9.docx`



---

### 2. Versioning Rules (SemVer)

Instead of "Final" or "Latest," use the  system:

* **Major (1.0.0):** Use when the document is finished and ready for submission.
* **Minor (0.1.0):** Use when you add a new section (e.g., you just added the *Methodology*).
* **Patch (0.1.1):** Use for small edits, fixing typos, or updating *References*.

---

### 3. Content Rules (Industry Best Practices)

To make your report and PPT content high-quality, follow these four rules:

* **The Single Source of Truth:** Your **Report** is the "Source." The **PPT** should be a "Summary." Never put information in the PPT that isn't already detailed in the Report.
* **MECE Principle:** (Mutually Exclusive, Collectively Exhaustive). Ensure your **Scope** and **Objective** do not overlap or repeat the same points.
* **Visual-First Methodology:** In the *Proposed Methodology* section, industry standards require a diagram (use the **C4 Model** or **UML Flowcharts**) before explaining it in text.
* **Active Voice:** Use "The system extracts tasks" instead of "Tasks will be extracted by the system." It sounds more authoritative.

---

### 4. Structure Summary Table

Follow this mapping to ensure consistency between both formats:

| Section Name | Rule for Content |
| --- | --- |
| **Problem Statement** | Must be quantifiable (e.g., "Manual tracking takes 10 hours/week"). |
| **Motivation** | Align this with current industry trends (e.g., the rise of Agentic AI). |
| **Methodology** | Use a "Block Diagram" for the PPT; use "Step-by-step logic" for the Report. |
| **Hardware/Software** | Categorize by *Development* (Python, Git) vs. *Deployment* (AWS, Docker). |
| **Expected Outcome** | Use bullet points with "Success Metrics." |
| **References** | Follow **IEEE** or **APA** style strictly. |

---

### 5. Formatting "Don'ts"

* **No "Wall of Text":** In the PPT, use the **6x6 Rule** (No more than 6 bullets per slide, 6 words per bullet).
* **No Unverified Links:** Ensure all URLs in your *References* are live and lead to the actual source.
* **No Inconsistent Terms:** If you call it an "AI Agent" in the report, don't call it a "Bot" in the PPT.