document.addEventListener("DOMContentLoaded", () => {

  // Page title animation
  gsap.from(".page-title", {
    opacity: 0,
    y: -30,
    duration: 0.8,
    ease: "power3.out"
  });

  // Stat cards
  gsap.from(".stat-card", {
    opacity: 0,
    y: 40,
    duration: 0.8,
    stagger: 0.2,
    delay: 0.2,
    ease: "power3.out"
  });

  // Content cards
  gsap.from(".card", {
    opacity: 0,
    y: 50,
    duration: 0.9,
    stagger: 0.2,
    delay: 0.4,
    ease: "power3.out"
  });

  // Skill badges
  gsap.from(".skill-badge", {
    scale: 0.7,
    opacity: 0,
    duration: 0.4,
    stagger: 0.06,
    delay: 0.9,
    ease: "back.out(1.7)"
    });
  
  });
  
  // Toggle Job Description for Recruiter mode
    document.querySelectorAll('input[name="mode"]').forEach((radio) => {
    radio.addEventListener("change", () => {
    const jdGroup = document.getElementById("jd-group");
    if (radio.value === "recruiter" && radio.checked) {
      jdGroup.style.display = "block";
    } else if (radio.value === "jobseeker" && radio.checked) {
      jdGroup.style.display = "none";
    }

});

});
