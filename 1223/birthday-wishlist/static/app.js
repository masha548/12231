(() => {
  "use strict";

  const menuButton = document.querySelector(".menu-toggle");
  const navigation = document.querySelector(".main-nav");

  if (menuButton && navigation) {
    menuButton.addEventListener("click", () => {
      const opened = navigation.classList.toggle("is-open");
      menuButton.setAttribute("aria-expanded", String(opened));
    });
  }

  const modal = document.querySelector("#reservation-modal");
  const form = document.querySelector("#reservation-form");
  const productName = document.querySelector("#modal-product");
  const wishId = document.querySelector("#wish-id");
  const formError = document.querySelector("#form-error");

  function closeReservationModal() {
    if (!modal) return;
    modal.close();
    form?.reset();
    if (formError) formError.textContent = "";
  }

  document.querySelectorAll("[data-reserve]").forEach((button) => {
    button.addEventListener("click", () => {
      if (!modal || !form || !wishId || !productName) return;
      wishId.value = button.dataset.id || "";
      productName.textContent = `${button.dataset.title || "Подарок"} · ${button.dataset.price || ""}`;
      form.reset();
      wishId.value = button.dataset.id || "";
      formError.textContent = "";
      modal.showModal();
      form.querySelector("input[name='name']")?.focus();
    });
  });

  document.querySelector("[data-modal-close]")?.addEventListener("click", closeReservationModal);

  modal?.addEventListener("click", (event) => {
    const bounds = modal.getBoundingClientRect();
    const outside = event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom;
    if (outside) closeReservationModal();
  });

  form?.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!wishId?.value) return;

    const submitButton = form.querySelector("button[type='submit']");
    const data = new FormData(form);
    const name = String(data.get("name") || "").trim();
    if (!name) {
      formError.textContent = "Напиши, пожалуйста, как тебя зовут.";
      form.querySelector("input[name='name']")?.focus();
      return;
    }

    formError.textContent = "";
    if (submitButton) {
      submitButton.disabled = true;
      submitButton.querySelector("span").textContent = "Бронирую…";
    }

    try {
      const response = await fetch(`/api/wishes/${encodeURIComponent(wishId.value)}/reserve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          contact: String(data.get("contact") || "").trim(),
          message: String(data.get("message") || "").trim(),
        }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Не получилось сохранить бронь. Попробуй ещё раз.");
      window.location.assign(result.redirect || "/thanks");
    } catch (error) {
      formError.textContent = error instanceof Error ? error.message : "Не получилось сохранить бронь. Попробуй ещё раз.";
      if (submitButton) {
        submitButton.disabled = false;
        submitButton.querySelector("span").textContent = "Забронировать";
      }
    }
  });

  const filters = document.querySelectorAll("[data-filter]");
  const search = document.querySelector("[data-wish-search]");
  const cards = [...document.querySelectorAll("[data-wish-grid] .wish-card")];
  const emptyState = document.querySelector("[data-empty-state]");
  const resultLabel = document.querySelector("[data-catalog-result]");
  let currentFilter = "all";

  function filterWishes() {
    const query = String(search?.value || "").trim().toLowerCase();
    let visible = 0;
    cards.forEach((card) => {
      const correctCategory = currentFilter === "all" || card.dataset.category === currentFilter;
      const correctSearch = !query || (card.dataset.title || "").includes(query);
      const show = correctCategory && correctSearch;
      card.hidden = !show;
      if (show) visible += 1;
    });
    if (emptyState) emptyState.hidden = visible !== 0;
    if (resultLabel) resultLabel.textContent = visible ? `Показываем: ${visible}` : "Ничего не нашлось";
  }

  filters.forEach((filter) => {
    filter.addEventListener("click", () => {
      currentFilter = filter.dataset.filter || "all";
      filters.forEach((item) => item.classList.toggle("is-active", item === filter));
      filterWishes();
    });
  });
  search?.addEventListener("input", filterWishes);

  const countdown = document.querySelector("[data-countdown]");
  if (countdown) {
    const days = countdown.querySelector("[data-days]");
    const hours = countdown.querySelector("[data-hours]");
    const minutes = countdown.querySelector("[data-minutes]");
    const plural = (number, forms) => {
      const remainder = number % 100;
      const last = number % 10;
      if (remainder > 10 && remainder < 20) return forms[2];
      if (last === 1) return forms[0];
      if (last > 1 && last < 5) return forms[1];
      return forms[2];
    };
    const updateCountdown = () => {
      const now = new Date();
      let birthday = new Date(now.getFullYear(), 8, 26, 0, 0, 0);
      if (birthday <= now) birthday = new Date(now.getFullYear() + 1, 8, 26, 0, 0, 0);
      const remaining = Math.max(0, birthday.getTime() - now.getTime());
      const daysNumber = Math.floor(remaining / 86400000);
      const hoursNumber = Math.floor((remaining % 86400000) / 3600000);
      const minutesNumber = Math.floor((remaining % 3600000) / 60000);
      if (days) days.textContent = String(daysNumber).padStart(2, "0");
      if (hours) hours.textContent = String(hoursNumber).padStart(2, "0");
      if (minutes) minutes.textContent = String(minutesNumber).padStart(2, "0");
      const labels = countdown.querySelectorAll("span");
      if (labels[0]) labels[0].textContent = plural(daysNumber, ["день", "дня", "дней"]);
      if (labels[1]) labels[1].textContent = plural(hoursNumber, ["час", "часа", "часов"]);
      if (labels[2]) labels[2].textContent = plural(minutesNumber, ["минута", "минуты", "минут"]);
    };
    updateCountdown();
    window.setInterval(updateCountdown, 30000);
  }
})();
