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
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code class="rich-text-inline-code">$1</code>')
    .replace(/\$([^$]+)\$/g, '<span class="rich-text-formula">$1</span>')
}

export function renderRichText(value: string | string[] | undefined): string {
  const raw = Array.isArray(value) ? value.join('\n') : String(value || '')
  const text = raw.replace(/\\n/g, '\n').trim()
  if (!text) return ''

  const blocks: string[] = []
  let paragraph: string[] = []
  let listItems: string[] = []
  let orderedItems: string[] = []
  let codeLines: string[] = []
  let inCode = false
  let inOrderedList = false

  const flushParagraph = () => {
    if (!paragraph.length) return
    blocks.push(`<p class="rich-text-paragraph">${renderInline(paragraph.join('<br>'))}</p>`)
    paragraph = []
  }

  const flushList = () => {
    if (!listItems.length) return
    blocks.push(`<ul class="rich-text-list">${listItems.map((item) => `<li>${renderInline(item)}</li>`).join('')}</ul>`)
    listItems = []
  }

  const flushOrderedList = () => {
    if (!orderedItems.length) return
    blocks.push(`<ol class="rich-text-ordered-list">${orderedItems.map((item) => `<li>${renderInline(item)}</li>`).join('')}</ol>`)
    orderedItems = []
    inOrderedList = false
  }

  const flushCode = () => {
    if (!codeLines.length) return
    blocks.push(`<pre class="rich-text-code-block"><code>${escapeHtml(codeLines.join('\n'))}</code></pre>`)
    codeLines = []
  }

  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trimEnd()
    // Code block toggle
    if (line.trim().startsWith('```')) {
      if (inCode) {
        flushCode()
        inCode = false
      } else {
        flushParagraph()
        flushList()
        flushOrderedList()
        inCode = true
      }
      continue
    }
    if (inCode) {
      codeLines.push(rawLine)
      continue
    }
    // Blank line: flush everything
    if (!line.trim()) {
      flushParagraph()
      flushList()
      flushOrderedList()
      continue
    }
    // Heading
    const headingMatch = line.trim().match(/^(#{1,3})\s+(.+)$/)
    if (headingMatch) {
      flushParagraph()
      flushList()
      flushOrderedList()
      const level = headingMatch[1].length
      const headingText = headingMatch[2]
      blocks.push(`<h${level} class="rich-text-heading">${renderInline(headingText)}</h${level}>`)
      continue
    }
    // Unordered list
    const ulMatch = line.trim().match(/^[-*]\s+(.+)$/)
    if (ulMatch) {
      flushParagraph()
      flushOrderedList()
      listItems.push(ulMatch[1])
      continue
    }
    // Ordered list
    const olMatch = line.trim().match(/^(\d+)[.)]\s+(.+)$/)
    if (olMatch) {
      flushParagraph()
      flushList()
      inOrderedList = true
      orderedItems.push(olMatch[2])
      continue
    }
    // Regular paragraph line
    flushList()
    flushOrderedList()
    paragraph.push(line.trim())
  }

  flushParagraph()
  flushList()
  flushOrderedList()
  flushCode()
  return blocks.join('')
}
