<div align="center">
  <img src="assets/logo.png" alt="zu-article-polisher-skill logo" width="320">
  <h1>zu-article-polisher-skill</h1>
  <p><a href="README.md">中文</a> | <strong>English</strong></p>
  <p><strong>Remove AI-flavored scaffolding from Chinese technical writing while preserving the author's claims, facts, and technical caveats.</strong></p>
</div>

> Note: part of this skill was originally informed by the open-source Humanizer skill's approach to spotting AI writing patterns. This version has since been adapted for my own Chinese writing workflow, especially for Chinese documentation, technical essays, opinion pieces, scripts, and talks that need to sound less AI-generated and more publishable.

zu-article-polisher-skill is a Codex skill for Chinese technical writing. Its purpose is not to make prose more ornate. It removes the formulaic scaffolding common in AI-generated drafts while preserving the author's judgment, facts, and technical boundaries, so the final piece reads like it came from a real person with real experience.

It is useful for:

- Chinese technical articles, long-form opinion pieces, and WeChat-style drafts
- Product proposals, internal documents, and project retrospectives
- Voice-over scripts, talks, and presentation drafts
- Second-pass editing of AI-generated drafts before publication

## Core Capabilities

### 1. Remove AI-Style Chinese Writing Patterns

It identifies and rewrites common AI writing artifacts in Chinese, including:

- Template openings and fake guiding questions
- Negation-based parallel phrasing such as `不是...而是...` and `不仅仅是...更是...`
- Three-part structures, forced bulleting, and bolded mini-heading lists
- Empty meaning inflation and forced summary endings
- Promotional tone, white-paper tone, and industry buzzwords
- Vague attribution and unsupported endorsement
- Over-balanced framing, generic challenges, and predictable outlook sections
- Leftover chat-style phrasing and model disclaimers

### 2. Preserve the Author's Real Judgment

This skill prioritizes the author's own point of view, experience, and technical caveats. It does not invent years, numbers, examples, sources, user feedback, or stronger claims just to make the writing feel more concrete.

When editing technical opinion pieces, it protects:

- Clear judgments
- Engineering boundaries
- Real constraints around cost, permissions, reliability, evaluation, migration, and maintenance
- Facts and attribution already present in the original draft

### 3. Rebuild the Article Structure

The skill first extracts the article's real thesis, then rewrites around that thesis instead of doing surface-level synonym replacement.

Typical edits include:

- Turning fake questions into direct judgment statements
- Removing generic setup and repeated summaries
- Reordering paragraphs so the main point appears earlier
- Keeping the reading outline, body headings, and section numbers in sync
- Cleaning up titles, lists, tables, and Markdown formatting

### 4. Support Pre-Publication Checks

This repository includes a helper script:

```bash
python3 zu-article-polisher/scripts/check_article_style.py <markdown-file>
```

The script only locates suspicious patterns. It does not rewrite the article automatically. It checks for:

- Whether the reading outline matches the body headings
- Whether section numbers are continuous
- Fixed AI-style sentence patterns and template structures
- Term casing consistency
- Overused bold text, blank-line issues, trailing spaces, and other Markdown problems

## Repository Layout

```text
.
├── README.md
├── README.en.md
├── assets/
│   └── logo.png
└── zu-article-polisher/
    ├── SKILL.md
    ├── agents/
    │   └── openai.yaml
    ├── references/
    │   └── style-guide.md
    └── scripts/
        └── check_article_style.py
```

- `zu-article-polisher/SKILL.md`: the main skill instructions and workflow.
- `zu-article-polisher/references/style-guide.md`: the pattern library and rewrite principles for Chinese AI-style writing.
- `zu-article-polisher/scripts/check_article_style.py`: the pre-publication helper script.
- `zu-article-polisher/agents/openai.yaml`: OpenAI agent display metadata and the default prompt.

## Install in Claude Code / Codex

The installable skill is the `zu-article-polisher/` directory in [`wwenj/zu-article-polisher`](https://github.com/wwenj/zu-article-polisher).

- Claude Code: copy it to `~/.claude/skills/zu-article-polisher/`
- Codex: copy it to `~/.codex/skills/zu-article-polisher/`

You can also ask an agent to install it:

```text
Download https://github.com/wwenj/zu-article-polisher and install its `zu-article-polisher/` directory into the personal Skill directory for the current tool.
```

## Scope

This skill is not a general-purpose copy editor, and it is not an AI detector. It works best on Chinese materials with a clear opinion, technical substance, and a real publication target.

It does not add facts on the author's behalf, and it does not flatten the original draft into neutral white-paper language. When the source lacks evidence, the right move is to make the wording more modest or explicitly note that a source is needed.
