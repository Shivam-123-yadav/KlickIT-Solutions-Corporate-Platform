// Wait until DOM is ready
document.addEventListener("DOMContentLoaded", () => {

  /* ========== Hide topbar on scroll down ========== */
  let lastScroll = 0;
  const topbar = document.getElementById("topbar");

  if (topbar) {
    window.addEventListener("scroll", function () {
      let currentScroll = window.pageYOffset;
      if (currentScroll > lastScroll) {
        topbar.classList.add("hide-topbar");
      } else {
        topbar.classList.remove("hide-topbar");
      }
      lastScroll = currentScroll;
    });
  }

  /* ========== Back To Top Button ========== */
  const backToTop = document.querySelector(".backToTop");

  if (backToTop) {
    window.addEventListener("scroll", () => {
      if (window.scrollY > 300) {
        backToTop.classList.add("show");
      } else {
        backToTop.classList.remove("show");
      }
    });

    backToTop.addEventListener("click", () => {
      window.scrollTo({
        top: 0,
        behavior: "smooth"
      });
    });
  }

  /* ========== Drawer Menu ========== */
  const contactBtn = document.getElementById("contactBtn");
  const drawer = document.getElementById("drawer");
  const closeDrawerBtn = document.getElementById("closeDrawer");
  let drawerOpen = false;

  if (contactBtn && drawer && closeDrawerBtn) {
    contactBtn.addEventListener("click", () => {
      drawer.style.right = drawerOpen ? "-300px" : "0";
      drawerOpen = !drawerOpen;
    });

    closeDrawerBtn.addEventListener("click", () => {
      drawer.style.right = "-300px";
      drawerOpen = false;
    });
  }

	/* ========== Play Sound on Hover (bannersoud sound) ========== */	
	document.querySelectorAll(".bannersoud").forEach(card => {
    card.addEventListener("mouseenter", () => {
      let sound = new Audio(card.getAttribute("data-sound"));
      sound.play();
    });
  });
	
	
	/* ========== Play Sound on Hover (what we do section) purple book now ========== */	
	document.querySelectorAll(".pulse").forEach(card => {
    card.addEventListener("mouseenter", () => {
      let sound = new Audio(card.getAttribute("data-sound"));
      sound.play();
    });
  });
	
	
/* ========== Play Sound on Hover (Service Card of logos) ========== */	
	document.querySelectorAll(".service-card").forEach(card => {
    card.addEventListener("mouseenter", () => {
      let sound = new Audio(card.getAttribute("data-sound"));
      sound.play();
    });
  });
	
	
	
	
	
  /* ========== Play Sound on Hover (Work Process Balloons) ========== */
  document.querySelectorAll(".balloon").forEach(balloon => {
    balloon.addEventListener("mouseenter", () => {
      let soundFile = balloon.getAttribute("data-sound");
      if (soundFile) {
        let audio = new Audio(soundFile);
        audio.play();
      }
    });
  });

	
	
	
  /* ========== Brands Logo Slider (requires jQuery + Slick) ========== */
  if (typeof $ !== "undefined" && $(".brands-slider").length) {
    $(".brands-slider").slick({
      slidesToShow: 5,
      slidesToScroll: 1,
      autoplay: false,
      autoplaySpeed: 2000,
      infinite: false,
      arrows: true,
      dots: true,
      responsive: [
        {
          breakpoint: 1024,
          settings: { slidesToShow: 3 }
        },
        {
          breakpoint: 768,
          settings: { slidesToShow: 2 }
        },
        {
          breakpoint: 480,
          settings: { slidesToShow: 2, arrows: false }
			
        }
      ]
    });
  }

  /* ========== Banner Slider (requires jQuery + Slick) ========== */
  if (typeof $ !== "undefined" && $(".banner-slider").length) {
    $(".banner-slider").slick({
      dots: true,
      arrows: false,
      autoplay: true,
      autoplaySpeed: 4000,
      fade: true,
      speed: 1000,
      cssEase: "ease-in-out"
    });
  }
	
	
	
	
	
  /* ========== Testimonials Slider (requires jQuery + Slick) ========== */
  if (typeof $ !== "undefined" && $(".testimonials-slider").length) {
    $(".testimonials-slider").slick({
//      dots: true,
        arrows: true,
        infinite: true,
        vertical: true,          // vertical mode enabled
        verticalSwiping: true,   // allow swipe up/down
        slidesToShow: 2,         // show 2 at once
        slidesToScroll: 1,
        autoplay: false,
        autoplaySpeed: 3800,
        speed: 600,
        centerMode: false,
        adaptiveHeight: false,
        pauseOnHover: true,
      responsive: [
          {
            breakpoint: 600,
            settings: {
              vertical: false,    // on small screens use horizontal for better UX
              slidesToShow: 1,
              verticalSwiping: false,
				 dots: true,
				  arrows: false,
            }
          }
        ]
    });
  }	
	
	
	
	
	
	
	
	
	
	

  /* ========== AOS (Animate On Scroll) ========== */
  if (typeof AOS !== "undefined") {
    AOS.init({ duration: 1000 });
  }

}); // DOMContentLoaded
