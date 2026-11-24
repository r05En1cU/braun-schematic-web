/* 公式放不下时按比例缩小(最小 70%),不出现滚动条。缩到 70% 仍放不下的,请用 \\ 或 aligned 手动断行。 */
function fitMath() {
  document.querySelectorAll('.katex-display').forEach(d => {
    const k = d.firstElementChild; d.style.fontSize = '';
    if (k && k.scrollWidth > d.clientWidth) d.style.fontSize = Math.max(70, Math.floor(d.clientWidth / k.scrollWidth * 100)) + '%';
  });
}
addEventListener('resize', fitMath);
