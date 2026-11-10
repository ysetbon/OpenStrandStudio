// The gallery's page: designs.json lists what scripts/share_inbox.py publish put in
// designs/ (an id, the model, the app's version). Newest first. Every value is checked
// again here and only ever shown as text, never as markup.
(async function () {
  const ID = /^[0-9a-f]{12}$/, MODEL = /^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$/, VERSION = /^[0-9][0-9A-Za-z._-]{0,15}$/;
  const status = document.getElementById('status'), list = document.getElementById('designs');
  const make = (tag, text) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    return node;
  };
  let designs;
  try {
    const answer = await fetch('designs.json', { cache: 'no-cache' });
    if (!answer.ok) throw new Error(String(answer.status));
    designs = (await answer.json()).designs;
  } catch {
    status.textContent = 'The designs could not be loaded. Try again in a moment.';
    return;
  }
  const shown = (Array.isArray(designs) ? designs : []).filter((d) => d && typeof d === 'object'
    && ID.test(d.id) && MODEL.test(d.model) && VERSION.test(d.version)).reverse();
  if (!shown.length) {
    status.textContent = 'No designs yet. The first ones will appear here.';
    return;
  }
  status.textContent = shown.length === 1 ? '1 design' : `${shown.length} designs`;
  for (const design of shown) {
    const item = make('li'), picture = make('img'), words = make('div');
    picture.src = `designs/${design.id}.png`;
    picture.alt = `A strand design made by ${design.model}`;
    picture.loading = 'lazy';
    const file = make('a', 'Download the design (.json)');
    file.href = `designs/${design.id}.json`;
    file.download = `openstrand-${design.id}.json`;
    words.append(make('strong', design.model), make('span', `OpenStrand Studio ${design.version}`), file);
    item.append(picture, words);
    list.append(item);
  }
})();
