// 교안 text 블록용 마크다운. 교안에서 쓰는 문법만 다룬다:
// 제목(##), 굵게, `코드`, 순서 있는/없는 목록, 표, 문단.

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

function inline(s) {
  return esc(s)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
}

const isTableRow = (l) => /^\|.*\|\s*$/.test(l);
const cells = (l) => l.trim().replace(/^\||\|$/g, '').split('|').map((c) => c.trim());

export function renderMarkdown(src) {
  const lines = String(src || '').split('\n');
  const out = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) { i++; continue; }

    const h = line.match(/^(#{1,3})\s+(.*)$/);
    if (h) { out.push(`<h3>${inline(h[2])}</h3>`); i++; continue; }

    if (isTableRow(line) && i + 1 < lines.length && /^\|[\s:|-]+\|\s*$/.test(lines[i + 1])) {
      const head = cells(line);
      i += 2;
      const rows = [];
      while (i < lines.length && isTableRow(lines[i])) rows.push(cells(lines[i++]));
      out.push(
        '<div class="md-table"><table><thead><tr>' + head.map((c) => `<th>${inline(c)}</th>`).join('') + '</tr></thead><tbody>' +
        rows.map((r) => '<tr>' + r.map((c) => `<td>${inline(c)}</td>`).join('') + '</tr>').join('') + '</tbody></table></div>'
      );
      continue;
    }

    const ol = line.match(/^(\d+)\.\s+(.*)$/);
    if (ol) {
      const items = [];
      while (i < lines.length && /^\d+\.\s+/.test(lines[i])) items.push(lines[i++].replace(/^\d+\.\s+/, ''));
      out.push(`<ol start="${ol[1]}">` + items.map((t) => `<li>${inline(t)}</li>`).join('') + '</ol>');
      continue;
    }

    if (/^-\s+/.test(line)) {
      const items = [];
      while (i < lines.length && /^-\s+/.test(lines[i])) items.push(lines[i++].replace(/^-\s+/, ''));
      out.push('<ul>' + items.map((t) => `<li>${inline(t)}</li>`).join('') + '</ul>');
      continue;
    }

    const para = [];
    while (i < lines.length && lines[i].trim() && !/^(#{1,3}\s|-\s|\d+\.\s)/.test(lines[i]) && !isTableRow(lines[i])) para.push(lines[i++]);
    out.push(`<p>${para.map(inline).join('<br>')}</p>`);
  }
  return out.join('');
}
