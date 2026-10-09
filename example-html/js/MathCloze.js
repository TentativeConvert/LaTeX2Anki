document.querySelectorAll('.note').forEach(note => {
  const uuidEl = note.querySelector('.uuid');
  const uuid = uuidEl ? uuidEl.outerHTML : ''; // preserve uuid HTML
  if (uuidEl) uuidEl.remove();

  let raw = note.innerHTML;
  console.log(raw);
  raw = raw.replaceAll(/\(\(CLOZE(\d+)\)\)/g,'<span class="cloze$1"><span class="syntax">{</span>');
  console.log("\nA:\n");
  raw = raw.replaceAll('((HINT))','</span><span class="hint"> <span class="syntax">:</span> ');
  console.log("\nB:\n");
  raw = raw.replaceAll('((CLEND))','<span class="syntax">}</span></span>');
  console.log(raw);
    
  const fields = raw.split("((FIELDSEPARATOR))").map(s => s.trim());
  
  const styled = fields.map((f, i) => {
    switch (i) {
      case 1: return `<div class="field title">${f}</div>`;
      case 2: return `<div class="field prompt">${f}</div>`;
      case 3: return `<div class="field background">${f}</div>`;
      case 4: return `<div class="field chapter">${f}</div>`;
      case 5: return `<div class="field def">${f}</div>`;
      case 6: return `<div class="field number">${f}</div>`;
      default: return `<div class="field">${f}</div>`;
    }
  });
   
  note.innerHTML = uuid + styled.join('');
});

