document.addEventListener("DOMContentLoaded", function () {

  /* HAMBURGER MENU */

  const hamburger = document.getElementById('hamburger');
  const navMenu = document.getElementById('navMenu');
  if (hamburger && navMenu) {
    hamburger.addEventListener('click', function () {
      hamburger.classList.toggle('active');
      navMenu.classList.toggle('active');
    });
    navMenu.querySelectorAll('a').forEach(link => {
      link.addEventListener('click', function () {
        hamburger.classList.remove('active');
        navMenu.classList.remove('active');
      });
    });
  }

  /* SMOOTH SCROLL*/
  
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        const navHeight = document.querySelector('.navbar').offsetHeight;
        const top = target.getBoundingClientRect().top + window.scrollY - navHeight - 10;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });

  /*CAROUSEL*/
  const track = document.getElementById('carouselTrack');
  const prevBtn = document.getElementById('carouselPrev');
  const nextBtn = document.getElementById('carouselNext');

  if (track && prevBtn && nextBtn) {
    const items = Array.from(track.children);
    const total = items.length;
    let current = 2;

    function getItemWidth() {
      return items[0].offsetWidth;
    }

    function updateCarousel(animate) {
      const itemW = getItemWidth();
      const viewportW = track.parentElement.offsetWidth;
    
      const offset = (viewportW / 2) - (current * itemW) - (itemW / 2);
      track.style.transition = animate ? 'transform 0.4s cubic-bezier(0.4,0,0.2,1)' : 'none';
      track.style.transform = `translateX(${offset}px)`;

      items.forEach((item, i) => {
        item.classList.remove('active', 'near');
        const dist = Math.abs(i - current);
        if (dist === 0) item.classList.add('active');
        else if (dist === 1) item.classList.add('near');
      });

      const underline = document.getElementById('brandUnderline');
      if (underline) {
        underline.style.width = itemW + 'px';
      }

      const activeBrand = items[current].getAttribute('data-brand');
      if (activeBrand && typeof filterByBrand === 'function') {
        filterByBrand(activeBrand);
      }
    }

    prevBtn.addEventListener('click', () => {
      current = (current - 1 + total) % total;
      updateCarousel(true);
    });

    nextBtn.addEventListener('click', () => {
      current = (current + 1) % total;
      updateCarousel(true);
    });

    items.forEach((item, i) => {
      item.addEventListener('click', () => {
        current = i;
        updateCarousel(true);
        const link = item.querySelector('a');
        if (link) {
          setTimeout(() => { window.location.href = link.href; }, 300);
        }
      });
    });

    // On catalog page: highlight the active brand from URL param
    const currentBrand = new URLSearchParams(window.location.search).get('brand');
    if (currentBrand) {
      const idx = items.findIndex(item => item.getAttribute('data-brand') === currentBrand);
      if (idx >= 0) { current = idx; updateCarousel(false); }
    }

    updateCarousel(false);
    window.addEventListener('resize', () => updateCarousel(false));


  }

});

/* CATALOG FILTER*/
function filterCars() {
  const category = document.getElementById('categoryFilter')?.value || 'all';
  const brand    = document.getElementById('brandFilter')?.value || 'all';
  const year     = document.getElementById('yearFilter')?.value || 'all';

  const cards = document.querySelectorAll('.car-card-catalog');
  let visible = 0;

  cards.forEach(card => {
    const matchCat   = category === 'all' || card.dataset.category === category;
    const matchBrand = brand === 'all' || card.dataset.brand === brand;
    const cardYear   = parseInt(card.dataset.year);
    let matchYear = true;
    if (year === '2023') matchYear = cardYear >= 2023;
    else if (year === '2022') matchYear = cardYear === 2022;
    else if (year === '2021') matchYear = cardYear === 2021;
    else if (year === '2020') matchYear = cardYear === 2020;
    else if (year === '2019') matchYear = cardYear === 2019;
    else if (year === '2018') matchYear = cardYear <= 2018;

    const show = matchCat && matchBrand && matchYear;
    card.style.display = show ? '' : 'none';
    if (show) visible++;
  });

  const results = document.getElementById('filterResults');
  if (results) {
    results.textContent = visible === 0
      ? 'No vehicles found'
      : `Showing ${visible} vehicle${visible !== 1 ? 's' : ''}`;
  }

  const noResults = document.getElementById('noResults');
  if (noResults) noResults.style.display = visible === 0 ? 'block' : 'none';
}

function filterByBrand(brand) {
  const brandSelect = document.getElementById('brandFilter');
  if (brandSelect) {
    brandSelect.value = brand;
    filterCars();
  }
}

/* DISCOUNT CAROUSEL */
document.addEventListener("DOMContentLoaded", function () {
  const dTrack = document.getElementById('discountTrack');
  const dPrev  = document.getElementById('discountPrev');
  const dNext  = document.getElementById('discountNext');

  if (!dTrack || !dPrev || !dNext) return;

  const dItems = Array.from(dTrack.children);
  if (dItems.length === 0) return;

  let dCurrent = 0;
  const CARD_W = 160 + 12; // card min-width + gap

  function updateDiscountCarousel(animate) {
    const viewW = dTrack.parentElement.offsetWidth;
    const offset = (viewW / 2) - (dCurrent * CARD_W) - (CARD_W / 2) + 10;
    dTrack.style.transition = animate ? 'transform 0.4s cubic-bezier(0.4,0,0.2,1)' : 'none';
    dTrack.style.transform = `translateX(${offset}px)`;
  }

  dPrev.addEventListener('click', () => {
    dCurrent = (dCurrent - 1 + dItems.length) % dItems.length;
    updateDiscountCarousel(true);
  });

  dNext.addEventListener('click', () => {
    dCurrent = (dCurrent + 1) % dItems.length;
    updateDiscountCarousel(true);
  });

  updateDiscountCarousel(false);
  window.addEventListener('resize', () => updateDiscountCarousel(false));

  // Auto-slide every 4 seconds
  setInterval(() => {
    dCurrent = (dCurrent + 1) % dItems.length;
    updateDiscountCarousel(true);
  }, 4000);
});

/* SCROLL REVEAL */
document.addEventListener("DOMContentLoaded", function () {
  const revealEls = document.querySelectorAll('.reveal');
  if (!revealEls.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  revealEls.forEach(el => observer.observe(el));
});

/* BACK TO TOP */
document.addEventListener("DOMContentLoaded", function () {
  const btn = document.getElementById('backToTop');
  if (!btn) return;
  btn.style.opacity = '0';
  btn.style.transition = 'opacity 0.3s, transform 0.3s';
  window.addEventListener('scroll', () => {
    if (window.scrollY > 400) {
      btn.style.opacity = '1';
      btn.style.pointerEvents = 'auto';
    } else {
      btn.style.opacity = '0';
      btn.style.pointerEvents = 'none';
    }
  }, { passive: true });
});
