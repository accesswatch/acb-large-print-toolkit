# BITS Launches Open-Source AI Toolkit to Automate ACB Large Print Compliance

**FOR IMMEDIATE RELEASE -- April 8, 2026**

***

The Blind Information Technology Solutions (BITS) organization today announced the release of the GLOW Accessibility Toolkit, an AI-powered formatting system built inside Visual Studio Code that automates compliance with the American Council of the Blind (ACB) Large Print Guidelines. The toolkit transforms what has historically been a manual, error-prone process into a one-command operation -- auditing, converting, and generating accessible documents across Markdown, HTML, CSS, and Microsoft Word.

"For decades, producing large print documents meant someone sitting with the ACB spec open in one window and their document in another, checking rules by hand," said **Jeff Bishop, President of BITS**. "We built this toolkit because that workflow doesn't scale. Organizations publish hundreds of agendas, newsletters, and reports every year, and every one of them deserves to be readable by people with low vision. AI can enforce these rules instantly and consistently in a way that human review alone never could."

## What the Toolkit Does

The GLOW Accessibility Toolkit is a suite of AI agents, slash commands, reference stylesheets, document templates, a desktop application, and a web application that automate compliance with the American Council of the Blind Large Print Guidelines. The toolkit now offers five ways to use it:

### Web Application (New -- April 2026)

A browser-based interface at [glow.bits-acb.org](https://glow.bits-acb.org) that requires no installation. Upload a Word document, choose an operation, and get results immediately. The web app provides:

-   **Audit** -- upload a .docx and get a full ACB compliance report in your browser, with findings grouped by severity
-   **Fix** -- upload a non-compliant .docx and download a corrected version with before/after compliance scores
-   **Template** -- generate a pre-configured Word template (.dotx) with ACB-compliant styles
-   **Export** -- convert a .docx to accessible HTML (standalone page with CSS, or a CMS-ready fragment for WordPress/Drupal)
-   **Guidelines** -- browse the complete ACB Large Print specification and WCAG 2.2 digital supplement as a searchable reference

### Recent Quality Improvements (April 2026)

Recent updates based on live user feedback improved the Fix workflow and result clarity:

- Fix Results suppresses `ACB-FAUX-HEADING` from scoring when heading detection is intentionally disabled and lists suppressed rules for transparency.
- Fix Results warns when source body text appears below 18pt so users can anticipate page-count growth after normalization.
- List indentation controls are always visible and toggle disabled/enabled based on the flush-list option.
- Legacy Word VML shapes with explicit `alt=""` are treated as decorative, reducing false missing-alt findings.
- **Quick Rule Exceptions** section added to Fix and Audit forms: users can suppress `ACB-LINK-TEXT`, `ACB-MISSING-ALT-TEXT`, or `ACB-FAUX-HEADING` per operation without entering Custom mode.
- **Preserve centered headings** option lets users skip alignment override for intentionally centered heading styles (useful for creative publications, story titles, poem titles).
- **Per-level list indentation** support added: users can now configure different indent values for Level 1, 2, and 3 lists instead of applying one uniform value across all nesting depths.
- **Dedicated FAQ page** at `/faq/` answers common questions about workflow exceptions, heading preservation, per-level indentation, page-count growth, and known limitations.

The web app runs on a Flask server inside Docker, meets WCAG 2.2 AA from day one with no JavaScript required, and deletes all uploaded files immediately after processing.

### VS Code Copilot Chat Agent

The toolkit's core agent -- the Large Print Formatter -- runs directly inside VS Code's Copilot Chat interface and operates in nine distinct modes:

-   **Audit** -- scans any HTML, CSS, or Markdown file against every ACB rule and produces a PASS/FAIL compliance scorecard
-   **Convert** -- takes existing documents and automatically fixes deviations: bold abuse, fake headings, italic misuse, broken fragments, and missing document structure
-   **Generate** -- creates new ACB-compliant pages from scratch with all typography, spacing, and layout rules applied from the start
-   **Markdown to HTML** -- runs a full conversion pipeline from Markdown source to a complete, accessible HTML document with embedded or linked CSS
-   **CMS Embed** -- produces class-scoped snippets safe to paste directly into WordPress, Drupal, or any content management system without breaking the site theme
-   **Word Setup** -- generates PowerShell scripts that configure Microsoft Word styles to match ACB specifications

The toolkit also bundles a full WCAG 2.2 AA markdown accessibility audit system covering nine domains -- links, alt text, headings, tables, emoji, diagrams, em-dashes, anchor validation, and plain language.

## Built from Real-World Testing

The toolkit was developed and validated against real organizational documents, including the BITS Board Meeting Agenda for April 8, 2026. That document -- converted from Markdown through Pandoc -- initially scored just 26% compliance (8 of 31 applicable rules passing), earning an F grade.

Common issues discovered during testing included entire paragraphs wrapped in bold tags, italic used for dates (prohibited under ACB rules), paragraph-like content faked as headings using bold tags, and `<br>` tags misused as paragraph separators. These patterns now have dedicated detection and automated repair built into the agent.

"When we ran our own board meeting agenda through the first version of the audit, it failed badly," Bishop said. "That was exactly the point. We needed to see what real documents actually look like in the wild, not what a perfectly authored test page looks like. Every failure we found became a rule in the toolkit. The agent now catches patterns that even experienced formatters miss -- like bold being used on an entire paragraph instead of just a word, or Markdown artifacts surviving the conversion to HTML."

## Bridging ACB Print Rules and WCAG Digital Standards

A key design decision in the toolkit is how it handles the intersection of the ACB's print-focused specification and WCAG 2.2 AA requirements for digital content. Where the two standards conflict -- such as line spacing, where ACB specifies 1.15 and WCAG requires support for 1.5 -- the toolkit applies the stricter digital standard by default while using CSS print media queries to revert to ACB values for physical output.

"The ACB guidelines were written for print, and they're excellent for print," Bishop noted. "But organizations today publish the same content on the web, in email, and in PDFs. We couldn't just pick one standard. The toolkit applies WCAG 2.2 AA for screens and ACB specs for paper, and it handles the switching automatically through CSS media queries. Nobody has to think about which rules apply where."

All CSS in the toolkit uses `rem` units rather than pixels, ensuring that browser zoom and text reflow work correctly up to 400% magnification -- a WCAG requirement that pixel-based stylesheets routinely break.

## Designed for Accessibility Practitioners Who Use Screen Readers

The toolkit was built by and for blind and low vision technology professionals. Every interaction runs through VS Code's Chat panel using text-based slash commands -- no mouse-dependent UI, no drag-and-drop, no visual-only feedback.

"I use a screen reader every day. If I can't use the tool I built, it has no business existing," Bishop said. "Every prompt, every question the agent asks, every report it generates -- it's all structured text. There's no point building an accessibility tool that isn't accessible."

The agent uses interactive questions to gather decisions -- CSS delivery method, print intent, conflict resolution between ACB and WCAG rules -- through VS Code's accessible dialog system rather than assuming defaults silently.

## Open and Extensible

The toolkit is structured as a standard VS Code workspace with GitHub Copilot agent files, making it immediately usable by anyone with VS Code and Copilot Chat. Five slash commands provide one-click access to the most common operations:

| Command           | Purpose                                     |
|-------------------|---------------------------------------------|
| `/acb-audit`      | Audit the open file for ACB compliance      |
| `/acb-convert`    | Fix the open file to ACB compliance         |
| `/acb-md-audit`   | Audit a Markdown file for ACB issues        |
| `/acb-md-convert` | Convert Markdown to ACB-compliant HTML      |
| `/acb-word-setup` | Generate a Word styles configuration script |

The toolkit also integrates with external tools when available -- markdownlint for structural Markdown validation and Pandoc for high-fidelity Markdown-to-HTML conversion -- and performs equivalent checks manually when those tools are not installed.

## Merging into Accessibility Agents

The GLOW Accessibility Toolkit is being merged into [Accessibility Agents](http://www.community-access.org), an open-source project that delivers accessibility guidance and remediation across platforms -- web, mobile, desktop, and documents. By joining that ecosystem, the large print agents gain access to a broader network of accessibility specialists covering WCAG auditing, ARIA patterns, design system tokens, CI/CD pipeline integration, and more, while contributing ACB Large Print expertise back to the community.

"We didn't build this to live in a silo," Bishop said. "Accessibility Agents already has dozens of specialized agents covering everything from color contrast to screen reader testing to PDF remediation. Merging the GLOW Accessibility Toolkit into that project means any organization using Accessibility Agents gets large print compliance out of the box -- and our agents get smarter by working alongside theirs. A Markdown file can get an ACB formatting audit and a full WCAG accessibility sweep in the same session, from agents that know how to hand off to each other. That's the value of open source: you build one thing well and it multiplies."

## Removing the Installation Barrier

"The number one piece of feedback we heard from chapters was: 'I don't want to install anything,'" Bishop said. "People would see the desktop tool or the VS Code agent and say, 'That looks great but I just need to check one document.' The web app is the answer. Point your browser to the URL, upload your file, and you are done. No accounts, no downloads, no configuration. It runs on a phone, a Chromebook, a library computer -- anywhere you have a browser."

The web application is built on the same Python core library that powers the desktop tool and the CLI. Bug fixes and new rules added to the core library automatically appear in the web app with no additional work.

## Looking Ahead

"This is the beginning, not the end," Bishop said. "We started with the ACB Large Print Guidelines because that's what our community knows and needs. But the architecture -- an AI agent that knows a specification and can enforce it automatically -- applies to any document standard. We want every organization that serves blind and low vision readers to be able to produce compliant documents without needing a formatting specialist on staff."

***

**About BITS:** The Blind Information Technology Solutions (BITS) is a special interest affiliate of the American Council of the Blind (ACB), dedicated to promoting the use of technology by and for people who are blind or have low vision.

**Contact:** Jeff Bishop, President, BITS -- [bits-acb.org](https://bits-acb.org)
