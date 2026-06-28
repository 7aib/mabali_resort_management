/**
 * Generic Phone Lookup Module
 * ───────────────────────────
 * Reusable phone-number lookup that auto-fills guest/customer name
 * and updates a status badge when a match is found.
 *
 * Usage:
 *   PhoneLookup.init({
 *     phoneInputId:  'id_phone_number',
 *     nameInputId:   'id_guest_name',        // optional
 *     badgeId:       'statusBadge',           // optional
 *     foundId:       'customerFound',         // optional – element to show/hide
 *     foundNameId:   'customerName',          // optional – text inside foundId
 *     apiUrl:        '/reservations/api/customer-lookup/?phone=',
 *     debounce:      400,
 *     minLength:     7,
 *     onSelect:      function(data){}         // optional callback
 *   });
 */
const PhoneLookup = (function () {

  function init(opts) {
    const phoneInput = document.getElementById(opts.phoneInputId);
    if (!phoneInput) return;

    const nameInput   = opts.nameInputId   ? document.getElementById(opts.nameInputId)   : null;
    const badge       = opts.badgeId       ? document.getElementById(opts.badgeId)       : null;
    const foundEl     = opts.foundId       ? document.getElementById(opts.foundId)       : null;
    const foundNameEl = opts.foundNameId   ? document.getElementById(opts.foundNameId)   : null;
    const apiUrl      = opts.apiUrl        || '';
    const debounceMs  = opts.debounce      || 400;
    const minLen      = opts.minLength     || 7;
    const onSelect    = opts.onSelect      || null;

    let timer = null;

    /* ── Badge helper (matches status_badge.html classes) ── */
    function setBadge(state, text, icon) {
      if (!badge) return;
      badge.className = 'status-badge-pill ' + state;
      badge.innerHTML = '<i class="' + icon + '"></i> ' + text;
    }

    /* ── Main lookup handler ── */
    function onPhoneInput() {
      const phone = phoneInput.value.trim();
      clearTimeout(timer);

      if (phone.length < minLen) {
        if (foundEl) foundEl.classList.remove('show');
        setBadge('unknown', 'Enter phone to detect status', 'bx bx-loader-circle');
        return;
      }

      setBadge('unknown', 'Checking…', 'bx bx-loader-circle bx-spin');

      timer = setTimeout(function () {
        fetch(apiUrl + encodeURIComponent(phone))
          .then(function (r) { return r.json(); })
          .then(function (data) {
            /* ── Old / returning customer ── */
            if (data.found || data.status === 'Old') {
              var name = data.name || '';
              if (foundEl)   foundEl.classList.add('show');
              if (foundNameEl) foundNameEl.textContent = name;
              if (nameInput && name && !nameInput.value) nameInput.value = name;
              setBadge('old-customer', 'Returning Customer', 'bx bx-check-circle');
            }
            /* ── New customer ── */
            else {
              if (foundEl) foundEl.classList.remove('show');
              setBadge('new-customer', 'New Customer', 'bx bx-star');
            }

            if (onSelect) onSelect(data);
          })
          .catch(function () {
            setBadge('unknown', 'Could not verify', 'bx bx-error-circle');
          });
      }, debounceMs);
    }

    phoneInput.addEventListener('input', onPhoneInput);

    /* Run once on load in case the field is pre-filled */
    if (phoneInput.value.trim().length >= minLen) {
      onPhoneInput();
    }
  }

  return { init: init };
})();
