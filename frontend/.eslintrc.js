// ESLint for the Next.js frontend. `.eslintrc.js` rather than `.eslintrc.json`
// so the rule deviations below can carry their reasoning inline.
module.exports = {
  extends: 'next/core-web-vitals',
  rules: {
    // Default `forbid` is [">", '"', "}", "'"]. Apostrophes and quotes are
    // left as literal characters: every one of ours sits in user-facing prose
    // that a human edits, and `&apos;` soup makes that copy materially harder
    // to read. `>` and `}` stay forbidden — unescaped, those usually mean
    // genuinely broken JSX rather than intentional punctuation.
    'react/no-unescaped-entities': ['error', { forbid: ['>', '}'] }],
  },
}
