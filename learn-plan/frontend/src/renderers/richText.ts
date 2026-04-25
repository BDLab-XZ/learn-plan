function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function renderInline(value: string): string {
  return escapeHtml(value)
    .replace(/`([^`]+)`/g, '<code class="rich-text-inline-code">$1</code>')
    .replace(/\$([^$]+)\$/g, '<span class="rich-text-formula">$1</span>')
}

export function renderRichText(value: string | string[] | undefined): string {
  const raw = Array.isArray(value) ? value.join('\n') : String(value || '')
  // Normalize literal \n strings from JSON
  const text = raw.replace(/\\n/g, '\n').trim()
  if (!text) return ''

  const blocks: string[] = []
  let paragraph: string[] = []
  let listItems: string[] = []
  let codeLines: string[] = []
  let inCode = false

  const flushParagraph = () => {
    if (!paragraph.length) return
    blocks.push(`<p>${renderInline(paragraph.join(' '))}</p>`)
    paragraph = []
  }

  const flushList = () => {
    if (!listItems.length) return
    blocks.push(`<ul class="rich-text-list">${listItems.map((item) => `<li>${renderInline(item)}</li>`).join('')}</ul>`)
    listItems = []
  }

  const flushCode = () => {
    if (!codeLines.length) return
    blocks.push(`<pre class="rich-text-code-block"><code>${escapeHtml(codeLines.join('\n'))}</code></pre>`)
    codeLines = []
  }

  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trimEnd()
    // Code block toggle — works with or without surrounding blank lines
    if (line.trim().startsWith('```')) {
      if (inCode) {
        flushCode()
        inCode = false
      } else {
        flushParagraph()
        flushList()
        inCode = true
      }
      continue
    }
    if (inCode) {
      codeLines.push(rawLine)
      continue
    }
    if (!line.trim()) {
      flushParagraph()
      flushList()
      continue
    }
    const listMatch = line.trim().match(/^[-*]\s+(.+)$/)
    if (listMatch) {
      flushParagraph()
      listItems.push(listMatch[1])
      continue
    }
    flushList()
    paragraph.push(line.trim())
  }

  flushParagraph()
  flushList()
  flushCode()
  return blocks.join('')
}
