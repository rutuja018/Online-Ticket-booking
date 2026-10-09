/**
 * RailAway — Global JavaScript Utilities
 */

// ==========================================================================
// Global OTP Timers and Helpers
// ==========================================================================
const otpTimers = {};

function getTimerObj(scope) {
  if (!otpTimers[scope]) {
    otpTimers[scope] = { expiry: null, cooldown: null };
  }
  return otpTimers[scope];
}

// Helper to retrieve CSRF token
function getCsrfToken() {
  const csrfInput = document.querySelector('input[name="csrfmiddlewaretoken"]');
  if (csrfInput) return csrfInput.value;
  const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
  return cookie ? cookie.split('=')[1] : '';
}

// Helper to show OTP status message
function setOtpStatus(scope, message, type) {
  const alertBox = document.getElementById(`${scope}OtpStatus`);
  if (!alertBox) return;
  if (!message) {
    alertBox.style.display = 'none';
    alertBox.className = 'irctc-status-alert';
    alertBox.textContent = '';
    return;
  }
  alertBox.className = `irctc-status-alert ${type}`;
  alertBox.textContent = message;
  alertBox.style.display = 'block';
}

// 1. Send / Resend OTP Action
window.sendAuthOtp = async function(scope, purpose = 'auth') {
  const emailInput = document.getElementById(`${scope}OtpEmail`) || document.getElementById('regEmailInput') || document.querySelector('input[name="email"]');
  const email = emailInput ? emailInput.value.trim() : '';
  const sendBtn = document.getElementById(`${scope}SendOtpBtn`);
  const resendBtn = document.getElementById(`${scope}ResendOtpBtn`);
  const otpSection = document.getElementById(`${scope}OtpInputSection`);
  const otpCodeInput = document.getElementById(`${scope}OtpCode`);
  const badgeStatus = document.getElementById(`${scope}EmailBadgeStatus`);

  if (!email || !email.includes('@') || !email.includes('.')) {
    setOtpStatus(scope, 'Please enter a valid email address first.', 'error');
    if (emailInput) emailInput.focus();
    return;
  }

  // Set sending state
  if (sendBtn) {
    sendBtn.disabled = true;
    sendBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sending OTP...';
  }
  if (resendBtn) resendBtn.disabled = true;
  if (badgeStatus) {
    badgeStatus.style.color = '#0284C7';
    badgeStatus.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sending OTP...';
  }
  setOtpStatus(scope, '', '');

  try {
    const formData = new FormData();
    formData.append('email', email);
    formData.append('purpose', purpose);
    formData.append('csrfmiddlewaretoken', getCsrfToken());

    const response = await fetch('/accounts/send-otp/', {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    });

    const data = await response.json();

    if (response.ok && data.success) {
      setOtpStatus(scope, data.message || `A 6-digit OTP has been sent to ${email}.`, 'success');

      // Update badge status
      if (badgeStatus) {
        badgeStatus.style.color = '#F59E0B';
        badgeStatus.innerHTML = '<i class="fa-solid fa-key"></i> OTP Sent — Enter Below';
      }

      // Keep email field visible, reveal OTP section below it
      if (otpSection) {
        otpSection.style.display = 'block';
      }
      if (sendBtn) {
        sendBtn.disabled = true;
        sendBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> OTP Sent';
      }
      if (otpCodeInput) {
        if (data.otp_hint && !data.email_sent) {
          otpCodeInput.value = data.otp_hint;
        } else {
          otpCodeInput.value = '';
        }
        setTimeout(() => otpCodeInput.focus(), 150);
      }

      // Start 2-Minute Expiry Countdown (120s)
      startOtpExpiryCountdown(scope, data.expiry_seconds || 120);

      // Start Resend Cooldown (30s)
      startResendCooldown(scope, data.cooldown_seconds || 30);
    } else {
      setOtpStatus(scope, data.error || 'Failed to send OTP. Please try again.', 'error');
      if (sendBtn) {
        sendBtn.disabled = false;
        sendBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Verify via OTP';
      }
      if (resendBtn) resendBtn.disabled = false;
      if (badgeStatus) {
        badgeStatus.style.color = '#DC2626';
        badgeStatus.innerHTML = '<i class="fa-solid fa-circle-exclamation"></i> Verification Failed';
      }
    }
  } catch (err) {
    setOtpStatus(scope, 'Network error. Please check your connection and try again.', 'error');
    if (sendBtn) {
      sendBtn.disabled = false;
      sendBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Verify via OTP';
    }
    if (resendBtn) resendBtn.disabled = false;
  }
};

// 2. Verify Registration Email OTP Action (In-line verification for Registration Form)
window.verifyRegistrationOtp = async function(scope = 'reg') {
  const emailInput = document.getElementById(`${scope}OtpEmail`) || document.getElementById('regEmailInput') || document.querySelector('input[name="email"]');
  const email = emailInput ? emailInput.value.trim() : '';
  const otpInput = document.getElementById(`${scope}OtpCode`);
  const otp = otpInput ? otpInput.value.trim() : '';
  const verifyBtn = document.getElementById(`${scope}VerifyOtpBtn`);
  const sendBtn = document.getElementById(`${scope}SendOtpBtn`);
  const otpSection = document.getElementById(`${scope}OtpInputSection`);
  const hiddenOtpField = document.getElementById('hiddenEmailOtp');
  const hiddenVerifiedField = document.getElementById('isEmailVerifiedHidden');
  const registerSubmitBtn = document.getElementById('registerSubmitBtn');
  const badgeStatus = document.getElementById(`${scope}EmailBadgeStatus`);
  const editEmailBtn = document.getElementById(`${scope}EditEmailBtn`);

  if (!otp || otp.length !== 6 || !/^\d{6}$/.test(otp)) {
    setOtpStatus(scope, 'Please enter the 6-digit OTP code received in your email.', 'error');
    if (otpInput) otpInput.focus();
    return;
  }

  if (verifyBtn) {
    verifyBtn.disabled = true;
    verifyBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Verifying...';
  }
  setOtpStatus(scope, '', '');

  try {
    const formData = new FormData();
    formData.append('email', email);
    formData.append('otp', otp);
    formData.append('action', 'verify_only');
    formData.append('csrfmiddlewaretoken', getCsrfToken());

    const response = await fetch('/accounts/verify-otp/', {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    });

    const data = await response.json();

    if (response.ok && data.success) {
      const timers = getTimerObj(scope);
      if (timers.expiry) clearInterval(timers.expiry);
      if (timers.cooldown) clearInterval(timers.cooldown);

      // Set global verified flags
      window.isEmailOtpVerified = true;
      if (hiddenVerifiedField) hiddenVerifiedField.value = '1';
      if (hiddenOtpField) hiddenOtpField.value = otp;

      setOtpStatus(scope, 'Email Verified Successfully! ✅ You can now create your account.', 'success');

      // Hide OTP input section
      if (otpSection) otpSection.style.display = 'none';

      // Update badge status above input
      if (badgeStatus) {
        badgeStatus.style.color = '#059669';
        badgeStatus.innerHTML = '<i class="fa-solid fa-circle-check"></i> Email OTP Verified ✅';
      }

      // Style the email input box as verified
      if (emailInput) {
        emailInput.readOnly = true;
        emailInput.style.backgroundColor = '#F0FDF4';
        emailInput.style.borderColor = '#10B981';
        emailInput.style.color = '#065F46';
        emailInput.style.fontWeight = '700';
      }

      // Change Send button to "Verified"
      if (sendBtn) {
        sendBtn.disabled = true;
        sendBtn.style.background = 'linear-gradient(135deg, #10B981 0%, #059669 100%)';
        sendBtn.innerHTML = '<i class="fa-solid fa-circle-check"></i> Verified';
      }

      // Reveal edit email button if present
      if (editEmailBtn) {
        editEmailBtn.style.display = 'inline-flex';
      }

      // Enable submit button
      if (registerSubmitBtn) {
        registerSubmitBtn.disabled = false;
        registerSubmitBtn.classList.add('pulse-glow');
      }
    } else {
      if (verifyBtn) {
        verifyBtn.disabled = false;
        verifyBtn.innerHTML = '<i class="fa-solid fa-circle-check"></i> Verify OTP';
      }

      if (data.expired) {
        setOtpStatus(scope, data.error || 'OTP expired. Please request a new OTP.', 'warning');
        const timerDisplay = document.getElementById(`${scope}OtpTimer`);
        if (timerDisplay) timerDisplay.classList.add('expired');
        const resendBtn = document.getElementById(`${scope}ResendOtpBtn`);
        if (resendBtn) resendBtn.disabled = false;
      } else {
        setOtpStatus(scope, data.error || 'Invalid OTP code. Please check your email and try again.', 'error');
        if (otpInput) {
          otpInput.focus();
          otpInput.select();
        }
      }
    }
  } catch (err) {
    if (verifyBtn) {
      verifyBtn.disabled = false;
      verifyBtn.innerHTML = '<i class="fa-solid fa-circle-check"></i> Verify OTP';
    }
    setOtpStatus(scope, 'Network error. Please try again.', 'error');
  }
};

// 3. Reset Registration Email Verification
window.resetRegistrationEmail = function(scope = 'reg') {
  const timers = getTimerObj(scope);
  if (timers.expiry) clearInterval(timers.expiry);
  if (timers.cooldown) clearInterval(timers.cooldown);

  window.isEmailOtpVerified = false;

  const emailInput = document.getElementById(`${scope}OtpEmail`) || document.getElementById('regEmailInput') || document.querySelector('input[name="email"]');
  const otpSection = document.getElementById(`${scope}OtpInputSection`);
  const sendBtn = document.getElementById(`${scope}SendOtpBtn`);
  const resendBtn = document.getElementById(`${scope}ResendOtpBtn`);
  const hiddenOtpField = document.getElementById('hiddenEmailOtp');
  const hiddenVerifiedField = document.getElementById('isEmailVerifiedHidden');
  const badgeStatus = document.getElementById(`${scope}EmailBadgeStatus`);
  const editEmailBtn = document.getElementById(`${scope}EditEmailBtn`);

  if (emailInput) {
    emailInput.readOnly = false;
    emailInput.style.backgroundColor = '#FFFFFF';
    emailInput.style.borderColor = '#CBD5E1';
    emailInput.style.color = '#0F172A';
    emailInput.style.fontWeight = 'normal';
    emailInput.focus();
  }
  if (otpSection) otpSection.style.display = 'none';
  if (sendBtn) {
    sendBtn.disabled = false;
    sendBtn.style.background = 'linear-gradient(135deg, #0284C7 0%, #0369A1 100%)';
    sendBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Verify via OTP';
  }
  if (resendBtn) resendBtn.disabled = true;
  if (hiddenOtpField) hiddenOtpField.value = '';
  if (hiddenVerifiedField) hiddenVerifiedField.value = '0';
  if (editEmailBtn) editEmailBtn.style.display = 'none';

  if (badgeStatus) {
    badgeStatus.style.color = '#D97706';
    badgeStatus.innerHTML = '<i class="fa-solid fa-circle-exclamation"></i> Verification Required';
  }

  setOtpStatus(scope, '', '');
};

// 4. Verify Standard Login / Quick OTP Action
window.verifyAuthOtp = async function(scope) {
  const emailInput = document.getElementById(`${scope}OtpEmail`);
  const email = emailInput ? emailInput.value.trim() : '';
  const otpInput = document.getElementById(`${scope}OtpCode`);
  const otp = otpInput ? otpInput.value.trim() : '';
  const verifyBtn = document.getElementById(`${scope}VerifyOtpBtn`);
  const nextInput = document.getElementById(`${scope}OtpNext`);
  const nextUrl = nextInput ? nextInput.value : '/accounts/dashboard/';

  if (!otp || otp.length !== 6 || !/^\d{6}$/.test(otp)) {
    setOtpStatus(scope, 'Please enter a valid 6-digit OTP code.', 'error');
    if (otpInput) otpInput.focus();
    return;
  }

  if (verifyBtn) {
    verifyBtn.disabled = true;
    verifyBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Verifying...';
  }
  setOtpStatus(scope, '', '');

  try {
    const formData = new FormData();
    formData.append('email', email);
    formData.append('otp', otp);
    formData.append('next', nextUrl);
    formData.append('csrfmiddlewaretoken', getCsrfToken());

    const response = await fetch('/accounts/verify-otp/', {
      method: 'POST',
      body: formData,
      headers: {
        'X-Requested-With': 'XMLHttpRequest'
      }
    });

    const data = await response.json();

    if (response.ok && data.success) {
      const timers = getTimerObj(scope);
      if (timers.expiry) clearInterval(timers.expiry);
      if (timers.cooldown) clearInterval(timers.cooldown);

      setOtpStatus(scope, 'OTP Verified! Redirecting...', 'success');
      if (verifyBtn) {
        verifyBtn.innerHTML = '<i class="fa-solid fa-check"></i> Success!';
      }

      setTimeout(() => {
        window.location.href = data.redirect_url || '/accounts/dashboard/';
      }, 500);
    } else {
      if (verifyBtn) {
        verifyBtn.disabled = false;
        verifyBtn.textContent = 'Verify & Continue';
      }

      if (data.expired) {
        setOtpStatus(scope, data.error || 'OTP expired. Please request a new OTP.', 'warning');
        const timerDisplay = document.getElementById(`${scope}OtpTimer`);
        if (timerDisplay) timerDisplay.classList.add('expired');
        const resendBtn = document.getElementById(`${scope}ResendOtpBtn`);
        if (resendBtn) resendBtn.disabled = false;
      } else {
        setOtpStatus(scope, data.error || 'Invalid OTP. Please check your email and try again.', 'error');
        if (otpInput) {
          otpInput.focus();
          otpInput.select();
        }
      }
    }
  } catch (err) {
    if (verifyBtn) {
      verifyBtn.disabled = false;
      verifyBtn.textContent = 'Verify & Continue';
    }
    setOtpStatus(scope, 'Network error. Please try again.', 'error');
  }
};

// 5. Reset OTP Form to change email
window.resetOtpSection = function(scope) {
  const timers = getTimerObj(scope);
  if (timers.expiry) clearInterval(timers.expiry);
  if (timers.cooldown) clearInterval(timers.cooldown);

  const emailSection = document.getElementById(`${scope}EmailSection`);
  const otpSection = document.getElementById(`${scope}OtpInputSection`);
  const emailInput = document.getElementById(`${scope}OtpEmail`);
  const sendBtn = document.getElementById(`${scope}SendOtpBtn`);
  const resendBtn = document.getElementById(`${scope}ResendOtpBtn`);
  const cooldownText = document.getElementById(`${scope}CooldownText`);

  if (emailSection) emailSection.style.display = 'block';
  if (otpSection) otpSection.style.display = 'none';
  if (sendBtn) {
    sendBtn.disabled = false;
    sendBtn.textContent = 'Send OTP';
  }
  if (resendBtn) resendBtn.disabled = true;
  if (cooldownText) cooldownText.textContent = '';
  if (emailInput) {
    emailInput.disabled = false;
    emailInput.focus();
  }
  setOtpStatus(scope, '', '');
};

// 6. Expiry Countdown Helper (2 minutes / 120 seconds)
function startOtpExpiryCountdown(scope, totalSeconds) {
  const timers = getTimerObj(scope);
  if (timers.expiry) clearInterval(timers.expiry);

  const timerCount = document.getElementById(`${scope}OtpTimerCount`);
  const timerBox = document.getElementById(`${scope}OtpTimer`);
  if (timerBox) timerBox.classList.remove('expired');

  let remaining = totalSeconds;

  function updateDisplay() {
    const minutes = Math.floor(remaining / 60);
    const seconds = remaining % 60;
    if (timerCount) {
      timerCount.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }

    if (remaining <= 0) {
      clearInterval(timers.expiry);
      if (timerBox) timerBox.classList.add('expired');
      if (timerCount) timerCount.textContent = '00:00 (Expired)';
      setOtpStatus(scope, 'OTP has expired. Please click Resend OTP to request a new code.', 'warning');
      const resendBtn = document.getElementById(`${scope}ResendOtpBtn`);
      if (resendBtn) resendBtn.disabled = false;
    }
    remaining--;
  }

  updateDisplay();
  timers.expiry = setInterval(updateDisplay, 1000);
}

// 7. Resend Cooldown Countdown Helper (30 seconds)
function startResendCooldown(scope, cooldownSeconds) {
  const timers = getTimerObj(scope);
  if (timers.cooldown) clearInterval(timers.cooldown);

  const resendBtn = document.getElementById(`${scope}ResendOtpBtn`);
  const cooldownText = document.getElementById(`${scope}CooldownText`);
  if (resendBtn) resendBtn.disabled = true;

  let remaining = cooldownSeconds;

  function updateCooldown() {
    if (remaining > 0) {
      if (cooldownText) cooldownText.textContent = `(${remaining}s)`;
      remaining--;
    } else {
      clearInterval(timers.cooldown);
      if (cooldownText) cooldownText.textContent = '';
      if (resendBtn) resendBtn.disabled = false;
    }
  }

  updateCooldown();
  timers.cooldown = setInterval(updateCooldown, 1000);
}

// ==========================================================================
// DOM Initialization & Event Handlers
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
  // 1. Auto-dismiss flash alerts after 6 seconds
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 250);
      });
    }

    setTimeout(() => {
      if (alert && alert.parentElement) {
        alert.style.transition = 'opacity 0.5s ease';
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 500);
      }
    }, 6000);
  });

  // 2. Date input min attribute protection
  const dateInputs = document.querySelectorAll('input[type="date"]');
  const todayStr = new Date().toISOString().split('T')[0];
  dateInputs.forEach(input => {
    if (!input.hasAttribute('min')) {
      input.setAttribute('min', todayStr);
    }
  });

  // 3. User dropdown menu
  const userMenuBtn = document.querySelector('#userMenuButton');
  const userDropdown = document.querySelector('#userDropdownMenu');
  if (userMenuBtn && userDropdown) {
    userMenuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      userDropdown.classList.toggle('show');
    });

    document.addEventListener('click', () => {
      userDropdown.classList.remove('show');
    });
  }

  // 4. IRCTC-Style Login Modal Controller
  const irctcModal = document.getElementById('irctcLoginModal');
  const modalCloseBtn = document.getElementById('irctcModalCloseBtn');
  const navLoginBtn = document.getElementById('navLoginBtn');

  window.openIrctcLoginModal = function(targetTab) {
    if (!irctcModal) return;
    irctcModal.classList.add('active');
    irctcModal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';

    if (targetTab) {
      window.switchIrctcTab(targetTab);
    }

    setTimeout(() => {
      const activePanel = irctcModal.querySelector('.irctc-tab-panel.active');
      if (activePanel) {
        const input = activePanel.querySelector('input:not([type="hidden"])');
        if (input) input.focus();
      }
    }, 150);
  };

  window.closeIrctcLoginModal = function() {
    if (!irctcModal) return;
    irctcModal.classList.remove('active');
    irctcModal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  };

  if (navLoginBtn) {
    navLoginBtn.addEventListener('click', (e) => {
      if (irctcModal && !window.location.pathname.includes('/accounts/login/')) {
        e.preventDefault();
        window.openIrctcLoginModal();
      }
    });
  }

  document.querySelectorAll('[data-open-login-modal]').forEach(el => {
    el.addEventListener('click', (e) => {
      e.preventDefault();
      const tab = el.getAttribute('data-open-login-modal') === 'guest' ? 'irctcGuestFormPanel' : 'irctcLoginFormPanel';
      window.openIrctcLoginModal(tab);
    });
  });

  if (modalCloseBtn) {
    modalCloseBtn.addEventListener('click', () => {
      window.closeIrctcLoginModal();
    });
  }

  if (irctcModal) {
    irctcModal.addEventListener('click', (e) => {
      if (e.target === irctcModal) {
        window.closeIrctcLoginModal();
      }
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && irctcModal && irctcModal.classList.contains('active')) {
      window.closeIrctcLoginModal();
    }
  });

  window.switchIrctcTab = function(targetPanelId) {
    if (!irctcModal) return;
    const tabPills = irctcModal.querySelectorAll('.irctc-tab-pill');
    const panels = irctcModal.querySelectorAll('.irctc-tab-panel');
    const alertBox = document.getElementById('irctcModalAlert');
    if (alertBox) alertBox.style.display = 'none';

    tabPills.forEach(pill => {
      const isTarget = pill.getAttribute('data-target') === targetPanelId;
      pill.classList.toggle('active', isTarget);
      pill.setAttribute('aria-selected', isTarget ? 'true' : 'false');
    });

    panels.forEach(panel => {
      if (panel.id === targetPanelId) {
        panel.style.display = 'block';
        panel.classList.add('active');
        const input = panel.querySelector('input:not([type="hidden"])');
        if (input) input.focus();
      } else {
        panel.style.display = 'none';
        panel.classList.remove('active');
      }
    });
  };

  const pillButtons = irctcModal ? irctcModal.querySelectorAll('.irctc-tab-pill') : [];
  pillButtons.forEach(pill => {
    pill.addEventListener('click', () => {
      const targetId = pill.getAttribute('data-target');
      if (targetId) window.switchIrctcTab(targetId);
    });
  });

  // Enter key listeners inside OTP input fields
  ['page', 'modal', 'reg', 'regQuick'].forEach(scope => {
    const otpInput = document.getElementById(`${scope}OtpCode`);
    if (otpInput) {
      otpInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          if (scope === 'reg') {
            window.verifyRegistrationOtp(scope);
          } else {
            window.verifyAuthOtp(scope);
          }
        }
      });
    }

    const emailInput = document.getElementById(`${scope}OtpEmail`);
    if (emailInput) {
      emailInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          e.preventDefault();
          const purpose = scope.startsWith('reg') ? 'registration' : 'auth';
          window.sendAuthOtp(scope, purpose);
        }
      });
    }
  });
});
