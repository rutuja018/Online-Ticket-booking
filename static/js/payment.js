/**
 * Demo Payment Gateway JavaScript
 * Handles Payment Method Tabs (Card, UPI, NetBanking) and Live Formatting
 */
document.addEventListener('DOMContentLoaded', () => {
  const methodRadios = document.querySelectorAll('input[name="payment_method"]');
  const methodSections = document.querySelectorAll('.payment-method-section');

  if (methodRadios.length > 0) {
    methodRadios.forEach(radio => {
      radio.addEventListener('change', () => {
        const selectedMethod = radio.value;
        methodSections.forEach(section => {
          if (section.id === `section_${selectedMethod}`) {
            section.style.display = 'block';
          } else {
            section.style.display = 'none';
          }
        });
      });
    });
  }

  // Card Number live formatting (4-4-4-4)
  const cardInput = document.getElementById('cardNumberInput');
  if (cardInput) {
    cardInput.addEventListener('input', (e) => {
      let val = e.target.value.replace(/\D/g, '');
      val = val.substring(0, 16);
      const parts = val.match(/.{1,4}/g);
      e.target.value = parts ? parts.join(' ') : '';
    });
  }

  // Card Expiry live formatting (MM/YY)
  const expInput = document.getElementById('cardExpiryInput');
  if (expInput) {
    expInput.addEventListener('input', (e) => {
      let val = e.target.value.replace(/\D/g, '');
      val = val.substring(0, 4);
      if (val.length >= 2) {
        e.target.value = `${val.substring(0, 2)}/${val.substring(2)}`;
      } else {
        e.target.value = val;
      }
    });
  }
});
