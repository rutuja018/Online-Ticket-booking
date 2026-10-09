/**
 * Hotel Booking Live Calculations and Real-Time Promo Validation
 */
document.addEventListener('DOMContentLoaded', () => {
  const checkInInput = document.getElementById('checkInInput');
  const checkOutInput = document.getElementById('checkOutInput');
  const roomCountInput = document.getElementById('roomCountInput');
  const guestCountInput = document.getElementById('guestCountInput');
  const promoInput = document.getElementById('promoCodeInput');
  const applyPromoBtn = document.getElementById('applyPromoBtn');
  const promoStatus = document.getElementById('promoStatusMsg');

  // Pricing Elements
  const nightsCountDisplay = document.getElementById('nightsCountDisplay');
  const pricePerNightVal = parseFloat(document.getElementById('pricePerNightHidden')?.value || '0');
  const baseFareDisplay = document.getElementById('baseFareDisplay');
  const taxesDisplay = document.getElementById('taxesDisplay');
  const serviceFeeDisplay = document.getElementById('serviceFeeDisplay');
  const discountRow = document.getElementById('discountRow');
  const discountDisplay = document.getElementById('discountDisplay');
  const finalTotalDisplay = document.getElementById('finalTotalDisplay');

  let appliedDiscount = 0;
  let appliedPromoCode = '';

  function calculatePricing() {
    if (!checkInInput || !checkOutInput) return;

    const inDate = new Date(checkInInput.value);
    const outDate = new Date(checkOutInput.value);
    
    // Ensure valid dates
    if (isNaN(inDate.getTime()) || isNaN(outDate.getTime())) return;

    // Minimum 1 night
    let diffDays = Math.round((outDate - inDate) / (1000 * 60 * 60 * 24));
    if (diffDays < 1) {
      diffDays = 1;
      const nextDay = new Date(inDate);
      nextDay.setDate(nextDay.getDate() + 1);
      checkOutInput.value = nextDay.toISOString().split('T')[0];
    }

    const rooms = parseInt(roomCountInput ? roomCountInput.value : '1') || 1;
    const baseFare = pricePerNightVal * diffDays * rooms;
    const taxes = Math.round(baseFare * 0.12 * 100) / 100;
    const serviceFee = 49.00;
    const grossTotal = baseFare + taxes + serviceFee;
    const finalTotal = Math.max(1.0, grossTotal - appliedDiscount);

    // Update UI elements
    if (nightsCountDisplay) {
      nightsCountDisplay.textContent = `${diffDays} Night${diffDays > 1 ? 's' : ''}`;
    }
    if (baseFareDisplay) {
      baseFareDisplay.textContent = `₹${baseFare.toFixed(2)}`;
    }
    if (taxesDisplay) {
      taxesDisplay.textContent = `₹${taxes.toFixed(2)}`;
    }
    if (serviceFeeDisplay) {
      serviceFeeDisplay.textContent = `₹${serviceFee.toFixed(2)}`;
    }
    if (discountDisplay && discountRow) {
      if (appliedDiscount > 0) {
        discountRow.style.display = 'flex';
        discountDisplay.textContent = `-₹${appliedDiscount.toFixed(2)}`;
      } else {
        discountRow.style.display = 'none';
      }
    }
    if (finalTotalDisplay) {
      finalTotalDisplay.textContent = `₹${finalTotal.toFixed(2)}`;
    }
  }

  // Event Listeners for Date & Room changes
  if (checkInInput) {
    checkInInput.addEventListener('change', () => {
      if (checkInInput.value) {
        const inDate = new Date(checkInInput.value);
        inDate.setDate(inDate.getDate() + 1);
        const minOut = inDate.toISOString().split('T')[0];
        checkOutInput.min = minOut;
        if (checkOutInput.value <= checkInInput.value) {
          checkOutInput.value = minOut;
        }
      }
      calculatePricing();
    });
  }

  if (checkOutInput) {
    checkOutInput.addEventListener('change', calculatePricing);
  }

  if (roomCountInput) {
    roomCountInput.addEventListener('input', calculatePricing);
    roomCountInput.addEventListener('change', calculatePricing);
  }

  // Dynamic Additional Guest Fields based on guestCountInput
  const additionalGuestsContainer = document.getElementById('additionalGuestsContainer');
  if (guestCountInput && additionalGuestsContainer) {
    function renderAdditionalGuests() {
      const count = parseInt(guestCountInput.value) || 1;
      additionalGuestsContainer.innerHTML = '';

      if (count > 1) {
        let html = '<div style="margin-top: 1.5rem; padding-top: 1.25rem; border-top: 1px dashed var(--border);">';
        html += '<h4 style="font-size: 1.05rem; color: var(--secondary); margin-bottom: 0.75rem;"><i class="fa-solid fa-users" style="color: var(--primary);"></i> Additional Guest Details</h4>';
        
        for (let i = 2; i <= count; i++) {
          html += `
            <div class="form-row" style="margin-bottom: 0.75rem; align-items: flex-end;">
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label" style="font-size: 0.8rem;">Guest ${i} Full Name</label>
                <input type="text" name="guest_${i}_name" class="form-input" placeholder="e.g. Priya Sharma" required>
              </div>
              <div class="form-group" style="margin-bottom: 0; max-width: 100px;">
                <label class="form-label" style="font-size: 0.8rem;">Age</label>
                <input type="number" name="guest_${i}_age" class="form-input" min="1" max="110" value="25">
              </div>
              <div class="form-group" style="margin-bottom: 0; max-width: 140px;">
                <label class="form-label" style="font-size: 0.8rem;">Gender</label>
                <select name="guest_${i}_gender" class="form-select">
                  <option value="MALE">Male</option>
                  <option value="FEMALE">Female</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>
            </div>
          `;
        }
        html += '</div>';
        additionalGuestsContainer.innerHTML = html;
      }
    }

    guestCountInput.addEventListener('input', renderAdditionalGuests);
    guestCountInput.addEventListener('change', renderAdditionalGuests);
    renderAdditionalGuests();
  }

  // Promo Code AJAX Application
  if (applyPromoBtn && promoInput) {
    applyPromoBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      const code = promoInput.value.trim().toUpperCase();
      if (!code) {
        if (promoStatus) {
          promoStatus.innerHTML = '<span style="color: var(--danger); font-size: 0.82rem;"><i class="fa-solid fa-circle-exclamation"></i> Please enter a promo code.</span>';
        }
        return;
      }

      applyPromoBtn.disabled = true;
      applyPromoBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Checking...';

      const inDate = new Date(checkInInput.value);
      const outDate = new Date(checkOutInput.value);
      let diffDays = Math.round((outDate - inDate) / (1000 * 60 * 60 * 24)) || 1;
      const rooms = parseInt(roomCountInput ? roomCountInput.value : '1') || 1;
      const baseFare = pricePerNightVal * diffDays * rooms;

      try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
        const response = await fetch('/hotels/api/validate-promo/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken
          },
          body: new URLSearchParams({
            code: code,
            base_fare: baseFare.toString()
          })
        });

        const data = await response.json();
        if (data.valid) {
          appliedDiscount = parseFloat(data.discount_amount);
          appliedPromoCode = code;
          if (promoStatus) {
            promoStatus.innerHTML = `<span style="color: #046A38; font-weight: 600; font-size: 0.85rem;"><i class="fa-solid fa-circle-check"></i> Coupon <strong>${code}</strong> applied! You saved ₹${appliedDiscount.toFixed(2)}</span>`;
          }
          calculatePricing();
        } else {
          appliedDiscount = 0;
          if (promoStatus) {
            promoStatus.innerHTML = `<span style="color: var(--danger); font-size: 0.85rem;"><i class="fa-solid fa-circle-xmark"></i> ${data.message}</span>`;
          }
          calculatePricing();
        }
      } catch (err) {
        if (promoStatus) {
          promoStatus.innerHTML = `<span style="color: var(--danger); font-size: 0.85rem;">Error checking promo coupon.</span>`;
        }
      } finally {
        applyPromoBtn.disabled = false;
        applyPromoBtn.innerHTML = 'Apply';
      }
    });
  }

  // Initial Calculation Run
  calculatePricing();
});
