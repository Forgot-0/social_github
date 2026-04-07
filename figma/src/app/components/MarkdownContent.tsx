import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MarkdownContentProps {
  content?: string;
  className?: string;
}

export function MarkdownContent({ content, className = '' }: MarkdownContentProps) {
  return (
    <div className={`markdown-content ${className}`.trim()}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children, ...props }) => {
            const isExternal = typeof href === 'string' && /^https?:\/\//i.test(href);
            return (
              <a
                href={href}
                {...props}
                target={isExternal ? '_blank' : undefined}
                rel={isExternal ? 'noreferrer noopener' : undefined}
              >
                {children}
              </a>
            );
          },
          code: ({ className: codeClassName, children, ...props }) => {
            const text = String(children).replace(/\n$/, '');
            const isBlock = Boolean(codeClassName);

            if (isBlock) {
              return (
                <code className={codeClassName} {...props}>
                  {text}
                </code>
              );
            }

            return (
              <code {...props}>
                {text}
              </code>
            );
          },
        }}
      >
        {content || ''}
      </ReactMarkdown>
    </div>
  );
}
