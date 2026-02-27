import { useState } from 'react'

interface CodeBlockProps {
  children: string
  language?: string
}

export function CodeBlock({ children, language = 'bash' }: CodeBlockProps) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    await navigator.clipboard.writeText(children)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="rounded-[var(--radius-xl)] overflow-hidden border border-[var(--color-border)]/50 bg-[var(--color-bg)]">
      <div className="px-5 py-3 border-b border-[var(--color-border)]/50 flex items-center gap-2 bg-[var(--color-surface)]/30">
        <span className="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest">{language}</span>
        <button
          onClick={handleCopy}
          className="ml-auto px-3 py-1.5 rounded-[var(--radius-sm)] text-xs font-medium text-[var(--color-text-muted)] hover:text-[var(--color-accent)] hover:bg-[var(--color-surface)]/50 transition-all"
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <pre className="p-5 overflow-x-auto text-sm font-mono text-[var(--color-text-secondary)] leading-relaxed">
        <code>{children}</code>
      </pre>
    </div>
  )
}
