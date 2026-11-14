// Both pages read release/releases.json (newest release first): the home page for the
// version on its button, the release page for everything it shows. Every value is checked
// again here and only ever shown as text, never as markup.
(async function () {
  const VERSION = /^[0-9]+(\.[0-9]+){1,2}$/, DATE = /^\d{4}-\d{2}-\d{2}$/;
  const INSTALLER = /^https:\/\/github\.com\/ysetbon\/OpenStrandStudio\/releases\/download\/[A-Za-z0-9._\/-]+$/;
  const onRelease = Boolean(document.getElementById('notes'));
  const make = (tag, text, name) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (name) node.className = name;
    return node;
  };
  const when = document.getElementById('when');
  let releases;
  try {
    const answer = await fetch(onRelease ? 'releases.json' : 'release/releases.json', { cache: 'no-cache' });
    if (!answer.ok) throw new Error(String(answer.status));
    releases = (await answer.json()).releases;
  } catch {
    if (when) when.textContent = 'The release could not be loaded. Try again in a moment.';
    return;
  }
  releases = (Array.isArray(releases) ? releases : []).filter((r) => r && typeof r === 'object'
    && VERSION.test(r.version) && DATE.test(r.date));
  const latest = releases[0];
  if (!latest) {
    if (when) when.textContent = 'No release is listed yet.';
    return;
  }
  for (const node of document.querySelectorAll('[data-latest]')) node.textContent = latest.version;
  if (!onRelease) return;

  const day = (date) => new Date(`${date}T00:00:00Z`).toLocaleDateString('en-GB',
    { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
  const notes = (release, list, cards) => {
    const rows = (Array.isArray(release.notes) ? release.notes : []).filter((n) => n && typeof n === 'object'
      && typeof n.title === 'string' && typeof n.text === 'string');
    rows.forEach((note, i) => {
      const row = make('li', undefined, cards ? 'card' : ''), words = make('div');
      const layer = make('span', `${rows.length - i}_1`, 'layer');   // numbered like the layer panel, top first
      layer.setAttribute('aria-hidden', 'true');
      words.append(make('h3', note.title), make('p', note.text));
      row.append(layer, words);
      list.append(row);
    });
  };

  when.textContent = `Released ${day(latest.date)}`;
  document.getElementById('latest-tag').hidden = false;
  for (const node of document.querySelectorAll('[data-latest-in]')) node.textContent = `in ${latest.version}`;
  notes(latest, document.getElementById('notes'), true);

  const files = latest.downloads && typeof latest.downloads === 'object' ? latest.downloads : {};
  for (const system of ['windows', 'macos']) {
    const button = document.getElementById(`get-${system}`), url = files[system];
    if (typeof url === 'string' && INSTALLER.test(url)) {
      button.href = url;
      button.removeAttribute('aria-disabled');
      button.append(make('small', decodeURIComponent(url.split('/').pop())));
    } else {
      button.textContent = `No installer for ${latest.version} here yet`;
    }
  }

  const earlier = document.getElementById('earlier');
  for (const release of releases.slice(1)) {
    const fold = make('details', undefined, 'card'), head = make('summary', `Version ${release.version}`);
    const list = make('ul', undefined, 'layers');
    head.append(make('span', day(release.date)));
    notes(release, list, false);
    fold.append(head, list);
    earlier.append(fold);
  }
  document.getElementById('earlier-section').hidden = releases.length < 2;
})();
