/**
 * Interactive Seat Selection & Dynamic Passenger Form Engine
 * Handles Train Berths, Flight Fuselage Seats, and Bus Decks
 */
document.addEventListener('DOMContentLoaded', () => {
  const seatButtons = document.querySelectorAll('.seat-btn, .berth-card, .flight-seat-btn, .bus-seat-btn');
  const selectedSeatsInput = document.getElementById('selectedSeatsInput');
  const seatChipsContainer = document.getElementById('selectedSeatChips');
  const selectedCountDisplay = document.getElementById('selectedCountDisplay');
  const baseFareDisplay = document.getElementById('baseFareDisplay');
  const taxDisplay = document.getElementById('taxDisplay');
  const totalFareDisplay = document.getElementById('totalFareDisplay');
  const passengerFormsContainer = document.getElementById('passengerFormsContainer');
  const proceedBtn = document.getElementById('proceedToPayBtn');

  const farePerSeat = parseFloat(document.getElementById('farePerSeatInput')?.value || '0');
  const transportType = document.getElementById('transportTypeInput')?.value || 'TRAIN';
  const taxRate = transportType === 'FLIGHT' ? 0.12 : 0.05;
  const convenienceFee = 49.00;

  const maxSeatsAllowed = 6;
  let selectedSeats = [];

  seatButtons.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      if (btn.classList.contains('occupied')) return;

      const seatNum = btn.getAttribute('data-seat-id') || btn.getAttribute('data-seat-number');

      if (btn.classList.contains('selected')) {
        // Deselect
        btn.classList.remove('selected');
        selectedSeats = selectedSeats.filter(s => s !== seatNum);
      } else {
        // Select
        if (selectedSeats.length >= maxSeatsAllowed) {
          alert(`You can select a maximum of ${maxSeatsAllowed} seats per booking.`);
          return;
        }
        btn.classList.add('selected');
        selectedSeats.push(seatNum);
      }

      updateUI();
    });
  });

  function updateUI() {
    // 1. Update hidden input
    if (selectedSeatsInput) {
      selectedSeatsInput.value = selectedSeats.join(', ');
    }

    // 2. Update Chips
    if (seatChipsContainer) {
      seatChipsContainer.innerHTML = '';
      if (selectedSeats.length === 0) {
        seatChipsContainer.innerHTML = '<span class="text-muted" style="font-size: 0.85rem;">No seats selected yet</span>';
      } else {
        selectedSeats.forEach(seat => {
          const chip = document.createElement('span');
          chip.className = 'selected-seat-chip';
          chip.innerHTML = `<i class="fa-solid fa-chair"></i> ${seat}`;
          seatChipsContainer.appendChild(chip);
        });
      }
    }

    // 3. Update Counters and Totals
    const count = selectedSeats.length;
    if (selectedCountDisplay) selectedCountDisplay.textContent = count;

    const baseTotal = count * farePerSeat;
    const taxes = Math.round(baseTotal * taxRate * 100) / 100;
    const finalTotal = count > 0 ? Math.round((baseTotal + taxes + convenienceFee) * 100) / 100 : 0;

    if (baseFareDisplay) baseFareDisplay.textContent = `₹${baseTotal.toFixed(2)}`;
    if (taxDisplay) taxDisplay.textContent = `₹${taxes.toFixed(2)}`;
    if (totalFareDisplay) totalFareDisplay.textContent = `₹${finalTotal.toFixed(2)}`;

    // Enable / Disable submit button
    if (proceedBtn) {
      proceedBtn.disabled = count === 0;
    }

    // 4. Render Dynamic Passenger Fields
    renderPassengerForms(selectedSeats);
  }

  function renderPassengerForms(seats) {
    if (!passengerFormsContainer) return;

    if (seats.length === 0) {
      passengerFormsContainer.innerHTML = `
        <div style="text-align: center; padding: 2rem; background: var(--bg-subtle); border-radius: var(--radius-lg); border: 1px dashed var(--border);">
          <i class="fa-solid fa-users" style="font-size: 2rem; color: var(--text-light); margin-bottom: 0.5rem;"></i>
          <p style="color: var(--text-muted); font-weight: 500;">Select seats on the map above to enter passenger details.</p>
        </div>
      `;
      return;
    }

    let html = '';
    seats.forEach((seat, index) => {
      const pIndex = index + 1;
      html += `
        <div class="card mb-3" style="border: 1.5px solid var(--border); border-radius: var(--radius-md); padding: 1.25rem; margin-bottom: 1.25rem; background: #fff;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--border);">
            <h4 style="font-size: 1.05rem; font-weight: 700; color: var(--secondary);">
              <i class="fa-solid fa-user" style="color: var(--primary); margin-right: 0.4rem;"></i> Passenger ${pIndex}
            </h4>
            <span class="badge badge-primary">Seat: ${seat}</span>
          </div>

          <div class="form-row" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
            <div class="form-group" style="margin-bottom: 0.75rem;">
              <label class="form-label">Full Name *</label>
              <input type="text" name="passenger_${pIndex}_name" required class="form-input" placeholder="As on Govt ID">
            </div>

            <div class="form-group" style="margin-bottom: 0.75rem;">
              <label class="form-label">Age *</label>
              <input type="number" name="passenger_${pIndex}_age" min="1" max="110" required class="form-input" placeholder="Age" value="28">
            </div>

            <div class="form-group" style="margin-bottom: 0.75rem;">
              <label class="form-label">Gender *</label>
              <select name="passenger_${pIndex}_gender" class="form-select" required>
                <option value="MALE">Male</option>
                <option value="FEMALE">Female</option>
                <option value="OTHER">Other</option>
              </select>
            </div>

            <div class="form-group" style="margin-bottom: 0.75rem;">
              <label class="form-label">ID Type *</label>
              <select name="passenger_${pIndex}_id_type" class="form-select" required>
                <option value="AADHAAR">Aadhaar Card</option>
                <option value="PASSPORT">Passport</option>
                <option value="DRIVING_LICENSE">Driving License</option>
                <option value="VOTER_ID">Voter ID</option>
                <option value="PAN_CARD">PAN Card</option>
              </select>
            </div>

            <div class="form-group" style="margin-bottom: 0.75rem;">
              <label class="form-label">ID Number *</label>
              <input type="text" name="passenger_${pIndex}_id_number" required class="form-input" placeholder="e.g. 5412 8901 2345" value="541289012345">
            </div>

            <div class="form-group" style="margin-bottom: 0.75rem;">
              <label class="form-label">Berth / Meal Preference</label>
              <select name="passenger_${pIndex}_berth_pref" class="form-select">
                <option value="NO_PREF">No Preference</option>
                <option value="LOWER">Lower Berth / Window</option>
                <option value="UPPER">Upper Berth / Aisle</option>
                <option value="VEG_MEAL">Veg Meal</option>
                <option value="NON_VEG_MEAL">Non-Veg Meal</option>
              </select>
            </div>
          </div>
        </div>
      `;
    });

    passengerFormsContainer.innerHTML = html;
  }
});
