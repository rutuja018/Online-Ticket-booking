/**
 * Multi-Modal Search Tab Switching (Train, Flight, Bus)
 */
document.addEventListener('DOMContentLoaded', () => {
  const tabButtons = document.querySelectorAll('.search-tabs .tab-btn');
  const tabContents = document.querySelectorAll('.search-widget .tab-content');

  if (tabButtons.length > 0) {
    tabButtons.forEach(button => {
      button.addEventListener('click', () => {
        const targetTabId = button.getAttribute('data-tab');

        // Remove active class from all buttons and contents
        tabButtons.forEach(b => b.classList.remove('active'));
        tabContents.forEach(c => c.classList.remove('active'));

        // Activate clicked tab
        button.classList.add('active');
        const targetContent = document.getElementById(targetTabId);
        if (targetContent) {
          targetContent.classList.add('active');
        }
      });
    });
  }

  // Round-trip radio toggler for flight search
  const tripTypeRadios = document.querySelectorAll('input[name="trip_type"]');
  const returnDateGroup = document.getElementById('returnDateGroup');
  if (tripTypeRadios.length > 0 && returnDateGroup) {
    tripTypeRadios.forEach(radio => {
      radio.addEventListener('change', () => {
        if (radio.value === 'roundtrip') {
          returnDateGroup.style.display = 'block';
          const returnInput = returnDateGroup.querySelector('input');
          if (returnInput) returnInput.required = true;
        } else {
          returnDateGroup.style.display = 'none';
          const returnInput = returnDateGroup.querySelector('input');
          if (returnInput) returnInput.required = false;
        }
      });
    });
  }
});
