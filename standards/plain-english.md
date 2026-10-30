# Writing for the product owner

The product owner reads these documents between meetings. They must see in 30 seconds what is wrong and
what we need from them.

- Lead with what needs a decision. The first thing on the page is the count and the list of blockers.
- One item = one line of problem + one line "Recommended:" + one line "If not decided:" (the consequence).
- Mark impact with a word at the start of the line: **BLOCKER** (cannot build without it), **HIGH**
  (builds the wrong thing), **MEDIUM** (rework later), **LOW** (polish).
- Short sentences, everyday words. No file paths, class names, API or database terms. If a technical word
  is unavoidable, explain it once in brackets.
- Use a made-up example person and real-looking data to show what a gap means
  ("Asha, a manager in Pune, opens the report on Monday - what does she see if no data came in?").
- Quote the requirement document by section and a few words, so the owner can find it.
- No more than 12 items per document; group the rest as "Smaller points" in one list.
- End with "What happens next" in two lines.
- Every document also gets an offline HTML copy: `python scripts/md_to_html.py <file.md>`.
