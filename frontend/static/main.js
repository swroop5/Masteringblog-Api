// Run on load: restore API base URL and load posts
window.addEventListener('load', () => {
  const saved = localStorage.getItem('apiBaseUrl');
  if (saved) {
    document.getElementById('api-base-url').value = saved;
  }
  loadPosts();
});

function baseUrl() {
  const url = document.getElementById('api-base-url').value.trim();
  localStorage.setItem('apiBaseUrl', url);
  return url;
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.innerText = String(str);
  return div.innerHTML;
}

// Fetch and render all posts
function loadPosts() {
  const url = baseUrl() + '/posts';
  fetch(url)
    .then(r => {
      if (!r.ok) throw new Error('Failed to load posts: ' + r.status);
      return r.json();
    })
    .then(posts => {
      const container = document.getElementById('post-container');
      container.innerHTML = '';
      if (!Array.isArray(posts) || posts.length === 0) {
        container.innerHTML = '<p class="empty">No posts yet. Add one above.</p>';
        return;
      }
      posts.forEach(p => {
        const card = document.createElement('div');
        card.className = 'post';
        card.innerHTML = `
          <h3>${escapeHtml(p.title)}</h3>
          <p>${escapeHtml(p.content)}</p>
          <div class="actions">
            <button class="danger" onclick="deletePost(${p.id})">Delete</button>
            <button onclick="promptUpdate(${p.id}, '${escapeHtml(p.title)}', '${escapeHtml(p.content)}')">Update</button>
          </div>
        `;
        container.appendChild(card);
      });
    })
    .catch(err => {
      console.error(err);
      document.getElementById('post-container').innerHTML =
        `<p class="error">${escapeHtml(err.message)}</p>`;
    });
}

// Create a new post
function addPost() {
  const titleEl = document.getElementById('post-title');
  const contentEl = document.getElementById('post-content');
  const title = titleEl.value.trim();
  const content = contentEl.value.trim();
  if (!title || !content) {
    alert('Please provide both title and content.');
    return;
  }
  fetch(baseUrl() + '/posts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, content })
  })
  .then(r => {
    if (!r.ok) return r.json().then(j => { throw new Error(j.error || 'Failed to create'); });
    return r.json();
  })
  .then(() => {
    titleEl.value = '';
    contentEl.value = '';
    loadPosts();
  })
  .catch(err => alert(err.message));
}

// Delete a post
function deletePost(id) {
  fetch(baseUrl() + '/posts/' + id, { method: 'DELETE' })
    .then(r => {
      if (!r.ok && r.status !== 204) return r.json().then(j => { throw new Error(j.error || 'Delete failed'); });
    })
    .then(loadPosts)
    .catch(err => alert(err.message));
}

// Prompt and update post
function promptUpdate(id, oldTitle, oldContent) {
  const title = prompt('New title:', oldTitle);
  if (title === null) return;
  const content = prompt('New content:', oldContent);
  if (content === null) return;

  fetch(baseUrl() + '/posts/' + id, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, content })
  })
  .then(r => {
    if (!r.ok) return r.json().then(j => { throw new Error(j.error || 'Update failed'); });
  })
  .then(loadPosts)
  .catch(err => alert(err.message));
}
