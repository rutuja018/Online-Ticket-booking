/**
 * RailAway — Global Multi-Currency & Multi-Language (i18n) Engine
 * Dynamically converts prices, translates UI elements, and maintains user preferences across all pages.
 */

(function() {
  'use strict';

  // =========================================================================
  // 1. CURRENCY CONVERSION CONFIGURATION & EXCHANGE RATES
  // =========================================================================
  const CURRENCIES = {
    'INR': { code: 'INR', symbol: '₹', name: 'Indian Rupee', flag: '🇮🇳', rate: 1.0, decimals: 2 },
    'USD': { code: 'USD', symbol: '$', name: 'US Dollar', flag: '🇺🇸', rate: 0.012, decimals: 2 },
    'EUR': { code: 'EUR', symbol: '€', name: 'Euro', flag: '🇪🇺', rate: 0.011, decimals: 2 },
    'GBP': { code: 'GBP', symbol: '£', name: 'British Pound', flag: '🇬🇧', rate: 0.0094, decimals: 2 },
    'AED': { code: 'AED', symbol: 'AED ', name: 'UAE Dirham', flag: '🇦🇪', rate: 0.044, decimals: 2 },
    'SGD': { code: 'SGD', symbol: 'S$', name: 'Singapore Dollar', flag: '🇸🇬', rate: 0.016, decimals: 2 },
    'CAD': { code: 'CAD', symbol: 'CA$', name: 'Canadian Dollar', flag: '🇨🇦', rate: 0.016, decimals: 2 },
    'AUD': { code: 'AUD', symbol: 'A$', name: 'Australian Dollar', flag: '🇦🇺', rate: 0.018, decimals: 2 },
    'JPY': { code: 'JPY', symbol: '¥', name: 'Japanese Yen', flag: '🇯🇵', rate: 1.80, decimals: 0 },
    'SAR': { code: 'SAR', symbol: 'SAR ', name: 'Saudi Riyal', flag: '🇸🇦', rate: 0.045, decimals: 2 }
  };

  // =========================================================================
  // 2. MULTI-LANGUAGE DICTIONARY (12 LANGUAGES)
  // =========================================================================
  const LANGUAGES = {
    'en': { code: 'en', name: 'English', flag: '🇬🇧', native: 'English' },
    'hi': { code: 'hi', name: 'Hindi', flag: '🇮🇳', native: 'हिन्दी' },
    'mr': { code: 'mr', name: 'Marathi', flag: '🇮🇳', native: 'मराठी' },
    'ta': { code: 'ta', name: 'Tamil', flag: '🇮🇳', native: 'தமிழ்' },
    'te': { code: 'te', name: 'Telugu', flag: '🇮🇳', native: 'తెలుగు' },
    'bn': { code: 'bn', name: 'Bengali', flag: '🇮🇳', native: 'বাংলা' },
    'gu': { code: 'gu', name: 'Gujarati', flag: '🇮🇳', native: 'ગુજરાતી' },
    'kn': { code: 'kn', name: 'Kannada', flag: '🇮🇳', native: 'ಕನ್ನಡ' },
    'es': { code: 'es', name: 'Spanish', flag: '🇪🇸', native: 'Español' },
    'fr': { code: 'fr', name: 'French', flag: '🇫🇷', native: 'Français' },
    'ar': { code: 'ar', name: 'Arabic', flag: '🇸🇦', native: 'العربية' },
    'de': { code: 'de', name: 'German', flag: '🇩🇪', native: 'Deutsch' }
  };

  const TRANSLATIONS = {
    'hi': {
      'Home': 'होम',
      'Trains': 'ट्रेनें',
      'Flights': 'उड़ानें',
      'Buses': 'बसें',
      'Hotels': 'होटल',
      'Food in Train': 'ट्रेन में खाना',
      'Retiring Rooms': 'विश्राम कक्ष',
      'Reviews': 'समीक्षाएं',
      'My Bookings': 'मेरी बुकिंग',
      'Dashboard': 'डैशबोर्ड',
      'Login': 'लॉग इन',
      'Register': 'रजिस्टर करें',
      'Logout': 'लॉग आउट',
      'Book Another Trip': 'नई यात्रा बुक करें',
      'Booking History': 'बुकिंग इतिहास',
      'All Bookings': 'सभी बुकिंग',
      'Confirmed': 'पुष्ट (Confirmed)',
      'Pending': 'लंबित (Pending)',
      'Cancelled': 'रद्द (Cancelled)',
      'Completed': 'पूर्ण (Completed)',
      'Checked In': 'चेक-इन पूर्ण',
      'PNR / Ref': 'पीएनआर / संदर्भ',
      'Type': 'प्रकार',
      'Service / Hotel': 'सेवा / होटल',
      'Dates & Timings': 'दिनांक व समय',
      'Guests / Seats': 'यात्री / सीटें',
      'Total Amount': 'कुल राशि',
      'Status': 'स्थिति',
      'Actions': 'कार्यवाही',
      'E-Ticket': 'ई-टिकट',
      'Voucher': 'वाउचर',
      'Stay Pass': 'स्टे पास',
      'Track / Bill': 'ट्रैक / बिल',
      'Slip': 'रसीद',
      'Pay Now': 'अभी भुगतान करें',
      'Search': 'खोजें',
      'From': 'कहाँ से',
      'To': 'कहाँ तक',
      'Journey Date': 'यात्रा की तिथि',
      'Departure': 'प्रस्थान',
      'Arrival': 'आगमन',
      'Class': 'श्रेणी',
      'Seats Available': 'सीटें उपलब्ध',
      'Book Now': 'अभी बुक करें',
      'Select Seats': 'सीटें चुनें',
      'Cancellation & Refund Policy': 'रद्दकरण व रिफंड नीति',
      'Refund Policy': 'रिफंड नीति',
      'Terms & Conditions': 'नियम व शर्तें',
      'Help & FAQs': 'सहायता व प्रश्न',
      '24x7 Customer Support': '24x7 ग्राहक सहायता',
      'Search Ref, hotel, train, city...': 'संदर्भ, होटल, ट्रेन या शहर खोजें...',
      'Search Ref, hotel, train, city, room...': 'संदर्भ, होटल, ट्रेन, शहर या कमरा खोजें...',
      'Price': 'कीमत',
      'Fare': 'किराया',
      'Tax': 'कर',
      'Discount': 'छूट'
    },
    'mr': {
      'Home': 'मुख्यपृष्ठ',
      'Trains': 'रेल्वे',
      'Flights': 'विमाने',
      'Buses': 'बसेस',
      'Hotels': 'हॉटेल्स',
      'Food in Train': 'गाडीत जेवण',
      'Retiring Rooms': 'विश्राम कक्ष',
      'Reviews': 'अभिप्राय',
      'My Bookings': 'माझी बुकिंग',
      'Dashboard': 'डॅशबोर्ड',
      'Login': 'लॉगिन',
      'Register': 'नोंदणी करा',
      'Logout': 'लॉगआउट',
      'Book Another Trip': 'नवीन प्रवास बुक करा',
      'Booking History': 'बुकिंग इतिहास',
      'All Bookings': 'सर्व बुकिंग',
      'Confirmed': 'निश्चित (Confirmed)',
      'Pending': 'प्रलंबित (Pending)',
      'Cancelled': 'रद्द (Cancelled)',
      'Completed': 'पूर्ण (Completed)',
      'Checked In': 'चेक-इन झाले',
      'PNR / Ref': 'पीएनआर / संदर्भ',
      'Type': 'प्रकार',
      'Service / Hotel': 'सेवा / हॉटेल',
      'Dates & Timings': 'दिनांक आणि वेळ',
      'Guests / Seats': 'प्रवासी / जागा',
      'Total Amount': 'एकूण रक्कम',
      'Status': 'स्थिती',
      'Actions': 'कृती',
      'E-Ticket': 'ई-तिकीट',
      'Voucher': 'व्हाउचर',
      'Stay Pass': 'स्टे पास',
      'Track / Bill': 'ट्रॅक / बिल',
      'Slip': 'पावती',
      'Pay Now': 'आता भरा',
      'Search': 'शोधा',
      'From': 'कुठून',
      'To': 'कुठे',
      'Journey Date': 'प्रवासाची तारीख',
      'Departure': 'सुटण्याची वेळ',
      'Arrival': 'पोहोचण्याची वेळ',
      'Book Now': 'आता बुक करा',
      'Select Seats': 'जागा निवडा',
      'Cancellation & Refund Policy': 'रद्दीकरण व परतावा धोरण',
      'Refund Policy': 'परतावा धोरण',
      'Terms & Conditions': 'नियम व अटी',
      'Help & FAQs': 'मदत आणि प्रश्न',
      '24x7 Customer Support': '२४x७ ग्राहक मदत केंद्र'
    },
    'ta': {
      'Home': 'முகப்பு',
      'Trains': 'ரயில்கள்',
      'Flights': 'விமானங்கள்',
      'Buses': 'பேருந்துகள்',
      'Hotels': 'ஹோட்டல்கள்',
      'Food in Train': 'ரயில் உணவு',
      'Retiring Rooms': 'ஓய்வறைகள்',
      'Reviews': 'மதிப்புரைகள்',
      'My Bookings': 'என் முன்பதிவுகள்',
      'Dashboard': 'டாஷ்போர்டு',
      'Login': 'உள்நுழைக',
      'Register': 'பதிவு செய்க',
      'Logout': 'வெளியேறு',
      'Book Another Trip': 'புதிய பயணம் பதிவு செய்',
      'Booking History': 'முன்பதிவு வரலாறு',
      'All Bookings': 'அனைத்து முன்பதிவுகள்',
      'Confirmed': 'உறுதியானது',
      'Pending': 'நிலுவையில்',
      'Cancelled': 'ரத்து செய்யப்பட்டது',
      'Completed': 'முடிந்தது',
      'E-Ticket': 'இ-டிக்கெட்',
      'Voucher': 'ரசீது',
      'Stay Pass': 'தங்கும் அனுமதி',
      'Track / Bill': 'ட்ராக் / பில்',
      'Pay Now': 'செலுத்துங்கள்',
      'Cancellation & Refund Policy': 'ரத்து மற்றும் பணத்தைத் திரும்பப் பெறும் கொள்கை',
      'Refund Policy': 'ரீஃபண்ட் கொள்கை',
      '24x7 Customer Support': '24x7 வாடிக்கையாளர் சேவை'
    },
    'te': {
      'Home': 'హోమ్',
      'Trains': 'రైళ్లు',
      'Flights': 'విమానాలు',
      'Buses': 'బస్సులు',
      'Hotels': 'హోటళ్ళు',
      'Food in Train': 'రైలులో భోజనం',
      'Retiring Rooms': 'విశ్రాంతి గదులు',
      'Reviews': 'సమీక్షలు',
      'My Bookings': 'నా బుకింగ్స్',
      'Dashboard': 'డాష్‌బోర్డ్',
      'Login': 'లాగిన్',
      'Register': 'నమోదు',
      'Logout': 'లాగ్అవుట్',
      'Booking History': 'బుకింగ్ చరిత్ర',
      'All Bookings': 'అన్ని బుకింగ్‌లు',
      'Confirmed': 'ధృవీకరించబడింది',
      'Pending': 'పెండింగ్‌లో ఉంది',
      'Cancelled': 'రద్దు చేయబడింది',
      'E-Ticket': 'ఇ-టికెట్',
      'Stay Pass': 'స్టే పాస్',
      'Track / Bill': 'ట్రాక్ / బిల్',
      'Pay Now': 'ఇప్పుడే చెల్లించండి',
      'Cancellation & Refund Policy': 'రద్దు & వాపసు విధానం',
      'Refund Policy': 'రీఫండ్ పాలసీ'
    },
    'bn': {
      'Home': 'হোম',
      'Trains': 'ট্রেন',
      'Flights': 'বিমান',
      'Buses': 'বাস',
      'Hotels': 'হোটেল',
      'Food in Train': 'ট্রেনে খাবার',
      'Retiring Rooms': 'বিশ্রামাগার',
      'Reviews': 'পর্যালোচনা',
      'My Bookings': 'আমার বুকিং',
      'Dashboard': 'ড্যাশবোর্ড',
      'Login': 'লগইন',
      'Register': 'নিবন্ধন',
      'Logout': 'লগআউট',
      'Booking History': 'বুকিং ইতিহাস',
      'All Bookings': 'সকল বুকিং',
      'Confirmed': 'নিশ্চিত',
      'Pending': 'অপেক্ষারত',
      'Cancelled': 'বাতিল',
      'E-Ticket': 'ই-টিকিট',
      'Stay Pass': 'স্টে পাস',
      'Track / Bill': 'ট্র্যাক / বিল',
      'Pay Now': 'এখনই পরিশোধ করুন',
      'Cancellation & Refund Policy': 'বাতিলকরণ ও ফেরত নীতি',
      'Refund Policy': 'ফেরত নীতি'
    },
    'gu': {
      'Home': 'હોમ',
      'Trains': 'ટ્રેનો',
      'Flights': 'ફ્લાઇટ્સ',
      'Buses': 'બસો',
      'Hotels': 'હોટેલ્સ',
      'Food in Train': 'ટ્રેનમાં ભોજન',
      'Retiring Rooms': 'વિશ્રામ ખંડ',
      'Reviews': 'રિવ્યૂઝ',
      'My Bookings': 'મારી બુકિંગ્સ',
      'Dashboard': 'ડેશબોર્ડ',
      'Login': 'લૉગિન',
      'Register': 'નોંધણી કરો',
      'Logout': 'લૉગઆઉટ',
      'Booking History': 'બુકિંગ ઇતિહાસ',
      'All Bookings': 'બધી બુકિંગ્સ',
      'Confirmed': 'કન્ફર્મ',
      'Pending': 'પેન્ડિંગ',
      'Cancelled': 'રદ થયેલ',
      'E-Ticket': 'ઈ-ટિકિટ',
      'Stay Pass': 'સ્ટે પાસ',
      'Track / Bill': 'ટ્રેક / બિલ',
      'Pay Now': 'હમણાં ચૂકવો',
      'Cancellation & Refund Policy': 'રદ અને રિફંડ નીતિ',
      'Refund Policy': 'રિફંડ નીતિ'
    },
    'kn': {
      'Home': 'ಮುಖಪುಟ',
      'Trains': 'ರೈಲುಗಳು',
      'Flights': 'ವಿಮಾನಗಳು',
      'Buses': 'ಬಸ್‌ಗಳು',
      'Hotels': 'ಹೋಟೆಲ್‌ಗಳು',
      'Food in Train': 'ರೈಲಿನಲ್ಲಿ ಊಟ',
      'Retiring Rooms': 'ವಿಶ್ರಾಂತಿ ಕೊಠಡಿಗಳು',
      'Reviews': 'ವಿಮರ್ಶೆಗಳು',
      'My Bookings': 'ನನ್ನ ಬುಕಿಂಗ್‌ಗಳು',
      'Dashboard': 'ಡ್ಯಾಶ್‌ಬೋರ್ಡ್',
      'Login': 'ಲಾಗಿನ್',
      'Register': 'ನೋಂದಣಿ',
      'Logout': 'ಲಾಗ್‌ಔಟ್',
      'Booking History': 'ಬುಕಿಂಗ್ ಇತಿಹಾಸ',
      'All Bookings': 'ಎಲ್ಲಾ ಬುಕಿಂಗ್‌ಗಳು',
      'Confirmed': 'ದೃಢೀಕರಿಸಲಾಗಿದೆ',
      'Pending': 'ಬಾಕಿ ಉಳಿದಿದೆ',
      'Cancelled': 'ರದ್ದುಗೊಳಿಸಲಾಗಿದೆ',
      'E-Ticket': 'ಇ-ಟಿಕೆಟ್',
      'Stay Pass': 'ಸ್ಟೇ ಪಾಸ್',
      'Track / Bill': 'ಟ್ರ್ಯಾಕ್ / ಬಿಲ್',
      'Pay Now': 'ಈಗ ಪಾವತಿಸಿ',
      'Cancellation & Refund Policy': 'ರದ್ದತಿ ಮತ್ತು ಮರುಪಾವತಿ ನೀತಿ'
    },
    'es': {
      'Home': 'Inicio',
      'Trains': 'Trenes',
      'Flights': 'Vuelos',
      'Buses': 'Autobuses',
      'Hotels': 'Hoteles',
      'Food in Train': 'Comida en Tren',
      'Retiring Rooms': 'Salas de Descanso',
      'Reviews': 'Reseñas',
      'My Bookings': 'Mis Reservas',
      'Dashboard': 'Panel',
      'Login': 'Iniciar sesión',
      'Register': 'Registrarse',
      'Logout': 'Cerrar sesión',
      'Book Another Trip': 'Reservar otro viaje',
      'Booking History': 'Historial de Reservas',
      'All Bookings': 'Todas las reservas',
      'Confirmed': 'Confirmado',
      'Pending': 'Pendiente',
      'Cancelled': 'Cancelado',
      'Completed': 'Completado',
      'PNR / Ref': 'PNR / Ref',
      'Type': 'Tipo',
      'Service / Hotel': 'Servicio / Hotel',
      'Dates & Timings': 'Fechas y Horarios',
      'Guests / Seats': 'Huéspedes / Asientos',
      'Total Amount': 'Monto Total',
      'Status': 'Estado',
      'Actions': 'Acciones',
      'E-Ticket': 'Billete electrónico',
      'Voucher': 'Cupón',
      'Stay Pass': 'Pase de Estancia',
      'Track / Bill': 'Rastrear / Factura',
      'Pay Now': 'Pagar Ahora',
      'Search': 'Buscar',
      'Book Now': 'Reservar Ahora',
      'Cancellation & Refund Policy': 'Política de Cancelación y Reembolso',
      'Refund Policy': 'Política de Reembolso',
      'Terms & Conditions': 'Términos y Condiciones',
      '24x7 Customer Support': 'Atención al Cliente 24x7'
    },
    'fr': {
      'Home': 'Accueil',
      'Trains': 'Trains',
      'Flights': 'Vols',
      'Buses': 'Bus',
      'Hotels': 'Hôtels',
      'Food in Train': 'Repas en Train',
      'Retiring Rooms': 'Salles de Repos',
      'Reviews': 'Avis',
      'My Bookings': 'Mes Réservations',
      'Dashboard': 'Tableau de bord',
      'Login': 'Connexion',
      'Register': 'Inscription',
      'Logout': 'Déconnexion',
      'Book Another Trip': 'Réserver un autre voyage',
      'Booking History': 'Historique des réservations',
      'All Bookings': 'Toutes les réservations',
      'Confirmed': 'Confirmé',
      'Pending': 'En attente',
      'Cancelled': 'Annulé',
      'Completed': 'Terminé',
      'Total Amount': 'Montant Total',
      'Status': 'Statut',
      'Actions': 'Actions',
      'E-Ticket': 'Billet électronique',
      'Voucher': 'Bon de réservation',
      'Stay Pass': 'Pass Séjour',
      'Track / Bill': 'Suivi / Facture',
      'Pay Now': 'Payer Maintenant',
      'Cancellation & Refund Policy': 'Politique d\'annulation et remboursement',
      'Refund Policy': 'Politique de Remboursement'
    },
    'ar': {
      'Home': 'الرئيسية',
      'Trains': 'القطارات',
      'Flights': 'الرحلات الجوية',
      'Buses': 'الحافلات',
      'Hotels': 'الفنادق',
      'Food in Train': 'طعام في القطار',
      'Retiring Rooms': 'غرف الاستراحة',
      'Reviews': 'التقييمات',
      'My Bookings': 'حجوزاتي',
      'Dashboard': 'لوحة التحكم',
      'Login': 'تسجيل الدخول',
      'Register': 'تسجيل جديد',
      'Logout': 'تسجيل الخروج',
      'Booking History': 'سجل الحجوزات',
      'All Bookings': 'جميع الحجوزات',
      'Confirmed': 'مؤكد',
      'Pending': 'قيد الانتظار',
      'Cancelled': 'ملغي',
      'Completed': 'مكتمل',
      'Total Amount': 'المبلغ الإجمالي',
      'Status': 'الحالة',
      'Actions': 'إجراءات',
      'E-Ticket': 'تذكرة إلكترونية',
      'Stay Pass': 'تصريح الإقامة',
      'Track / Bill': 'تتبع / الفاتورة',
      'Pay Now': 'ادفع الآن',
      'Cancellation & Refund Policy': 'سياسة الإلغاء واسترداد الأموال',
      'Refund Policy': 'سياسة الاسترداد'
    },
    'de': {
      'Home': 'Startseite',
      'Trains': 'Züge',
      'Flights': 'Flüge',
      'Buses': 'Busse',
      'Hotels': 'Hotels',
      'Food in Train': 'Essen im Zug',
      'Retiring Rooms': 'Ruheräume',
      'Reviews': 'Bewertungen',
      'My Bookings': 'Meine Buchungen',
      'Dashboard': 'Dashboard',
      'Login': 'Anmelden',
      'Register': 'Registrieren',
      'Logout': 'Abmelden',
      'Booking History': 'Buchungsverlauf',
      'All Bookings': 'Alle Buchungen',
      'Confirmed': 'Bestätigt',
      'Pending': 'Ausstehend',
      'Cancelled': 'Storniert',
      'Completed': 'Abgeschlossen',
      'Total Amount': 'Gesamtbetrag',
      'Status': 'Status',
      'Actions': 'Aktionen',
      'E-Ticket': 'E-Ticket',
      'Stay Pass': 'Aufenthaltspass',
      'Track / Bill': 'Verfolgen / Rechnung',
      'Pay Now': 'Jetzt bezahlen',
      'Cancellation & Refund Policy': 'Stornierungs- & Rückerstattungsrichtlinie',
      'Refund Policy': 'Rückerstattungsrichtlinie'
    }
  };

  // =========================================================================
  // 3. CORE STATE MANAGEMENT
  // =========================================================================
  let currentCurrency = localStorage.getItem('railaway_currency') || 'INR';
  let currentLanguage = localStorage.getItem('railaway_language') || 'en';

  if (!CURRENCIES[currentCurrency]) currentCurrency = 'INR';
  if (!LANGUAGES[currentLanguage]) currentLanguage = 'en';

  // Expose global API
  window.RailAwayI18n = {
    getCurrencies: () => CURRENCIES,
    getLanguages: () => LANGUAGES,
    getCurrentCurrency: () => currentCurrency,
    getCurrentLanguage: () => currentLanguage,
    setCurrency: setCurrency,
    setLanguage: setLanguage,
    formatCurrency: formatCurrency,
    translateText: translateText,
    refreshPageLocalization: refreshPageLocalization
  };

  // =========================================================================
  // 4. CURRENCY CONVERSION ENGINE
  // =========================================================================
  function formatCurrency(amountInINR, targetCurrencyCode = currentCurrency) {
    const curr = CURRENCIES[targetCurrencyCode] || CURRENCIES['INR'];
    const num = parseFloat(amountInINR);
    if (isNaN(num)) return `₹0.00`;

    const converted = num * curr.rate;
    
    // Format based on currency decimal places
    let formattedNum;
    if (curr.decimals === 0) {
      formattedNum = Math.round(converted).toLocaleString('en-US');
    } else {
      formattedNum = converted.toLocaleString('en-US', {
        minimumFractionDigits: curr.decimals,
        maximumFractionDigits: curr.decimals
      });
    }

    return `${curr.symbol}${formattedNum}`;
  }

  function setCurrency(currencyCode) {
    if (!CURRENCIES[currencyCode]) return;
    currentCurrency = currencyCode;
    localStorage.setItem('railaway_currency', currencyCode);
    document.cookie = `railaway_currency=${currencyCode};path=/;max-age=31536000`;
    document.documentElement.setAttribute('data-currency', currencyCode);

    updateNavbarSelectors();
    applyCurrencyConversion();

    // Dispatch custom event for widgets/calculators
    window.dispatchEvent(new CustomEvent('currencyChanged', { detail: { currency: currencyCode } }));
  }

  /**
   * Scans the entire DOM and converts any visible prices.
   * Elements with original values preserve `data-base-inr` so repeated conversions stay exact.
   */
  function applyCurrencyConversion() {
    const curr = CURRENCIES[currentCurrency] || CURRENCIES['INR'];

    // 1. Convert elements already tagged or elements matching price patterns
    const priceNodes = document.querySelectorAll('[data-base-inr]');
    priceNodes.forEach(el => {
      const baseINR = parseFloat(el.getAttribute('data-base-inr'));
      if (!isNaN(baseINR)) {
        el.textContent = formatCurrency(baseINR, currentCurrency);
      }
    });

    // 2. Scan text nodes containing ₹ symbol and tag them with data-base-inr
    const walker = document.createTreeWalker(
      document.body,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode: function(node) {
          if (!node.parentElement) return NodeFilter.FILTER_REJECT;
          const tag = node.parentElement.tagName.toLowerCase();
          if (['script', 'style', 'textarea', 'input', 'select', 'noscript'].includes(tag)) {
            return NodeFilter.FILTER_REJECT;
          }
          if (node.parentElement.hasAttribute('data-base-inr')) {
            return NodeFilter.FILTER_REJECT;
          }
          // Match ₹ currency patterns
          if (/₹\s*[\d,]+(\.\d+)?/.test(node.nodeValue)) {
            return NodeFilter.FILTER_ACCEPT;
          }
          return NodeFilter.FILTER_SKIP;
        }
      }
    );

    const nodesToReplace = [];
    while (walker.nextNode()) {
      nodesToReplace.push(walker.currentNode);
    }

    nodesToReplace.forEach(node => {
      const parent = node.parentElement;
      if (!parent) return;

      const text = node.nodeValue;
      // Replace instances of ₹XXX.XX with <span data-base-inr="XXX.XX">...</span>
      const regex = /₹\s*([\d,]+(\.\d+)?)/g;
      let match;
      let lastIndex = 0;
      const frag = document.createDocumentFragment();
      let matchedAny = false;

      while ((match = regex.exec(text)) !== null) {
        matchedAny = true;
        // Text before match
        if (match.index > lastIndex) {
          frag.appendChild(document.createTextNode(text.substring(lastIndex, match.index)));
        }

        const rawAmount = match[1].replace(/,/g, '');
        const num = parseFloat(rawAmount);

        const span = document.createElement('span');
        span.setAttribute('data-base-inr', num);
        span.className = 'i18n-price';
        span.textContent = formatCurrency(num, currentCurrency);
        frag.appendChild(span);

        lastIndex = regex.lastIndex;
      }

      if (matchedAny) {
        if (lastIndex < text.length) {
          frag.appendChild(document.createTextNode(text.substring(lastIndex)));
        }
        parent.replaceChild(frag, node);
      }
    });
  }

  // =========================================================================
  // 5. LANGUAGE TRANSLATION ENGINE
  // =========================================================================
  function translateText(text, targetLang = currentLanguage) {
    if (targetLang === 'en' || !TRANSLATIONS[targetLang]) return text;
    const clean = text.trim();
    return TRANSLATIONS[targetLang][clean] || text;
  }

  function setLanguage(langCode) {
    if (!LANGUAGES[langCode]) return;
    currentLanguage = langCode;
    localStorage.setItem('railaway_language', langCode);
    document.cookie = `railaway_language=${langCode};path=/;max-age=31536000`;
    document.documentElement.setAttribute('data-lang', langCode);
    document.documentElement.setAttribute('lang', langCode);

    if (langCode === 'ar') {
      document.documentElement.setAttribute('dir', 'rtl');
    } else {
      document.documentElement.removeAttribute('dir');
    }

    updateNavbarSelectors();
    applyLanguageTranslation();

    // Dispatch custom event
    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { language: langCode } }));
  }

  function applyLanguageTranslation() {
    if (currentLanguage === 'en') {
      // Revert to English original texts if stored
      document.querySelectorAll('[data-orig-en]').forEach(el => {
        el.textContent = el.getAttribute('data-orig-en');
      });
      return;
    }

    const dict = TRANSLATIONS[currentLanguage];
    if (!dict) return;

    // Scan interactive text elements: nav links, buttons, table headers, badges, headings
    const elements = document.querySelectorAll('a, button, th, label, .badge, .filter-tab, .action-card span, h1, h2, h3, h4, strong, span');

    elements.forEach(el => {
      // Skip if contains child elements that are not text or icons
      if (el.children.length > 0 && Array.from(el.children).some(c => !c.classList.contains('fa-solid') && !c.classList.contains('fa-regular') && !c.classList.contains('fa-brands') && !c.classList.contains('badge'))) {
        return;
      }

      let originalText = el.getAttribute('data-orig-en');
      if (!originalText) {
        // Extract text while ignoring icon tags
        let textContent = '';
        el.childNodes.forEach(child => {
          if (child.nodeType === Node.TEXT_NODE) {
            textContent += child.nodeValue;
          }
        });
        originalText = textContent.trim();
        if (originalText) {
          el.setAttribute('data-orig-en', originalText);
        }
      }

      if (originalText && dict[originalText]) {
        // Replace text node only, preserving icons
        el.childNodes.forEach(child => {
          if (child.nodeType === Node.TEXT_NODE && child.nodeValue.trim() !== '') {
            child.nodeValue = ' ' + dict[originalText] + ' ';
          }
        });
      }
    });

    // Translate placeholder attributes in inputs
    document.querySelectorAll('input[placeholder]').forEach(input => {
      const origPh = input.getAttribute('data-orig-placeholder') || input.placeholder;
      if (!input.getAttribute('data-orig-placeholder')) {
        input.setAttribute('data-orig-placeholder', origPh);
      }
      if (dict[origPh.trim()]) {
        input.placeholder = dict[origPh.trim()];
      }
    });
  }

  // =========================================================================
  // 6. NAVBAR & UI SELECTOR CONTROLS
  // =========================================================================
  function updateNavbarSelectors() {
    const curr = CURRENCIES[currentCurrency] || CURRENCIES['INR'];
    const lang = LANGUAGES[currentLanguage] || LANGUAGES['en'];

    // Update Currency button labels
    document.querySelectorAll('.current-currency-display').forEach(el => {
      el.innerHTML = `${curr.flag} ${curr.code} (${curr.symbol.trim()})`;
    });

    // Update Language button labels
    document.querySelectorAll('.current-lang-display').forEach(el => {
      el.innerHTML = `${lang.flag} ${lang.native}`;
    });

    // Mark active in dropdowns
    document.querySelectorAll('[data-set-currency]').forEach(item => {
      if (item.getAttribute('data-set-currency') === currentCurrency) {
        item.classList.add('active-i18n');
      } else {
        item.classList.remove('active-i18n');
      }
    });

    document.querySelectorAll('[data-set-lang]').forEach(item => {
      if (item.getAttribute('data-set-lang') === currentLanguage) {
        item.classList.add('active-i18n');
      } else {
        item.classList.remove('active-i18n');
      }
    });
  }

  function refreshPageLocalization() {
    updateNavbarSelectors();
    applyCurrencyConversion();
    applyLanguageTranslation();
  }

  // =========================================================================
  // 7. INITIALIZATION ON DOM READY & OBSERVERS
  // =========================================================================
  document.addEventListener('DOMContentLoaded', function() {
    refreshPageLocalization();

    // Global Click Delegation for Dropdowns & Selectors
    document.addEventListener('click', function(e) {
      // 1. Currency item clicked
      const currItem = e.target.closest('[data-set-currency]');
      if (currItem) {
        e.preventDefault();
        const code = currItem.getAttribute('data-set-currency');
        setCurrency(code);
        closeAllI18nDropdowns();
        return;
      }

      // 2. Language item clicked
      const langItem = e.target.closest('[data-set-lang]');
      if (langItem) {
        e.preventDefault();
        const lang = langItem.getAttribute('data-set-lang');
        setLanguage(lang);
        closeAllI18nDropdowns();
        return;
      }

      // 3. Dropdown toggle clicked
      const toggleBtn = e.target.closest('.i18n-dropdown-toggle');
      if (toggleBtn) {
        e.preventDefault();
        e.stopPropagation();
        const menu = toggleBtn.nextElementSibling;
        const isOpen = menu.classList.contains('show');
        closeAllI18nDropdowns();
        if (!isOpen) {
          menu.classList.add('show');
        }
        return;
      }

      // 4. Click outside to close
      if (!e.target.closest('.i18n-dropdown-container')) {
        closeAllI18nDropdowns();
      }
    });

    // Observe dynamic changes (e.g. AJAX cart updates, seat selections, search filter changes)
    const observer = new MutationObserver(function(mutations) {
      let shouldReapply = false;
      mutations.forEach(m => {
        if (m.addedNodes.length > 0) {
          shouldReapply = true;
        }
      });
      if (shouldReapply) {
        applyCurrencyConversion();
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });
  });

  function closeAllI18nDropdowns() {
    document.querySelectorAll('.i18n-dropdown-menu.show').forEach(m => {
      m.classList.remove('show');
    });
  }

})();
