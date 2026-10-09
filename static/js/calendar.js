/* ==========================================================================
   RailAway — Travel Itinerary & Fare Price Calendar Script
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {
  // 1. Parse initial events data
  const rawEventsElem = document.getElementById('allEventsData');
  let allEvents = [];
  if (rawEventsElem) {
    try {
      allEvents = JSON.parse(rawEventsElem.textContent || '[]');
    } catch (e) {
      console.error('Error parsing calendar events JSON:', e);
    }
  }

  // State management
  const today = new Date();
  let currentYear = today.getFullYear();
  let currentMonth = today.getMonth(); // 0-indexed (0 = Jan, 9 = Oct)
  let activeFilter = 'ALL';
  let activeStatus = '';
  let activeView = 'month';

  const monthNames = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  // DOM Elements
  const calMonthDisplay = document.getElementById('calMonthDisplay');
  const calDaysGrid = document.getElementById('calDaysGrid');
  const calTimelineList = document.getElementById('calTimelineList');
  const monthViewContainer = document.getElementById('monthViewContainer');
  const timelineViewContainer = document.getElementById('timelineViewContainer');
  const calPrevMonthBtn = document.getElementById('calPrevMonthBtn');
  const calNextMonthBtn = document.getElementById('calNextMonthBtn');
  const calTodayBtn = document.getElementById('calTodayBtn');
  const calStatusSelect = document.getElementById('calStatusSelect');
  const filterPills = document.querySelectorAll('.cal-pill');
  const viewTabBtns = document.querySelectorAll('.cal-tab-btn');

  // Modal Elements
  const calEventModal = document.getElementById('calEventModal');
  const closeCalModalBtn = document.getElementById('closeCalModalBtn');
  const modalCloseActionBtn = document.getElementById('modalCloseActionBtn');
  const modalEventTitle = document.getElementById('modalEventTitle');
  const modalEventBody = document.getElementById('modalEventBody');
  const modalActionTicketBtn = document.getElementById('modalActionTicketBtn');

  // Filter events based on active category & status
  function getFilteredEvents() {
    return allEvents.filter(ev => {
      // Category filter
      if (activeFilter !== 'ALL' && ev.type !== activeFilter) {
        return false;
      }
      // Status filter
      if (activeStatus === 'CONFIRMED' && ev.is_cancelled) {
        return false;
      }
      if (activeStatus === 'CANCELLED' && !ev.is_cancelled) {
        return false;
      }
      if (activeStatus === 'PENDING' && ev.status !== 'PENDING') {
        return false;
      }
      return true;
    });
  }

  // Render the Calendar
  function renderCalendar() {
    if (!calMonthDisplay || !calDaysGrid) return;

    // Update Header Display
    calMonthDisplay.textContent = `${monthNames[currentMonth]} ${currentYear}`;

    // Get First day of the month & total days
    const firstDayIndex = new Date(currentYear, currentMonth, 1).getDay(); // 0 = Sun, 1 = Mon ...
    // Adjust for Monday start (0 = Mon, 6 = Sun)
    const startOffset = (firstDayIndex + 6) % 7;
    const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
    const daysInPrevMonth = new Date(currentYear, currentMonth, 0).getDate();

    const filteredEvents = getFilteredEvents();

    // Map events by date string YYYY-MM-DD
    const eventsByDate = {};
    filteredEvents.forEach(ev => {
      if (!eventsByDate[ev.date]) {
        eventsByDate[ev.date] = [];
      }
      eventsByDate[ev.date].push(ev);
    });

    calDaysGrid.innerHTML = '';

    // 1. Trailing days from previous month
    for (let i = startOffset - 1; i >= 0; i--) {
      const prevDateNum = daysInPrevMonth - i;
      const cell = document.createElement('div');
      cell.className = 'cal-day-cell other-month';
      cell.innerHTML = `
        <div class="cal-day-top">
          <span class="cal-date-num">${prevDateNum}</span>
        </div>
      `;
      calDaysGrid.appendChild(cell);
    }

    // 2. Current Month Days
    for (let d = 1; d <= daysInMonth; d++) {
      const monthFormatted = String(currentMonth + 1).padStart(2, '0');
      const dayFormatted = String(d).padStart(2, '0');
      const dateStr = `${currentYear}-${monthFormatted}-${dayFormatted}`;

      const cell = document.createElement('div');
      cell.className = 'cal-day-cell';

      // Check if today
      const isToday = (
        d === today.getDate() &&
        currentMonth === today.getMonth() &&
        currentYear === today.getFullYear()
      );
      if (isToday) {
        cell.classList.add('today');
      }

      // Top bar of day cell
      const dayTop = document.createElement('div');
      dayTop.className = 'cal-day-top';
      dayTop.innerHTML = `<span class="cal-date-num">${d}</span>`;
      cell.appendChild(dayTop);

      // Events container
      const eventsContainer = document.createElement('div');
      eventsContainer.className = 'cal-events-list';

      const dayEvents = eventsByDate[dateStr] || [];
      const maxDisplay = 2;

      dayEvents.slice(0, maxDisplay).forEach(ev => {
        const pill = document.createElement('div');
        pill.className = `cal-event-pill ${ev.badge_class}`;
        pill.innerHTML = `
          <i class="${ev.icon}"></i>
          <span class="event-title" style="flex: 1; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(ev.title)}</span>
          <span class="event-time">${escapeHtml(ev.time)}</span>
        `;
        pill.addEventListener('click', (e) => {
          e.stopPropagation();
          openEventModal(ev);
        });
        eventsContainer.appendChild(pill);
      });

      if (dayEvents.length > maxDisplay) {
        const moreBtn = document.createElement('button');
        moreBtn.className = 'cal-more-events-btn';
        moreBtn.textContent = `+${dayEvents.length - maxDisplay} more`;
        moreBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          openDayEventsModal(dateStr, dayEvents);
        });
        eventsContainer.appendChild(moreBtn);
      }

      cell.appendChild(eventsContainer);

      // Allow clicking day cell if it has events
      if (dayEvents.length > 0) {
        cell.style.cursor = 'pointer';
        cell.addEventListener('click', () => {
          if (dayEvents.length === 1) {
            openEventModal(dayEvents[0]);
          } else {
            openDayEventsModal(dateStr, dayEvents);
          }
        });
      }

      calDaysGrid.appendChild(cell);
    }

    // 3. Leading days for next month to complete the grid (total multiple of 7)
    const totalCells = startOffset + daysInMonth;
    const nextMonthFiller = (7 - (totalCells % 7)) % 7;
    for (let j = 1; j <= nextMonthFiller; j++) {
      const cell = document.createElement('div');
      cell.className = 'cal-day-cell other-month';
      cell.innerHTML = `
        <div class="cal-day-top">
          <span class="cal-date-num">${j}</span>
        </div>
      `;
      calDaysGrid.appendChild(cell);
    }

    // Render Timeline View in background/sync
    renderTimelineView(filteredEvents);
  }

  // Render Agenda / Timeline View
  function renderTimelineView(filteredEvents) {
    if (!calTimelineList) return;

    calTimelineList.innerHTML = '';

    if (filteredEvents.length === 0) {
      calTimelineList.innerHTML = `
        <div style="text-align: center; padding: 3rem 1rem; color: var(--text-muted);">
          <i class="fa-regular fa-calendar-xmark" style="font-size: 3rem; margin-bottom: 1rem; color: #cbd5e1;"></i>
          <h3 style="color: var(--secondary); font-size: 1.2rem;">No Bookings Found</h3>
          <p style="font-size: 0.9rem;">You don't have any bookings matching this filter in your calendar.</p>
          <a href="/railways/" class="btn btn-sm btn-primary" style="margin-top: 1rem;">
            <i class="fa-solid fa-plus"></i> Book a Journey
          </a>
        </div>
      `;
      return;
    }

    // Group events by date
    const grouped = {};
    filteredEvents.forEach(ev => {
      if (!grouped[ev.date]) {
        grouped[ev.date] = [];
      }
      grouped[ev.date].push(ev);
    });

    // Sort dates ascending
    const sortedDates = Object.keys(grouped).sort();

    sortedDates.forEach(dateKey => {
      const dateObj = new Date(dateKey + 'T00:00:00');
      const dayNum = dateObj.getDate();
      const monthStr = monthNames[dateObj.getMonth()].substring(0, 3);
      const weekdayStr = dateObj.toLocaleDateString('en-US', { weekday: 'short' });

      const groupDiv = document.createElement('div');
      groupDiv.className = 'cal-timeline-group';

      groupDiv.innerHTML = `
        <div class="cal-timeline-date">
          <div class="t-day">${dayNum}</div>
          <div class="t-month">${monthStr}, ${weekdayStr}</div>
        </div>
        <div class="cal-timeline-cards" id="timeline-cards-${dateKey}"></div>
      `;

      calTimelineList.appendChild(groupDiv);

      const cardsContainer = groupDiv.querySelector(`#timeline-cards-${dateKey}`);
      grouped[dateKey].forEach(ev => {
        const card = document.createElement('div');
        card.className = 'cal-timeline-card';
        card.innerHTML = `
          <div style="display: flex; align-items: center; gap: 1rem;">
            <div style="width: 44px; height: 44px; border-radius: 10px; background: ${ev.theme_color}18; color: ${ev.theme_color}; display: flex; align-items: center; justify-content: center; font-size: 1.25rem;">
              <i class="${ev.icon}"></i>
            </div>
            <div>
              <div style="display: flex; align-items: center; gap: 0.5rem;">
                <h4 style="font-size: 1.05rem; color: var(--secondary); margin: 0;">${escapeHtml(ev.title)}</h4>
                <span class="badge ${ev.badge_class}" style="font-size: 0.72rem;">${escapeHtml(ev.status_display)}</span>
              </div>
              <p style="font-size: 0.85rem; color: var(--text-muted); margin: 0.2rem 0 0 0;">
                <i class="fa-regular fa-clock"></i> ${escapeHtml(ev.time)} &bull; 
                <span>${escapeHtml(ev.route_display)}</span> &bull; 
                <span style="font-weight: 600;">PNR/Ref:</span> ${escapeHtml(ev.ref)}
              </p>
            </div>
          </div>
          <div style="display: flex; align-items: center; gap: 0.75rem;">
            <span style="font-weight: 700; font-size: 1.05rem; color: var(--secondary);">₹${ev.fare.toFixed(2)}</span>
            <button type="button" class="btn btn-sm btn-outline view-event-btn">
              <i class="fa-solid fa-eye"></i> Details
            </button>
          </div>
        `;

        card.querySelector('.view-event-btn').addEventListener('click', () => openEventModal(ev));
        cardsContainer.appendChild(card);
      });
    });
  }

  // Open Event Modal with rich information
  function openEventModal(ev) {
    if (!calEventModal) return;

    modalEventTitle.innerHTML = `
      <i class="${ev.icon}" style="color: ${ev.theme_color};"></i>
      <span>${escapeHtml(ev.type_display)}: ${escapeHtml(ev.title)}</span>
    `;

    // Google Calendar URL generator
    const googleCalUrl = createGoogleCalendarLink(ev);

    modalEventBody.innerHTML = `
      <div style="background: var(--bg-subtle); padding: 1rem 1.25rem; border-radius: var(--radius-md); margin-bottom: 1.25rem; border-left: 4px solid ${ev.theme_color};">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.5rem;">
          <div>
            <span style="font-size: 0.75rem; text-transform: uppercase; font-weight: 700; color: var(--text-muted); letter-spacing: 0.05em;">Booking Reference / PNR</span>
            <div style="font-size: 1.25rem; font-weight: 800; color: var(--secondary); letter-spacing: 0.05em;">${escapeHtml(ev.ref)}</div>
          </div>
          <span class="badge ${ev.badge_class}" style="font-size: 0.8rem; padding: 0.35rem 0.75rem; font-weight: 700;">
            ${escapeHtml(ev.status_display)}
          </span>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.25rem;">
        <div>
          <label style="font-size: 0.75rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase;">Date & Time</label>
          <div style="font-weight: 600; color: var(--secondary); font-size: 0.95rem;">
            <i class="fa-regular fa-calendar" style="color: var(--primary);"></i> ${escapeHtml(ev.date)}
          </div>
          <div style="font-size: 0.85rem; color: var(--text-muted);">
            <i class="fa-regular fa-clock"></i> Departure / Start: ${escapeHtml(ev.time)}
          </div>
        </div>
        <div>
          <label style="font-size: 0.75rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase;">Seats / Rooms</label>
          <div style="font-weight: 600; color: var(--secondary); font-size: 0.95rem;">
            ${escapeHtml(ev.seats)}
          </div>
          <div style="font-size: 0.85rem; color: var(--text-muted);">
            Class: ${escapeHtml(ev.travel_class || 'Standard')}
          </div>
        </div>
      </div>

      <div style="margin-bottom: 1.25rem; padding-bottom: 1.25rem; border-bottom: 1px solid var(--border);">
        <label style="font-size: 0.75rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase;">Journey Route / Location</label>
        <div style="font-weight: 700; color: var(--secondary); font-size: 1.05rem; margin-top: 0.2rem;">
          ${escapeHtml(ev.origin)} &rarr; ${escapeHtml(ev.destination)}
        </div>
      </div>

      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem;">
        <div>
          <label style="font-size: 0.75rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase;">Passengers / Guests</label>
          <div style="font-weight: 600; color: var(--secondary); font-size: 0.9rem;">
            ${escapeHtml((ev.passengers || []).join(', '))}
          </div>
        </div>
        <div style="text-align: right;">
          <label style="font-size: 0.75rem; color: var(--text-muted); font-weight: 700; text-transform: uppercase;">Total Paid</label>
          <div style="font-size: 1.2rem; font-weight: 800; color: #046a38;">
            ₹${ev.fare.toFixed(2)}
          </div>
        </div>
      </div>

      <!-- Quick Add to Google Calendar -->
      <div style="margin-top: 1rem;">
        <a href="${googleCalUrl}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-outline" style="width: 100%; justify-content: center; gap: 0.5rem; font-size: 0.85rem;">
          <i class="fa-brands fa-google"></i> Add to Google Calendar
        </a>
      </div>
    `;

    modalActionTicketBtn.href = ev.url;
    modalActionTicketBtn.style.display = 'inline-flex';

    calEventModal.classList.add('active');
  }

  // Open multi-events modal on busy day
  function openDayEventsModal(dateStr, eventsList) {
    if (!calEventModal) return;

    modalEventTitle.innerHTML = `
      <i class="fa-regular fa-calendar-check" style="color: var(--primary);"></i>
      <span>Bookings for ${dateStr}</span>
    `;

    let html = `<div style="display: flex; flex-direction: column; gap: 0.75rem;">`;
    eventsList.forEach(ev => {
      html += `
        <div style="background: #ffffff; border: 1px solid var(--border); border-left: 4px solid ${ev.theme_color}; border-radius: var(--radius-md); padding: 0.85rem 1rem; cursor: pointer; transition: all 0.2s;" class="multi-event-row" data-ev-id="${ev.id}">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="display: flex; align-items: center; gap: 0.6rem;">
              <i class="${ev.icon}" style="color: ${ev.theme_color};"></i>
              <strong style="color: var(--secondary); font-size: 0.95rem;">${escapeHtml(ev.title)}</strong>
            </div>
            <span class="badge ${ev.badge_class}" style="font-size: 0.72rem;">${escapeHtml(ev.status_display)}</span>
          </div>
          <div style="font-size: 0.82rem; color: var(--text-muted); margin-top: 0.3rem;">
            ${escapeHtml(ev.time)} &bull; ${escapeHtml(ev.route_display)} &bull; Seats: ${escapeHtml(ev.seats)}
          </div>
        </div>
      `;
    });
    html += `</div>`;

    modalEventBody.innerHTML = html;
    modalActionTicketBtn.style.display = 'none';

    modalEventBody.querySelectorAll('.multi-event-row').forEach((row, idx) => {
      row.addEventListener('click', () => {
        openEventModal(eventsList[idx]);
      });
    });

    calEventModal.classList.add('active');
  }

  function closeEventModal() {
    if (calEventModal) {
      calEventModal.classList.remove('active');
    }
  }

  if (closeCalModalBtn) closeCalModalBtn.addEventListener('click', closeEventModal);
  if (modalCloseActionBtn) modalCloseActionBtn.addEventListener('click', closeEventModal);
  if (calEventModal) {
    calEventModal.addEventListener('click', (e) => {
      if (e.target === calEventModal) closeEventModal();
    });
  }

  // Google Calendar Link Builder
  function createGoogleCalendarLink(ev) {
    const title = encodeURIComponent(`${ev.type_display}: ${ev.title} (${ev.ref})`);
    const details = encodeURIComponent(`Booking Ref: ${ev.ref}\nRoute: ${ev.route_display}\nSeats/Rooms: ${ev.seats}\nPassenger(s): ${(ev.passengers || []).join(', ')}\nStatus: ${ev.status_display}\nPortal: RailAway`);
    const location = encodeURIComponent(ev.route_display || 'India');

    let dtStart = ev.date.replace(/-/g, '') + 'T090000Z';
    let dtEnd = ev.date.replace(/-/g, '') + 'T120000Z';

    return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&details=${details}&location=${location}&dates=${dtStart}/${dtEnd}`;
  }

  // Helper Escape HTML
  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Navigation handlers
  if (calPrevMonthBtn) {
    calPrevMonthBtn.addEventListener('click', () => {
      currentMonth--;
      if (currentMonth < 0) {
        currentMonth = 11;
        currentYear--;
      }
      renderCalendar();
    });
  }

  if (calNextMonthBtn) {
    calNextMonthBtn.addEventListener('click', () => {
      currentMonth++;
      if (currentMonth > 11) {
        currentMonth = 0;
        currentYear++;
      }
      renderCalendar();
    });
  }

  if (calTodayBtn) {
    calTodayBtn.addEventListener('click', () => {
      currentYear = today.getFullYear();
      currentMonth = today.getMonth();
      renderCalendar();
    });
  }

  // Filter Pill buttons
  filterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      filterPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      activeFilter = pill.getAttribute('data-filter') || 'ALL';
      renderCalendar();
    });
  });

  // Status Select
  if (calStatusSelect) {
    calStatusSelect.addEventListener('change', (e) => {
      activeStatus = e.target.value;
      renderCalendar();
    });
  }

  // View Switcher (Month / Agenda)
  viewTabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      viewTabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeView = btn.getAttribute('data-view') || 'month';

      if (activeView === 'month') {
        if (monthViewContainer) monthViewContainer.style.display = 'block';
        if (timelineViewContainer) timelineViewContainer.style.display = 'none';
      } else {
        if (monthViewContainer) monthViewContainer.style.display = 'none';
        if (timelineViewContainer) timelineViewContainer.style.display = 'block';
      }
    });
  });

  // Countdown timer for next upcoming trip banner
  const nextTripCountdownElem = document.getElementById('nextTripCountdown');
  if (nextTripCountdownElem) {
    const evDateStr = nextTripCountdownElem.getAttribute('data-event-date');
    const evTimeStr = nextTripCountdownElem.getAttribute('data-event-time') || '09:00';

    function updateCountdown() {
      try {
        let hours = 9, minutes = 0;
        if (evTimeStr.includes(':')) {
          const parts = evTimeStr.split(':');
          hours = parseInt(parts[0], 10);
          minutes = parseInt(parts[1], 10);
        }
        const targetDate = new Date(`${evDateStr}T${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:00`);
        const now = new Date();
        const diffMs = targetDate - now;

        if (diffMs <= 0) {
          nextTripCountdownElem.innerHTML = `<i class="fa-solid fa-flag-checkered"></i> Travel Date Reached`;
          nextTripCountdownElem.className = 'badge badge-success';
          return;
        }

        const days = Math.floor(diffMs / (1000 * 60 * 60 * 24));
        const hrs = Math.floor((diffMs % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const mins = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

        let text = `Departing in `;
        if (days > 0) text += `${days}d `;
        text += `${hrs}h ${mins}m`;

        nextTripCountdownElem.innerHTML = `<i class="fa-solid fa-clock"></i> ${text}`;
      } catch (err) {
        nextTripCountdownElem.style.display = 'none';
      }
    }

    updateCountdown();
    setInterval(updateCountdown, 60000);
  }

  // Initial render
  renderCalendar();
});
