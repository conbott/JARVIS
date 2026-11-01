# RAG & Voice Assistant: Technical Architecture & Code Report

### 1. SSE SOURCES PAYLOAD

#### (a) Document-Grounded Answer (`sources` event)
```json
{
  "type": "sources",
  "source_type": "document",
  "path": "document",
  "fallback_reason": null,
  "best_score": 0.812,
  "threshold": 0.45,
  "sources": [
    {
      "title": "attention-is-all-you-need.pdf (Page 3)",
      "filename": "attention-is-all-you-need.pdf",
      "page": 3,
      "snippet": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
      "source_type": "document",
      "score": 0.812
    }
  ]
}
```

#### (b) DuckDuckGo Web Answer (`sources` event)
```json
{
  "type": "sources",
  "source_type": "web",
  "path": "web",
  "fallback_reason": "low_confidence",
  "best_score": 0.128,
  "threshold": 0.45,
  "sources": [
    {
      "title": "Pokémon Fire Ash - PokeHarbor",
      "url": "https://pokeharbor.com/2021/06/pokemon-fire-ash/",
      "domain": "pokeharbor.com",
      "snippet": "Pokemon Fire Ash is a fan-made Pokemon game that recreates Ash Ketchum's entire anime journey...",
      "source_type": "web"
    }
  ]
}
```

#### Status Event Shape & Path Reporting
```json
{"type": "status", "message": "Searching live web for: \"...\"..."}
```
**Path & Score Reporting:** Yes. The `sources` SSE event now emits:
- `"path"`: `"document"` | `"web"` | `"direct"`
- `"fallback_reason"`: `null` | `"low_confidence"` | `"empty_store"` | `"forced_web"`
- `"best_score"`: float in `[0.0, 1.0]` representing cosine similarity (1.0 = identical, 0.0 = dissimilar)
- `"threshold"`: `0.45`

---

### 2. MARKDOWN RENDERING

Rendered via **`react-markdown` (v10.1.0)** with **`remark-gfm` (v4.0.1)**. No external syntax highlighter library is used.

```tsx
<div className="prose prose-invert prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-[#07080c] prose-pre:border prose-pre:border-white/[0.08] prose-pre:rounded-xl">
  <ReactMarkdown
    remarkPlugins={[remarkGfm]}
    components={{
      code({ className, children, ...props }) {
        return (
          <code className={`${className || ''} bg-[#0c0d14] text-indigo-300 px-1.5 py-0.5 rounded text-xs border border-white/[0.08] font-mono`} {...props}>
            {children}
          </code>
        );
      },
      a({ href, children }) {
        return (
          <a href={href} target="_blank" rel="noreferrer" className="text-indigo-400 hover:text-indigo-300 underline underline-offset-2 inline-flex items-center gap-0.5">
            {children}
          </a>
        );
      },
    }}
  >
    {message.content}
  </ReactMarkdown>
</div>
```
**Why headings/bullets were flat:** Tailwind CSS v4 preflight strips default browser margins, font sizing, and list discs (`list-style: none`, `margin: 0`). `@tailwindcss/typography` is not installed in `package.json`, rendering `.prose` inactive. Standard typography styles (`.prose h1-h4`, `.prose ul`, `.prose ol`, `.prose li`, `.prose strong`) have now been directly added to `frontend/src/index.css`.

---

### 3. TAILWIND SETUP

- **Installed Version:** Tailwind CSS v4 (`tailwindcss: ^4.3.3`, `@tailwindcss/vite: ^4.3.3`).
- **`tailwind.config.js`:** None. Tailwind v4 uses CSS-first configuration via `@import "tailwindcss";` in `src/index.css`.
- **`index.html` Font Imports:** None. Uses system sans-serif font stack.

```css
/* frontend/src/index.css */
@import "tailwindcss";

@layer base {
  body {
    background-color: #0b0f19;
    color: #f1f5f9;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
}
```

---

### 4. STATE AND LAYOUT

#### State Variables in `App.tsx`:
| State Variable | Type | Component(s) Displaying / Using It |
| :--- | :--- | :--- |
| `sessions` | `ChatSession[]` | `Sidebar.tsx` (conversation list), `localStorage` |
| `activeSessionId` | `string` | `Sidebar.tsx` (highlight active), `Header.tsx` |
| `messages` | `ChatMessage[]` | `ChatMessageItem.tsx` (rendered message stream) |
| `isLoading` | `boolean` | `ChatInput.tsx` (disable send, stop button), `Header.tsx` |
| `liveStatus` | `string` | `ThinkingStatus.tsx` (pill above input) |
| `isSidebarOpen` | `boolean` | Layout visibility toggle for `Sidebar.tsx` |
| `isDrawerOpen` | `boolean` | Slide-over drawer visibility for `DocumentDrawer.tsx` |
| `stats` | `DocumentStats \| null` | `Header.tsx`, `Sidebar.tsx` footer, `DocumentDrawer.tsx` |
| `health` | `HealthStatus \| null` | `Header.tsx`, `Sidebar.tsx` footer, `ChatInput.tsx` footer |
| `searchMode` | `SearchMode` | `ChatInput.tsx` (mode selector pills: auto, web, docs) |
| `availableVoices`| `VoiceOption[]` | `Header.tsx` (voice dropdown) |
| `selectedVoice` | `string` | `Header.tsx` (voice dropdown), `localStorage` |
| `playingMessageId`| `string \| null` | `ChatMessageItem.tsx` (toggles Speak / Stop Speaking) |
| `synthesizingMessageId` | `string \| null` | `ChatMessageItem.tsx` (loading spinner during audio fetch) |

#### Hardware/Model/Chunk Duplication Locations:
- **`Header.tsx`**: Shows GPU badge, current model pill, Chroma chunks pill, and Pinecone index pill.
- **`Sidebar.tsx` (Footer)**: Shows Hardware Engine badge with GPU name, model name, Chroma chunk counter, Pinecone index.
- **`ChatInput.tsx` (Footer)**: Shows model status pill and hardware engine badge below the prompt box.

---

### 5. VOICE ENGINE

- **TTS Engine:** Microsoft `edge-tts` (v7.3.1) only. Kokoro is **not** installed.
- **VRAM / Hardware Footprint:** Runs 100% on CPU / network (0 MB GPU VRAM used).
- **Auto-Play:** **No.** Typed or voice messages never trigger audio automatically. Synthesis and playback only run when the user explicitly clicks the `Speak` button on an assistant message card.
