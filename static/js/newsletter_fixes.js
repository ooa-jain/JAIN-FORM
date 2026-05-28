/**
 * newsletter_fixes.js
 * ───────────────────
 * Include this AFTER the main <script> block in templates/newsletter/edit.html
 * Place this tag just before </body>:
 *   <script src="{{ url_for('static', filename='js/newsletter_fixes.js') }}"></script>
 *
 * Fixes:
 *   A. Drag vs Click — clicking a block only selects it; dragging reorders it.
 *   B. Toolbar on cursor placement — formatting toolbar appears when cursor
 *      is placed inside any contenteditable block (not just on text selection).
 *   C. Auto-upload base64 images to /newsletter/upload-image before saving,
 *      so MongoDB never receives raw base64 data.
 */

/* ═══════════════════════════════════════════
   FIX A + B — Replace makeBlkEl with improved version
   • mousedown tracks position; if mouse moves >5px it's a drag; else it's a click
   • focus on any contenteditable shows the toolbar
═══════════════════════════════════════════ */
(function () {
  'use strict';

  /* Wait until the page scripts have run */
  window.addEventListener('load', function () {

    /* ── Patch makeBlkEl ── */
    if (typeof makeBlkEl !== 'undefined') {
      var _origMakeBlkEl = makeBlkEl;

      window.makeBlkEl = function (b, idx) {
        /* Build the element using the original function */
        var wrap = _origMakeBlkEl(b, idx);

        /* Remove the original draggable attribute — we control it ourselves */
        wrap.setAttribute('draggable', 'false');

        var dragStartX = 0, dragStartY = 0, _isDragging = false;

        /* ── mousedown: record start position ── */
        wrap.addEventListener('mousedown', function (e) {
          if (e.target.isContentEditable) return;
          if (['BUTTON', 'INPUT', 'SELECT', 'TEXTAREA', 'A'].includes(e.target.tagName)) return;
          if (e.target.closest('button')) return;
          dragStartX = e.clientX;
          dragStartY = e.clientY;
          _isDragging = false;
        }, true);

        /* ── mousemove: enable dragging only after 5px of movement ── */
        wrap.addEventListener('mousemove', function (e) {
          if (!dragStartX) return;
          var dx = Math.abs(e.clientX - dragStartX);
          var dy = Math.abs(e.clientY - dragStartY);
          if (dx > 5 || dy > 5) {
            _isDragging = true;
            wrap.setAttribute('draggable', 'true');
          }
        }, true);

        /* ── mouseup: if no drag happened, just select ── */
        wrap.addEventListener('mouseup', function (e) {
          if (!_isDragging) {
            /* Pure click — select the block */
            if (typeof selectBlk === 'function') selectBlk(b.id);
          }
          wrap.setAttribute('draggable', 'false');
          _isDragging = false;
          dragStartX  = 0;
          dragStartY  = 0;
        }, true);

        /* ── dragstart / dragend ── */
        wrap.addEventListener('dragstart', function (e) {
          if (typeof window !== 'undefined') window.dragId = b.id;
          wrap.style.opacity = '.4';
          e.dataTransfer.effectAllowed = 'move';
        });
        wrap.addEventListener('dragend', function () {
          if (typeof window !== 'undefined') window.dragId = null;
          wrap.style.opacity = '1';
          wrap.setAttribute('draggable', 'false');
          _isDragging = false;
        });

        /* ── FIX B: show toolbar on focus of any contenteditable in this block ── */
        setTimeout(function () {
          wrap.querySelectorAll('[contenteditable]').forEach(function (el) {
            el.addEventListener('focus', function () {
              if (typeof showToolbarPanel === 'function') showToolbarPanel();
              if (typeof updateToolbarState === 'function') updateToolbarState();
              if (typeof saveSelection === 'function') {
                window.savedSelection = saveSelection();
              }
            });
            el.addEventListener('blur', function (e) {
              var related = e.relatedTarget;
              var panel   = document.getElementById('richToolbarPanel');
              if (panel && panel.contains(related)) return;
              var canvas  = document.getElementById('nlCanvas');
              if (canvas && canvas.contains(related)) return;
              if (typeof hideToolbarPanel === 'function') hideToolbarPanel();
            });
          });
        }, 50);

        return wrap;
      };
    }

    /* ── Also show toolbar when cursor enters header contenteditable areas ── */
    ['nlHdrTitle', 'nlHdrSub', 'nlLogoTxt', 'nlFooter'].forEach(function (id) {
      var el = document.getElementById(id);
      if (!el) return;
      el.addEventListener('focus', function () {
        if (typeof showToolbarPanel === 'function') showToolbarPanel();
        if (typeof updateToolbarState === 'function') updateToolbarState();
      });
    });

  });
})();


/* ═══════════════════════════════════════════
   FIX C — Pre-upload base64 images before saving
   Patches doSave() to convert base64 → /static/ URL first
═══════════════════════════════════════════ */
(function () {
  'use strict';

  window.addEventListener('load', function () {
    if (typeof doSave !== 'function') return;

    /* Upload any base64 data-URLs found inside nlState.blocks */
    async function _uploadBase64InBlocks(blocks) {
      for (var i = 0; i < blocks.length; i++) {
        var block   = blocks[i];
        var content = block.content || {};
        var keys    = Object.keys(content);
        for (var j = 0; j < keys.length; j++) {
          var key = keys[j];
          var val = content[key];
          if (typeof val === 'string' && val.startsWith('data:image/')) {
            try {
              var res  = await fetch('/newsletter/upload-image', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ data_url: val }),
              });
              var data = await res.json();
              if (data.success && data.url) {
                content[key] = data.url;
                /* Also update any live <img> with this base64 src */
                var blkEl = document.querySelector('.nl-blk[data-id="' + block.id + '"]');
                if (blkEl) {
                  blkEl.querySelectorAll('img[src^="data:"]').forEach(function (img) {
                    img.src = data.url;
                  });
                }
              }
            } catch (e) {
              console.warn('[newsletter_fixes] image upload failed for block', block.id, e);
            }
          }
        }
      }
    }

    /* Wrap doSave */
    var _origDoSave = window.doSave;
    window.doSave = async function () {
      if (typeof syncDOMToState === 'function') syncDOMToState();
      if (window.nlState && Array.isArray(window.nlState.blocks)) {
        await _uploadBase64InBlocks(window.nlState.blocks);
      }
      await _origDoSave();
    };
  });

})();