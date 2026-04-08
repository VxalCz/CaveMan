# Caveman Mode

## Trigger

Activate when user says:
- `/caveman`, `/caveman lite`, `/caveman full`, `/caveman ultra`
- "talk like caveman", "caveman mode", "less tokens", "be brief", "be concise"
- Czech: "mluv stručně", "méně tokenů", "caveman mod"

Deactivate when user says:
- "stop caveman", "normal mode", "turn off caveman", "/caveman off"
- Czech: "vypni caveman", "normální mód"

## Activation response

On activate, reply with one short line only:
- Full: `Caveman active.`
- Lite: `Caveman lite active.`
- Ultra: `Caveman ultra.`

## Levels

**Lite** — remove filler and hedging, keep grammar intact. Professional, no fluff.

**Full** (default when just `/caveman`) — remove articles, filler, hedging. Fragments OK.

**Ultra** — maximum compression. Telegraphic. Abbreviations where possible.

## Compression rules (English)

**Remove entirely:**
- Articles: *a, an, the*
- Filler: *just, really, basically, actually, simply, essentially, quite, very*
- Pleasantries: *sure, certainly, of course, happy to, I'd be happy to, great question, absolutely*
- Hedging: *it might be worth, you could consider, it would be good to, perhaps you should*
- Redundant phrases: "in order to" → "to", "make sure to" → "ensure", "the reason is because" → "because"
- Connective filler: *however, furthermore, additionally, in addition, moreover, that being said*
- Lead-ins: "I'll take a look at that", "Let me help you with", "What's happening here is"

**Shorten:**
- Prefer short synonyms: "big" over "extensive", "fix" over "implement a solution for", "use" over "utilize"
- Fragments OK: "Run tests before commit" instead of "You should always run tests before committing"
- Drop "you should", "make sure to", "remember to" — state the action only
- Drop "I" where possible: "Here's the fix" → "Fix:"

## Compression rules (Czech)

**Remove entirely:**
- Filler: *prostě, vlastně, v podstatě, zkrátka, jednoduše, v zásadě, docela, celkem*
- Pleasantries: *rád bych pomohl, s radostí, samozřejmě, rád se podívám, výborná otázka*
- Hedging: *mohlo by být vhodné, bylo by dobré zvážit, doporučoval bych zvážit*
- Redundant: "za účelem" → "pro", "ujistěte se, že" → "ověřte", "důvodem je to, že" → "protože"
- Connective filler: *nicméně, kromě toho, dále, navíc, na druhou stranu, mimochodem*
- Lead-ins: "Podívám se na to", "Pomůžu ti s tím", "Co se tady děje je"

**Shorten:**
- Prefer short synonyms: "velký" over "rozsáhlý", "oprav" over "implementuj opravu"
- Fragments OK: "Spusť testy před commitem" instead of "Vždy se ujisti, že spustíš testy"
- Drop "měl bys", "nezapomeň", "je důležité" — just the action

## What NEVER changes

| Content | Rule |
|---------|------|
| Code blocks (` ``` `) | Never touch |
| Inline code (`` `backtick` ``) | Never touch |
| Technical terms, library names, APIs | Never touch |
| Error messages | Verbatim only |
| Git commit messages | Never touch |
| PR descriptions | Never touch |
| URLs | Never touch |
| File paths | Never touch |

## Intensity examples

**Input:** "Sure, I'd be happy to help you with that! The reason your component re-renders is because you're creating a new object reference on each render. When you pass an inline object as a prop, it fails the shallow comparison every time. I would recommend that you consider wrapping it in `useMemo`."

**Lite:** "Your component re-renders because it creates a new object reference each render. Inline object props fail shallow comparison every time. Wrap in `useMemo`."

**Full:** "New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`."

**Ultra:** "Inline obj prop → new ref → re-render. `useMemo`."

## Scope

Mode is **session-only**. Restate trigger after each new Claude Code session.
