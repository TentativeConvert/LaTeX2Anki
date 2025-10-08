document.querySelectorAll('.note').forEach(note => {
  const uuidEl = note.querySelector('.uuid');
  const uuid = uuidEl ? uuidEl.outerHTML : ''; // preserve uuid HTML
  if (uuidEl) uuidEl.remove();

  // Normalize <br class="fieldseparator"></br> variations
  const raw = note.innerHTML.replace(/<\/?br\s*>/gi, '');
  //const fields = raw.split(/<br class="fieldseparator"[^>]*>/i).map(s => s.trim()).filter(Boolean);
  const fields = raw.split(/<br class="fieldseparator"[^>]*>/i).map(s => s.trim());
  
  if (fields.length > 6) {
    console.warn(`Note ${uuid.replace(/<[^>]*>/g, '')} has more than 6 fields (${fields.length}).`);
  }

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

