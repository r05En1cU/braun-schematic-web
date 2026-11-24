/* 表格不出现横向滚动条:给每个单元格补 data-label;放不下,或平均每列不足 92px(中文会被挤成竖条),就切换为堆叠。
   要求:表格外层有 .table-wrap(且 .table-wrap{min-width:0});表格要有 <thead>。 */
function fitTables() {
  document.querySelectorAll('.table-wrap table').forEach(t => {
    const heads = [...t.querySelectorAll('thead th')].map(h => h.textContent.trim());
    t.querySelectorAll('tbody tr').forEach(tr => [...tr.children].forEach((td, i) => td.dataset.label = heads[i] || ''));
    t.classList.remove('is-stacked');
    const w = t.closest('.table-wrap'), cols = heads.length || 1;
    if (t.scrollWidth > w.clientWidth + 1 || w.clientWidth / cols < 92) t.classList.add('is-stacked');
  });
}
addEventListener('DOMContentLoaded', fitTables);
addEventListener('resize', fitTables);
document.fonts && document.fonts.ready.then(fitTables);
