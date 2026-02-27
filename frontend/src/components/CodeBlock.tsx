interface CodeBlockProps {
  children: string
  language?: string
}

export function CodeBlock({ children, language = 'bash' }: CodeBlockProps) {
  return (
    <div className="rounded-[var(--radius-lg)] overflow-hidden border border-[var(--color-border)] bg-[var(--color-bg)]">
      <div className="px-4 py-2 border-b border-[var(--color-border)] flex items-center gap-2">
        <span className="text-xs font-medium text-[var(--color-text-muted)] uppercase tracking-wider">{language}</span>
        <button
          onClick={() => navigator.clipboard.writeText(children)}
          className="ml-auto text-xs text-[var(--color-text-muted)] hover:text-[var(--color-accent)] transition-colors"
        >
          Copy
        </button>
      </div>
      <pre className="p-4 overflow-x-auto text-sm font-mono text-[var(--color-text-secondary)] leading-relaxed">
        <code>{children}</code>
      </pre>
    </div>
  )
}
